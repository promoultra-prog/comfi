"""
File    : zsampler_turbo_advanced.py
Purpose : Node for denoising latent images with Z-Image Turbo (ZIT).
          Smart mode uses a single adaptive Karras schedule; legacy staged
          modes remain for backward compatibility.
Author  : Martin Rizzo | <martinrizzo@gmail.com>
Date    : Feb 13, 2026
Repo    : https://github.com/martin-rizzo/ComfyUI-ZImagePowerNodes
License : MIT
"""

from __future__ import annotations

import math
import time
from collections import OrderedDict
from typing import Any

import torch
import comfy.utils
import comfy.sample
import comfy.samplers
import comfy.sampler_helpers
from comfy_api.latest import io

from .lib.system import logger
from .lib.progress_bar import ProgressPreview


# ── Empirical constants ───────────────────────────────────────────────────────
SIGMA_LIMIT_POWER = 0.074
NOISE_OVERDOSE_MAX = 3.0
KARRAS_RHO = 7.0
_BIAS_CLAMP_MAX = 4.0
_BIAS_NORMALIZER_MIN = 0.25
_BIAS_NORMALIZER_MAX = 16.0
_NOISE_CLAMP_MAX = 4.0  # hard clamp before bias


# ── Smart mode defaults ───────────────────────────────────────────────────────
SMART_DEFAULT_SAMPLER = "dpmpp_2m_sde"


# ── Sampler name mapping ──────────────────────────────────────────────────────
# Legacy staged pipeline: two samplers (S1+S2 / S3).
SAMPLER_MODES: dict[str, tuple[str, str]] = {
    "euler":               ("euler",           "euler"),
    "hybrid":              ("euler",           "euler_ancestral"),
    "euler_ancestral":     ("euler_ancestral", "euler_ancestral"),
    "dpmpp_2s_ancestral":   ("euler",          "dpmpp_2s_ancestral"),
    "dpm2m":               ("euler",           "dpmpp_2m"),
    "dpm2m_hybrid":        ("dpmpp_2m",        "euler_ancestral"),
    "dpmpp_sde":           ("euler",           "dpmpp_sde"),
    "dpmpp_sde_gpu":       ("euler",           "dpmpp_sde_gpu"),
    "dpmpp_2m_sde":        ("euler",           "dpmpp_2m_sde"),
    "dpmpp_3m_sde":        ("euler",           "dpmpp_3m_sde"),
    "deis":                ("euler",           "deis"),
    "uni_pc":              ("euler",           "uni_pc"),
    "uni_pc_bh2":          ("euler",           "uni_pc_bh2"),
    "lcm":                 ("lcm",             "lcm"),
}
DEFAULT_SAMPLER_MODE = "hybrid"

# Smart mode: single sampler across the full schedule.
SMART_SAMPLER_MODES: dict[str, str] = {
    "euler":               "euler",
    "hybrid":              "euler_ancestral",
    "euler_ancestral":     "euler_ancestral",
    "dpmpp_2s_ancestral":   "dpmpp_2s_ancestral",
    "dpm2m":                "dpmpp_2m",
    "dpmpp_2m":             "dpmpp_2m",
    "dpmpp_sde":            "dpmpp_sde",
    "dpmpp_sde_gpu":        "dpmpp_sde_gpu",
    "dpmpp_2m_sde":         "dpmpp_2m_sde",
    "dpmpp_3m_sde":         "dpmpp_3m_sde",
    "deis":                 "deis",
    "uni_pc":               "uni_pc",
    "uni_pc_bh2":           "uni_pc_bh2",
    "lcm":                  "lcm",
}


# ── Staged distribution ───────────────────────────────────────────────────────
STAGE1_FIXED_STEPS = 2
_DEFAULT_STAGE3_RATIOS: dict[int, float] = {
    6: 0.50, 7: 0.40, 8: 0.33, 9: 0.43,
    10: 0.38, 11: 0.44, 12: 0.40,
}
_DEFAULT_STAGE3_RATIO_FALLBACK = 0.38


# ── Staged sigma ranges ───────────────────────────────────────────────────────
_STAGE1_SIGMA_RANGE = (0.991, 0.920)
_STAGE2_SIGMA_RANGE = (0.942, 0.750)
_STAGE3_SIGMA_RANGE = (0.6582, 0.2000)


# ══════════════════════════════════════════════════════════════════════════════
#  Sigma helpers
# ══════════════════════════════════════════════════════════════════════════════

def _generate_sigmas(n_steps: int, sigma_max: float, sigma_min: float) -> list[float]:
    """Linear descending sigma schedule with terminal 0.0."""
    if n_steps <= 0:
        return [sigma_min, 0.0]
    if n_steps == 1:
        return [sigma_max, 0.0]
    step = (sigma_max - sigma_min) / (n_steps - 1)
    sigmas = [sigma_max - i * step for i in range(n_steps)]
    sigmas[-1] = sigma_min
    sigmas.append(0.0)
    return sigmas


def _generate_sigmas_karras(
    n_steps: int,
    sigma_max: float,
    sigma_min: float,
    rho: float = KARRAS_RHO,
) -> list[float]:
    """Karras et al. (2022) sigma schedule with terminal 0.0."""
    if n_steps <= 0:
        return [sigma_min, 0.0]
    if n_steps == 1:
        return [sigma_max, 0.0]

    rho = max(float(rho), 1e-3)
    inv_rho = 1.0 / rho
    ramp = [i / (n_steps - 1) for i in range(n_steps)]
    max_inv_rho = sigma_max ** inv_rho
    min_inv_rho = sigma_min ** inv_rho
    sigmas = [(max_inv_rho + t * (min_inv_rho - max_inv_rho)) ** rho for t in ramp]
    sigmas[-1] = sigma_min
    sigmas.append(0.0)
    return sigmas


def _blend_sigmas(a: list[float], b: list[float], blend: float) -> list[float]:
    """Kept for API compatibility. Not used internally — blending was removed.

    Linear interpolation between linear and Karras sigma scales is not
    physically meaningful (Karras is non-linear by design).  Call
    _generate_sigmas or _generate_sigmas_karras directly instead.
    """
    if len(a) != len(b):
        raise ValueError(
            f"Sigma lists must have the same length for blending, got {len(a)} and {len(b)}"
        )
    if blend <= 0.0:
        return list(a)
    if blend >= 1.0:
        return list(b)
    out = [float(x * (1.0 - blend) + y * blend) for x, y in zip(a, b)]
    out[-1] = 0.0
    return out


def _ensure_terminal_zero(sigmas: list[float]) -> list[float]:
    """Return a copy of sigmas guaranteed to end with 0.0."""
    if not sigmas:
        return [0.0]
    return list(sigmas) if sigmas[-1] == 0.0 else list(sigmas) + [0.0]


def _validate_sigmas_monotone(sigmas: list[float]) -> tuple[bool, str]:
    """Check that positive sigma values are strictly descending."""
    body = [v for v in sigmas if v > 0.0]
    if len(body) < 2:
        return True, ""
    if any(not math.isfinite(v) for v in body):
        return False, "contains non-finite values"
    for i in range(len(body) - 1):
        if body[i + 1] >= body[i]:
            return False, f"non-descending at index {i}: {body[i]:.6f} → {body[i + 1]:.6f}"
    return True, ""


def _generate_stage_sigmas(
    n_steps: int,
    sigma_max: float,
    sigma_min: float,
    *,
    schedule: str = "linear",
) -> list[float]:
    """Generate stage sigmas using pure linear or pure Karras schedule.

    Blending is intentionally removed: linear interpolation between linear
    and Karras scales is not physically meaningful and loses the step-density
    benefit that Karras provides.  Use one or the other cleanly.
    """
    if schedule == "karras":
        return _generate_sigmas_karras(n_steps, sigma_max, sigma_min)
    return _generate_sigmas(n_steps, sigma_max, sigma_min)


def _resolve_sigma_mode(sigma_mode: str | None) -> tuple[str, bool]:
    """Normalise legacy / unknown sigma_mode strings."""
    mode = (sigma_mode or "smart").strip().lower()
    legacy_alias_used = False
    if mode == "dynamic":
        mode = "dynamic_karras"
        legacy_alias_used = True
    if mode not in {"smart", "static", "dynamic_linear", "dynamic_karras"}:
        logger.warning(f"[ZTurbo] Unknown sigma_mode '{sigma_mode}', falling back to 'smart'")
        mode = "smart"
    return mode, legacy_alias_used


def _smart_sigma_floor(steps: int, denoise: float) -> float:
    """Adaptive sigma_min floor for smart mode.

    Design goals:
    - Low denoise (img2img) → higher floor (less detail destruction)
    - High step count → slightly lower floor (more room for refinement)
    - Denoise has strong, meaningful effect across the full [0, 1] range

    Range: [0.10, 0.20]
    """
    denoise_f = max(0.0, min(float(denoise), 1.0))

    # Base floor from steps — log-scaled, gentle degradation.
    # At 12 steps: 0.18.  At 30: ~0.16.  At 60: ~0.15.  At 100+: ~0.14 (clamped at 0.13).
    log_factor = max(math.log2(max(int(steps), 4)) - math.log2(12), 0.0)
    base_floor  = 0.18 - 0.015 * log_factor         # 0.015 instead of 0.03 → gentler

    # Denoise modulation: the primary driver for img2img consistency.
    # At denoise=1.0 (text2img): floor stays at base (full schedule).
    # At denoise=0.3 (light img2img): floor rises to ~0.20 (protect structure).
    # Mapping: linear from base at denoise=1 to 0.20 at denoise=0.
    denoise_floor = base_floor + (0.20 - base_floor) * (1.0 - denoise_f)

    return max(0.13, min(0.20, denoise_floor))


def _smart_sigma_rho(steps: int) -> float:
    """Adaptive Karras rho for smart mode.

    Higher rho → more steps concentrated near sigma_min (detail region).
    Uses a logarithmic curve so the effect is real at high step counts:
      12 steps → rho 7.0  (standard)
      30 steps → rho 8.0  (denser detail region)
      60 steps → rho 8.8  (near cap)
    """
    log_factor = max(math.log2(max(int(steps), 4)) - math.log2(12), 0.0)
    rho = 7.0 + 1.2 * log_factor              # meaningful increase via log
    return max(6.5, min(9.0, rho))


def _generate_smart_sigmas(steps: int, denoise: float) -> list[float]:
    """Single-pass adaptive Karras schedule used in smart mode."""
    return _generate_sigmas_karras(
        steps,
        0.991,
        _smart_sigma_floor(steps, max(float(denoise), 0.0)),
        _smart_sigma_rho(steps),
    )


# ── Staged sigma tables (original hardcoded values, steps 4-12) ──────────────
_STATIC_SIGMAS: dict[int, tuple[list, list, list]] = {
    4:  ([0.991, 0.980, 0.920], [0.942, 0.000],                           [0.790, 0.000]),
    5:  ([0.991, 0.980, 0.920], [0.942, 0.780, 0.000],                    [0.6200, 0.0000]),
    6:  ([0.991, 0.980, 0.920], [0.942, 0.780, 0.000],                    [0.6582, 0.3019, 0.0000]),
    7:  ([0.991, 0.980, 0.920], [0.9350, 0.8916, 0.7600, 0.0000],         [0.6582, 0.3019, 0.0000]),
    8:  ([0.991, 0.980, 0.920], [0.935, 0.90, 0.875, 0.750, 0.0000],      [0.6582, 0.3019, 0.0000]),
    9:  ([0.991, 0.980, 0.920], [0.935, 0.90, 0.875, 0.750, 0.0000],      [0.6582, 0.4556, 0.2000, 0.0000]),
    10: ([0.991, 0.980, 0.920], _generate_sigmas(5, *_STAGE2_SIGMA_RANGE), _generate_sigmas(3, *_STAGE3_SIGMA_RANGE)),
    11: ([0.991, 0.980, 0.920], _generate_sigmas(5, *_STAGE2_SIGMA_RANGE), _generate_sigmas(4, *_STAGE3_SIGMA_RANGE)),
    12: ([0.991, 0.980, 0.920], _generate_sigmas(6, *_STAGE2_SIGMA_RANGE), _generate_sigmas(4, *_STAGE3_SIGMA_RANGE)),
}


def _get_static_sigmas(steps: int) -> tuple[list, list, list]:
    """Return (sigmas1, sigmas2, sigmas3) for the given step count."""
    if steps in _STATIC_SIGMAS:
        return _STATIC_SIGMAS[steps]
    s1 = 2
    s3 = 3 if steps <= 10 else 4
    s2 = max(steps - s1 - s3, 1)
    return (
        [0.991, 0.980, 0.920],
        _generate_sigmas(s2, *_STAGE2_SIGMA_RANGE),
        _generate_sigmas(s3, *_STAGE3_SIGMA_RANGE),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Misc helpers
# ══════════════════════════════════════════════════════════════════════════════

def _make_sampler(name: str, fallback: str = "euler") -> comfy.samplers.KSAMPLER:
    """Create a ComfyUI sampler object by name, falling back gracefully."""
    try:
        return comfy.samplers.sampler_object(name)
    except KeyError:
        logger.warning(f"[ZTurbo] Sampler '{name}' not found, falling back to '{fallback}'")
        return comfy.samplers.sampler_object(fallback)
    except Exception as e:
        logger.error(f"[ZTurbo] Sampler '{name}' raised unexpected error: {e}")
        raise


def _resolve_smart_sampler(name: str | None) -> str:
    """Resolve a UI sampler label to its internal ComfyUI name."""
    raw = (name or SMART_DEFAULT_SAMPLER).strip().lower()
    if raw in SMART_SAMPLER_MODES:
        return SMART_SAMPLER_MODES[raw]
    if raw in set(SMART_SAMPLER_MODES.values()):
        return raw
    logger.warning(
        f"[ZTurbo] Unknown smart_sampler_mode '{name}', falling back to '{SMART_DEFAULT_SAMPLER}'"
    )
    return SMART_DEFAULT_SAMPLER


def _distribute_steps(total_steps: int, stage3_ratio: float) -> tuple[int, int, int]:
    """Distribute total steps across 3 stages, each guaranteed at least 1."""
    remaining = max(total_steps - STAGE1_FIXED_STEPS, 1)
    s3 = max(round(remaining * stage3_ratio), 1)
    s2 = max(remaining - s3, 1)
    while STAGE1_FIXED_STEPS + s2 + s3 > total_steps and s2 > 1:
        s2 -= 1
    while STAGE1_FIXED_STEPS + s2 + s3 > total_steps and s3 > 1:
        s3 -= 1
    return STAGE1_FIXED_STEPS, s2, s3


def _to_list(s: Any) -> list[float]:
    if s is None:
        return []
    return s if isinstance(s, list) else s.tolist()


def _fmt_sigmas_short(sig: list[float]) -> str:
    if not sig or len(sig) < 2:
        return "—"
    return f"{sig[0]:.4f} → {sig[-2]:.4f}  ({len(sig)-1} steps)"


def _fmt_sigmas_full(sig: list[float]) -> str:
    if not sig:
        return "—"
    return "[" + ", ".join(f"{v:.4f}" for v in sig) + "]"


def _analyze_sigmas(sigmas: list[float] | None) -> dict[str, Any]:
    """Return compact diagnostics for a sigma schedule."""
    if not sigmas or len(sigmas) < 2:
        return {}

    body = [float(v) for v in sigmas if float(v) > 0.0]
    if len(body) < 1:
        return {}

    diffs = [body[i] - body[i + 1] for i in range(len(body) - 1)]
    avg_drop = sum(diffs) / max(len(diffs), 1)
    sigma_max = body[0]
    sigma_min = body[-1]
    sigma_ratio = sigma_max / max(sigma_min, 1e-6)
    max_drop = max(diffs) if diffs else 0.0
    tail = "soft"
    if sigma_min <= 0.16:
        tail = "aggressive"
    elif sigma_min <= 0.20:
        tail = "balanced"

    return {
        "sigma_max": sigma_max,
        "sigma_min": sigma_min,
        "sigma_ratio": sigma_ratio,
        "avg_drop": avg_drop,
        "max_drop": max_drop,
        "tail_strength": tail,
        "step_count": len(body),
    }


def _coerce_to_list(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        try:
            return [float(v) for v in value]
        except Exception:
            return None
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().float().tolist()
    if hasattr(value, "cpu"):
        try:
            return value.cpu().float().tolist()
        except Exception:
            return None
    if hasattr(value, "__iter__"):
        try:
            return [float(v) for v in value]
        except Exception:
            return None
    return None


def _model_id(model: Any) -> str:
    return f"{id(model):x}"


# ══════════════════════════════════════════════════════════════════════════════
#  Bias cache
# ══════════════════════════════════════════════════════════════════════════════

_BIAS_CACHE: OrderedDict[tuple, tuple[torch.Tensor, float]] = OrderedDict()
_BIAS_CACHE_MAX = 16


def _bias_cache_key(
    model: Any,
    seed: int,
    steps: int,
    forced_size: int | None,
    method: str,
    sigma_mode: str,
    sampler_name: str,
    denoise_bucket: int,
    first_sigma_key: int,   # round(sigma[0] * 1000) — bias validity depends on entry sigma
) -> tuple:
    return (
        _model_id(model), seed, steps, forced_size,
        method, sigma_mode, sampler_name, denoise_bucket,
        first_sigma_key,
    )


def _bias_cache_get(key: tuple) -> tuple[torch.Tensor, float] | None:
    value = _BIAS_CACHE.get(key)
    if value is not None:
        _BIAS_CACHE.move_to_end(key)
    return value


def _bias_cache_put(key: tuple, bias: torch.Tensor, normalizer: float) -> None:
    if len(_BIAS_CACHE) >= _BIAS_CACHE_MAX and key not in _BIAS_CACHE:
        _BIAS_CACHE.popitem(last=False)
    _BIAS_CACHE[key] = (bias.detach().cpu(), float(normalizer))


# ══════════════════════════════════════════════════════════════════════════════
#  Main node class
# ══════════════════════════════════════════════════════════════════════════════

class ZSamplerTurboAdvanced(io.ComfyNode):
    xTITLE = "Z-Sampler Turbo (Advanced)"
    xCATEGORY = ""
    xCOMFY_NODE_ID = ""
    xDEPRECATED = False

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            display_name=cls.xTITLE,
            category=cls.xCATEGORY,
            node_id=cls.xCOMFY_NODE_ID,
            is_deprecated=cls.xDEPRECATED,
            description=(
                'Efficiently denoises latent images, specifically tuned for the '
                '"Z-Image Turbo" model. Smart mode uses a single adaptive pass; '
                'legacy staged modes remain for compatibility.'
            ),
            inputs=[
                io.Model.Input("model", tooltip="The model used for generating the latent images."),
                io.Conditioning.Input("positive", tooltip="Positive conditioning."),
                io.Conditioning.Input(
                    "negative",
                    tooltip="Negative conditioning (CFG=1.0 = no effect, included for experimentation).",
                ),
                io.Latent.Input(
                    "latent_input",
                    tooltip="Initial latent image: 'Empty Latent' for text2img or encoded image for img2img.",
                ),
                io.Int.Input("seed", default=1, min=1, max=0xFFFFFFFFFFFFFFFF, control_after_generate=True, tooltip="Random noise seed."),
                io.Int.Input("steps", default=12, min=4, max=256, step=1, tooltip="Number of sampling iterations. Smart mode supports arbitrary step counts."),
                io.Float.Input("denoise", default=1.0, min=0.0, max=1.0, step=0.01, tooltip="Denoising strength. Lower values preserve input structure (img2img)."),

                io.Custom("ZIPN_DIVIDER").Input("div_sampler"),
                io.Combo.Input(
                    "sigma_mode",
                    default="smart",
                    options=["smart", "static", "dynamic", "dynamic_linear", "dynamic_karras"],
                    tooltip=(
                        "smart: single-pass adaptive Karras — recommended, use this. "
                        "static/dynamic*: legacy staged modes (deprecated, kept for compatibility)."
                    ),
                ),
                io.Combo.Input(
                    "smart_sampler_mode",
                    default=SMART_DEFAULT_SAMPLER,
                    options=list(SMART_SAMPLER_MODES.keys()),
                    tooltip="Sampler used in smart mode across the full schedule.",
                ),
                io.Combo.Input(
                    "sampler_mode",
                    default="hybrid",
                    options=list(SAMPLER_MODES.keys()),
                    tooltip=(
                        "Legacy staged sampler strategy (S1+S2 / S3). "
                        "hybrid ★: Euler/Euler-A — recommended for the staged path."
                    ),
                ),

                io.Custom("ZIPN_DIVIDER").Input("div_noise"),
                io.Float.Input(
                    "initial_noise_calibration",
                    default=0.0, min=0.0, max=1.0, step=0.05,
                    tooltip="Master control for noise adjustments (0 = all noise tweaks disabled).",
                ),
                io.Float.Input(
                    "noise_overdose",
                    default=0.33, min=-1.0, max=1.0, step=0.01,
                    tooltip="Initial noise overamplitude. Negative = reduce amplitude.",
                ),
                io.Combo.Input(
                    "noise_bias_estimation",
                    default="experimental",
                    options=["none", "experimental", "accurate"],
                    tooltip=(
                        "Bias estimation method. none: disabled. "
                        "experimental: minimal-noise denoising (fast). "
                        "accurate: full-noise denoising (slower, more precise)."
                    ),
                ),
                io.Combo.Input(
                    "noise_bias_sample_size",
                    default="image_size",
                    options=["image_size", "1024px", "512px", "256px"],
                    tooltip="Latent size for bias calculation. Smaller = faster first step.",
                ),
                io.Float.Input(
                    "noise_bias_scale",
                    default=0.12, min=0.0, max=1.0, step=0.01,
                    tooltip="How much of the calculated bias to apply (0 = none, 1 = full).",
                ),

                io.Custom("ZIPN_DIVIDER").Input("div_advanced"),
                io.Float.Input(
                    "stage3_ratio",
                    default=0.38, min=0.0, max=1.0, step=0.05,
                    optional=True,
                    tooltip="Only in dynamic modes. Fraction of non-S1 steps for Stage3. Disconnected = auto ratio.",
                ),
                io.Boolean.Input(
                    "use_custom_sigmas3",
                    default=True,
                    tooltip="Only in dynamic modes. When disabled, custom_sigmas3 is ignored.",
                ),
                io.Sigmas.Input(
                    "custom_sigmas3",
                    optional=True,
                    tooltip="Only in dynamic modes. External sigmas for Stage3. Must be strictly descending.",
                ),
            ],
            outputs=[
                io.Latent.Output(display_name="latent_output", tooltip="Denoised latent image."),
                io.String.Output(display_name="status_text", tooltip="Detailed sampling report for ShowText node."),
            ],
        )

    @classmethod
    def execute(
        cls,
        model,
        positive: list,
        negative: list,
        latent_input: dict[str, Any],
        seed: int,
        steps: int,
        denoise: float,
        sigma_mode: str = "smart",
        smart_sampler_mode: str = SMART_DEFAULT_SAMPLER,
        sampler_mode: str = DEFAULT_SAMPLER_MODE,
        initial_noise_calibration: float = 0.0,
        noise_overdose: float = 0.33,
        noise_bias_estimation: str = "experimental",
        noise_bias_sample_size: str | int | None = "image_size",
        noise_bias_scale: float = 0.12,
        stage3_ratio: float | None = None,
        use_custom_sigmas3: bool = True,
        custom_sigmas3: Any = None,
        **kwargs,
    ) -> io.NodeOutput:
        t_total_start = time.perf_counter()

        performing_inpainting = denoise < 0.99
        sigma_limit = denoise ** SIGMA_LIMIT_POWER if performing_inpainting else None
        denoise_bucket = round(float(denoise) * 100)

        effective_noise_bias_scale = noise_bias_scale * initial_noise_calibration
        effective_noise_overdose = noise_overdose * initial_noise_calibration
        if noise_bias_estimation == "accurate":
            effective_noise_bias_scale /= 2.0

        if sampler_mode not in SAMPLER_MODES:
            logger.warning(
                f"[ZTurbo] Unknown sampler_mode '{sampler_mode}', falling back to '{DEFAULT_SAMPLER_MODE}'"
            )
            sampler_mode = DEFAULT_SAMPLER_MODE

        staged_name12, staged_name3 = SAMPLER_MODES[sampler_mode]
        sampler_stage12 = _make_sampler(staged_name12)
        sampler_stage3 = _make_sampler(staged_name3)
        sampler_euler = _make_sampler("euler")

        resolved_sigma_mode, legacy_dynamic_alias = _resolve_sigma_mode(sigma_mode)
        smart_sampler_name = _resolve_smart_sampler(smart_sampler_mode)

        logger.info(
            f"[ZTurbo] steps={steps}, denoise={denoise:.2f}, seed={seed}, sigma_mode={sigma_mode} → {resolved_sigma_mode}"
        )
        logger.info(
            f"[ZTurbo] staged sampler: S1-2={staged_name12} / S3={staged_name3} | smart sampler: {smart_sampler_name}"
        )

        progress = ProgressPreview.from_comfyui(model, 100)
        latent_device = latent_input["samples"].device
        latent_dtype = latent_input["samples"].dtype

        forced_size: int | None = None
        if isinstance(noise_bias_sample_size, str) and noise_bias_sample_size.endswith("px"):
            forced_size = int(noise_bias_sample_size[:-2])
        elif isinstance(noise_bias_sample_size, (int, float)):
            forced_size = int(noise_bias_sample_size)

        # ═══════════════════════════════════════════════════════════════
        #  SMART MODE — single-pass adaptive Karras
        # ═══════════════════════════════════════════════════════════════
        if resolved_sigma_mode == "smart":
            try:
                sampler_smart = _make_sampler(smart_sampler_name)
            except Exception:
                logger.warning(
                    f"[ZTurbo] Smart sampler '{smart_sampler_name}' unavailable, falling back to euler"
                )
                sampler_smart = _make_sampler("euler")
                smart_sampler_name = "euler"

            smart_sigmas = _generate_smart_sigmas(steps, denoise)
            smart_sigmas_for_status = list(smart_sigmas)
            smart_sigmas_truncated = len(smart_sigmas) - 1

            if performing_inpainting:
                smart_tensor = torch.tensor(smart_sigmas, dtype=torch.float32, device=latent_device)
                smart_tensor = cls.truncate_sigmas(smart_tensor, sigma_limit)
                if smart_tensor is None or smart_tensor.shape[-1] < 2:
                    # All sigmas exceed the denoise limit — zero work would be done.
                    # This is a configuration issue, not a silent no-op.
                    msg = (
                        f"Smart mode: sigma schedule fully truncated for "
                        f"denoise={denoise:.2f} (sigma_limit={sigma_limit:.4f}). "
                        "No denoising performed — returning input latent unchanged. "
                        "Increase denoise or use a higher value."
                    )
                    logger.error(f"[ZTurbo] {msg}")
                    return io.NodeOutput(latent_input.copy(), msg)
                smart_sigmas           = smart_tensor.tolist()
                smart_sigmas_truncated = len(smart_sigmas) - 1

            od = max(-NOISE_OVERDOSE_MAX, min(effective_noise_overdose, NOISE_OVERDOSE_MAX))
            # 2**od gives predictable linear feel to the user:
            #   od=-1 → 0.50x,  od=0 → 1.00x,  od=+1 → 2.00x
            # exp() was too sensitive in mid-range and hard to tune presets for.
            initial_noise_amplitude = 2.0 ** od
            initial_noise_bias = 0

            t_bias_start = time.perf_counter()
            bias_was_computed = False
            bias_from_cache = False
            bias_enabled = (
                abs(effective_noise_bias_scale) > 1e-9
                and noise_bias_estimation != "none"
                and sigma_limit is None
            )

            if bias_enabled and smart_sigmas:
                first_sigma_key = round(smart_sigmas[0] * 1000)   # 3 decimal places
                cache_key = _bias_cache_key(
                    model, seed, steps, forced_size,
                    noise_bias_estimation, resolved_sigma_mode,
                    smart_sampler_name, denoise_bucket,
                    first_sigma_key,
                )
                cached = _bias_cache_get(cache_key)
                if cached is not None:
                    raw_bias, auto_normalizer = cached
                    raw_bias = raw_bias.to(device=latent_device, dtype=latent_dtype)
                    bias_from_cache = True
                    logger.info("[ZTurbo] Bias loaded from cache")
                else:
                    try:
                        first_sigma = smart_sigmas[0]
                        raw_bias = cls.calculate_denoise_bias(
                            latent_input, model, seed, positive, negative,
                            sampler=sampler_euler,
                            sigmas=[1.000, first_sigma],
                            method=noise_bias_estimation,
                            forced_size=forced_size,
                            progress_preview=ProgressPreview(
                                100,
                                parent=(progress, 0, max(100 // steps, 1)),
                            ),
                        )
                        raw_bias = raw_bias.to(device=latent_device, dtype=latent_dtype)
                        # L1 normalizer: mean absolute value is the correct reference
                        # for a channel-shift bias — RMS over-weights outlier channels.
                        l1 = torch.mean(torch.abs(raw_bias.float())).clamp(min=1e-4)
                        auto_normalizer = float(
                            torch.clamp(1.0 / l1, _BIAS_NORMALIZER_MIN, _BIAS_NORMALIZER_MAX)
                        )
                        _bias_cache_put(cache_key, raw_bias, auto_normalizer)
                        bias_was_computed = True
                        logger.info(f"[ZTurbo] Bias computed, l1={l1:.5f}, auto_normalizer={auto_normalizer:.4f}")
                    except Exception as e:
                        logger.error(f"[ZTurbo] Bias calculation failed: {e} — continuing without bias correction")
                        raw_bias = None
                        auto_normalizer = 1.0

                if raw_bias is not None:
                    bias_tensor = raw_bias * auto_normalizer
                    bias_tensor = torch.clamp(bias_tensor, -_BIAS_CLAMP_MAX, _BIAS_CLAMP_MAX)
                    initial_noise_bias = bias_tensor * effective_noise_bias_scale

            t_bias_elapsed = time.perf_counter() - t_bias_start

            t_denoise_start = time.perf_counter()
            latent_output = cls.execute_sampler(
                latent_input, model, seed, 1.0, positive, negative,
                sampler=sampler_smart,
                sigmas=smart_sigmas,
                noise_bias=initial_noise_bias,
                noise_amplitude=initial_noise_amplitude,
                keep_masked_area=True,
                progress_preview=ProgressPreview(100, parent=(progress, max(100 // steps, 1), 100)),
            )
            t_denoise_elapsed = time.perf_counter() - t_denoise_start
            t_total_elapsed = time.perf_counter() - t_total_start

            status_text = cls._build_smart_status_text(
                seed=seed, steps=steps, denoise=denoise,
                smart_sampler_name=smart_sampler_name,
                performing_inpainting=performing_inpainting,
                smart_sigmas_truncated=smart_sigmas_truncated,
                initial_noise_calibration=initial_noise_calibration,
                noise_overdose=noise_overdose,
                initial_noise_amplitude=initial_noise_amplitude,
                effective_noise_bias_scale=effective_noise_bias_scale,
                noise_bias_estimation=noise_bias_estimation,
                noise_bias_sample_size=noise_bias_sample_size,
                bias_was_computed=bias_was_computed,
                bias_from_cache=bias_from_cache,
                smart_sigmas_for_status=smart_sigmas_for_status,
                t_bias_elapsed=t_bias_elapsed,
                t_denoise_elapsed=t_denoise_elapsed,
                t_total_elapsed=t_total_elapsed,
            )
            return io.NodeOutput(latent_output, status_text)

        # ═══════════════════════════════════════════════════════════════
        #  LEGACY STAGED MODES
        # ═══════════════════════════════════════════════════════════════
        effective_ratio = 0.0

        logger.warning(
            f"[ZTurbo] sigma_mode='{resolved_sigma_mode}' is a legacy staged pipeline. "
            "It is kept for compatibility but is not recommended. "
            "Switch to sigma_mode='smart' for better results and reproducibility."
        )

        if resolved_sigma_mode == "static":
            sigmas1, sigmas2, sigmas3 = _get_static_sigmas(steps)
            logger.info(
                f"[ZTurbo] sigma_mode=static → S1:{len(sigmas1)-1} S2:{len(sigmas2)-1} S3:{len(sigmas3)-1} steps"
            )
        else:
            if stage3_ratio is None:
                effective_ratio = _DEFAULT_STAGE3_RATIOS.get(steps, _DEFAULT_STAGE3_RATIO_FALLBACK)
            else:
                effective_ratio = max(0.0, min(float(stage3_ratio), 1.0))

            s1_steps, s2_steps, s3_steps = _distribute_steps(steps, effective_ratio)
            logger.info(
                f"[ZTurbo] sigma_mode={resolved_sigma_mode}, stage3_ratio={'auto' if stage3_ratio is None else f'{effective_ratio:.2f}'} → S1:{s1_steps} S2:{s2_steps} S3:{s3_steps}"
            )
            sigmas1 = _generate_stage_sigmas(s1_steps, *_STAGE1_SIGMA_RANGE, schedule="linear")
            if resolved_sigma_mode == "dynamic_linear":
                sigmas2 = _generate_stage_sigmas(s2_steps, *_STAGE2_SIGMA_RANGE, schedule="linear")
                sigmas3 = _generate_stage_sigmas(s3_steps, *_STAGE3_SIGMA_RANGE, schedule="linear")
            else:   # dynamic_karras — pure Karras, no blending
                sigmas2 = _generate_stage_sigmas(s2_steps, *_STAGE2_SIGMA_RANGE, schedule="karras")
                sigmas3 = _generate_stage_sigmas(s3_steps, *_STAGE3_SIGMA_RANGE, schedule="karras")

        custom_sigmas3_status = "OFF"
        is_dynamic = resolved_sigma_mode in ("dynamic_linear", "dynamic_karras")
        if is_dynamic and use_custom_sigmas3 and custom_sigmas3 is not None:
            ext = _coerce_to_list(custom_sigmas3)
            if ext is not None and len(ext) >= 2:
                ext = _ensure_terminal_zero(ext)
                ok, reason = _validate_sigmas_monotone(ext)
                if not ok:
                    custom_sigmas3_status = f"rejected (not monotone: {reason})"
                    logger.warning(
                        f"[ZTurbo] custom_sigmas3 rejected — {reason}. Falling back to generated sigmas."
                    )
                else:
                    stage3_max = float(sigmas3[0])
                    ext_clamped = torch.tensor(ext, dtype=torch.float32).clamp(max=stage3_max)
                    sigmas3 = ext_clamped.tolist()
                    custom_sigmas3_status = "ON (applied)"
                    logger.info(
                        f"[ZTurbo] custom_sigmas3 applied (clamped to max={stage3_max:.4f}, {len(sigmas3)-1} steps)"
                    )
            else:
                custom_sigmas3_status = "connected but invalid (ignored)"
                logger.warning("[ZTurbo] custom_sigmas3 could not be parsed or has < 2 values")
        elif is_dynamic and custom_sigmas3 is not None and not use_custom_sigmas3:
            custom_sigmas3_status = "connected but disabled"

        sigmas1_for_status = _to_list(sigmas1)
        sigmas2_for_status = _to_list(sigmas2)
        sigmas3_for_status = _to_list(sigmas3)

        if performing_inpainting:
            s1_body = sigmas1[:-1] if isinstance(sigmas1, list) else sigmas1[:-1].tolist()
            s2_full = _ensure_terminal_zero(sigmas2 if isinstance(sigmas2, list) else sigmas2.tolist())
            sigmas1 = s1_body + s2_full
            sigmas2 = None

        od = max(-NOISE_OVERDOSE_MAX, min(effective_noise_overdose, NOISE_OVERDOSE_MAX))
        initial_noise_amplitude = 2.0 ** od   # 2^od: predictable doubling/halving per unit
        initial_noise_bias = 0

        t_bias_start = time.perf_counter()
        bias_was_computed = False
        bias_from_cache = False
        bias_enabled = (
            abs(effective_noise_bias_scale) > 1e-9
            and noise_bias_estimation != "none"
            and sigma_limit is None
        )

        if bias_enabled:
            first_sigma_key = round(
                (sigmas1[0] if isinstance(sigmas1, list) else float(sigmas1[0])) * 1000
            )
            cache_key = _bias_cache_key(
                model, seed, steps, forced_size,
                noise_bias_estimation, resolved_sigma_mode,
                sampler_mode, denoise_bucket,
                first_sigma_key,
            )
            cached = _bias_cache_get(cache_key)
            if cached is not None:
                raw_bias, auto_normalizer = cached
                raw_bias = raw_bias.to(device=latent_device, dtype=latent_dtype)
                bias_from_cache = True
                logger.info("[ZTurbo] Bias loaded from cache")
            else:
                try:
                    first_sigma = sigmas1[0] if isinstance(sigmas1, list) else sigmas1[0].item()
                    raw_bias = cls.calculate_denoise_bias(
                        latent_input, model, seed, positive, negative,
                        sampler=sampler_euler,
                        sigmas=[1.000, first_sigma],
                        method=noise_bias_estimation,
                        forced_size=forced_size,
                        progress_preview=ProgressPreview(
                            100,
                            parent=(progress, 0, max(100 // steps, 1)),
                        ),
                    )
                    raw_bias = raw_bias.to(device=latent_device, dtype=latent_dtype)
                    l1 = torch.mean(torch.abs(raw_bias.float())).clamp(min=1e-4)
                    auto_normalizer = float(
                        torch.clamp(1.0 / l1, _BIAS_NORMALIZER_MIN, _BIAS_NORMALIZER_MAX)
                    )
                    _bias_cache_put(cache_key, raw_bias, auto_normalizer)
                    bias_was_computed = True
                    logger.info(f"[ZTurbo] Bias computed, l1={l1:.5f}, auto_normalizer={auto_normalizer:.4f}")
                except Exception as e:
                    logger.error(f"[ZTurbo] Bias calculation failed: {e} — continuing without bias correction")
                    raw_bias = None
                    auto_normalizer = 1.0

            if raw_bias is not None:
                bias_tensor = raw_bias * auto_normalizer
                bias_tensor = torch.clamp(bias_tensor, -_BIAS_CLAMP_MAX, _BIAS_CLAMP_MAX)
                initial_noise_bias = bias_tensor * effective_noise_bias_scale

        t_bias_elapsed = time.perf_counter() - t_bias_start

        t_denoise_start = time.perf_counter()
        latent_output, stage_times = cls.execute_3_stage_denoising(
            latent_input, model, seed, 1.0, positive, negative,
            sampler_stage12=sampler_stage12,
            sampler_stage3=sampler_stage3,
            sigmas1=sigmas1, sigmas2=sigmas2, sigmas3=sigmas3,
            sigma_limit=sigma_limit,
            initial_noise_bias=initial_noise_bias,
            initial_noise_amplitude=initial_noise_amplitude,
            progress_preview=ProgressPreview(
                100, parent=(progress, max(100 // steps, 1), 100)
            ),
        )
        t_denoise_elapsed = time.perf_counter() - t_denoise_start
        t_total_elapsed = time.perf_counter() - t_total_start

        status_text = cls._build_status_text(
            seed=seed, steps=steps, denoise=denoise,
            performing_inpainting=performing_inpainting,
            sigma_mode=resolved_sigma_mode,
            legacy_dynamic_alias=legacy_dynamic_alias,
            stage3_ratio=stage3_ratio,
            effective_ratio=effective_ratio,
            name12=staged_name12, name3=staged_name3,
            custom_sigmas3_status=custom_sigmas3_status,
            initial_noise_calibration=initial_noise_calibration,
            noise_overdose=noise_overdose,
            initial_noise_amplitude=initial_noise_amplitude,
            effective_noise_bias_scale=effective_noise_bias_scale,
            noise_bias_estimation=noise_bias_estimation,
            noise_bias_sample_size=noise_bias_sample_size,
            bias_was_computed=bias_was_computed,
            bias_from_cache=bias_from_cache,
            sigmas1_for_status=sigmas1_for_status,
            sigmas2_for_status=sigmas2_for_status,
            sigmas3_for_status=sigmas3_for_status,
            stage_times=stage_times,
            t_bias_elapsed=t_bias_elapsed,
            t_denoise_elapsed=t_denoise_elapsed,
            t_total_elapsed=t_total_elapsed,
        )
        return io.NodeOutput(latent_output, status_text)

    # ══════════════════════════════════════════════════════════════════════════
    #  Status text helpers
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _bias_status_strings(
        *,
        effective_noise_bias_scale: float,
        performing_inpainting: bool,
        initial_noise_calibration: float,
        noise_bias_estimation: str,
        noise_bias_sample_size: Any,
        bias_was_computed: bool,
        bias_from_cache: bool,
    ) -> tuple[str, str]:
        bias_active = (
            abs(effective_noise_bias_scale) > 1e-9
            and not performing_inpainting
            and initial_noise_calibration > 0.0
            and noise_bias_estimation != "none"
        )
        if bias_active:
            cache_tag = " [from cache]" if bias_from_cache else " [computed]"
            bias_str = (
                f"{effective_noise_bias_scale:.2f}  "
                f"({noise_bias_estimation}, {noise_bias_sample_size})"
                f"{cache_tag}"
            )
        else:
            bias_str = "OFF"

        if bias_was_computed:
            bias_calc_str = "yes (auto-normalized)"
        elif bias_from_cache:
            bias_calc_str = "yes (from cache)"
        else:
            bias_calc_str = "no (disabled or img2img)"

        return bias_str, bias_calc_str

    @staticmethod
    def _build_smart_status_text(
        *,
        seed, steps, denoise, smart_sampler_name,
        performing_inpainting, smart_sigmas_truncated,
        initial_noise_calibration, noise_overdose,
        initial_noise_amplitude, effective_noise_bias_scale,
        noise_bias_estimation, noise_bias_sample_size,
        bias_was_computed, bias_from_cache,
        smart_sigmas_for_status,
        t_bias_elapsed, t_denoise_elapsed, t_total_elapsed,
    ) -> str:
        div = "═" * 50
        div2 = "─" * 50
        img_mode = "img2img" if performing_inpainting else "text2img"

        bias_str, bias_calc_str = ZSamplerTurboAdvanced._bias_status_strings(
            effective_noise_bias_scale=effective_noise_bias_scale,
            performing_inpainting=performing_inpainting,
            initial_noise_calibration=initial_noise_calibration,
            noise_bias_estimation=noise_bias_estimation,
            noise_bias_sample_size=noise_bias_sample_size,
            bias_was_computed=bias_was_computed,
            bias_from_cache=bias_from_cache,
        )

        sigma_stats = _analyze_sigmas(smart_sigmas_for_status)
        sched_line = _fmt_sigmas_short(smart_sigmas_for_status)
        full_steps = len(smart_sigmas_for_status) - 1
        if performing_inpainting and smart_sigmas_truncated < full_steps:
            sched_line += f"  → {smart_sigmas_truncated} steps after truncation (inpainting)"

        lines = [
            div,
            "  Z-SAMPLER TURBO — SAMPLING REPORT",
            div, "",
            "  CORE", div2,
            f"  seed              : {seed}",
            f"  steps             : {steps}",
            f"  denoise           : {denoise:.2f}  ({img_mode})",
            "",
            "  SAMPLER", div2,
            "  sigma_mode        : smart (single-pass adaptive Karras)",
            f"  sampler           : {smart_sampler_name}",
            "  report           : extended diagnostics",
            "",
            "  NOISE", div2,
            f"  calibration       : {initial_noise_calibration:.2f}",
            f"  overdose          : {noise_overdose:.2f}  →  amplitude: {initial_noise_amplitude:.4f}  (2^od)",
            f"  bias_scale        : {bias_str}",
            f"  bias_calculated   : {bias_calc_str}",
            "",
            "  SIGMA SCHEDULE", div2,
            f"  schedule          : {sched_line}",
            f"                    : {_fmt_sigmas_full(smart_sigmas_for_status)}",
            "",
            "  SIGMA ANALYSIS", div2,
            f"  sigma_max         : {sigma_stats.get('sigma_max', 0.0):.4f}" if sigma_stats else "  sigma_max         : —",
            f"  sigma_min         : {sigma_stats.get('sigma_min', 0.0):.4f}" if sigma_stats else "  sigma_min         : —",
            f"  sigma_ratio       : {sigma_stats.get('sigma_ratio', 0.0):.2f}x" if sigma_stats else "  sigma_ratio       : —",
            f"  avg_step_drop     : {sigma_stats.get('avg_drop', 0.0):.4f}" if sigma_stats else "  avg_step_drop     : —",
            f"  tail_strength     : {sigma_stats.get('tail_strength', '—')}" if sigma_stats else "  tail_strength     : —",
            "",
            "  NOISE PROFILE", div2,
            f"  amplitude         : {initial_noise_amplitude:.4f}",
            f"  bias_norm         : {'computed' if (bias_was_computed or bias_from_cache) else 'off'}",
            f"  bias_source       : {'cache' if bias_from_cache else ('fresh' if bias_was_computed else 'disabled')}",
            f"  bias_scale_eff    : {effective_noise_bias_scale:.4f}",
            f"  calibration_eff   : {initial_noise_calibration:.2f}",
            "",
            "  STABILITY", div2,
            f"  sigma_tail_risk   : {'high' if (sigma_stats and sigma_stats.get('sigma_min', 1.0) < 0.16) else ('medium' if (sigma_stats and sigma_stats.get('sigma_min', 1.0) < 0.20) else 'low')}",
            f"  bias_risk         : {'low' if abs(effective_noise_bias_scale) < 0.05 else ('medium' if abs(effective_noise_bias_scale) < 0.15 else 'high')}",
            f"  sampler_risk      : {'low' if smart_sampler_name in ('dpmpp_2m_sde', 'dpmpp_3m_sde', 'dpmpp_2m') else 'medium'}",
            "",
            "  TIMING", div2,
            f"  Bias estimation   : {t_bias_elapsed:.3f}s" + ("" if (bias_was_computed or bias_from_cache) else "  (skipped)"),
            f"  Denoise total     : {t_denoise_elapsed:.3f}s",
            f"  Pipeline total    : {t_total_elapsed:.3f}s",
            div,
        ]
        return "\n".join(lines)

    @staticmethod
    def _build_status_text(
        *,
        seed, steps, denoise, performing_inpainting,
        sigma_mode, legacy_dynamic_alias,
        stage3_ratio, effective_ratio,
        name12, name3, custom_sigmas3_status,
        initial_noise_calibration, noise_overdose,
        initial_noise_amplitude, effective_noise_bias_scale,
        noise_bias_estimation, noise_bias_sample_size,
        bias_was_computed, bias_from_cache,
        sigmas1_for_status, sigmas2_for_status, sigmas3_for_status,
        stage_times, t_bias_elapsed, t_denoise_elapsed, t_total_elapsed,
    ) -> str:
        div = "═" * 50
        div2 = "─" * 50
        img_mode = "img2img" if performing_inpainting else "text2img"

        if sigma_mode == "static":
            mode_str = "static (hardcoded tables) [LEGACY]"
        else:
            sched = "Karras" if sigma_mode == "dynamic_karras" else "linear"
            ratio_src = "auto" if stage3_ratio is None else f"{effective_ratio:.2f}"
            mode_str = sigma_mode + " [LEGACY]"
            if legacy_dynamic_alias:
                mode_str += " (alias: dynamic)"
            mode_str += f"  |  schedule: {sched}  |  ratio: {ratio_src}"

        bias_str, bias_calc_str = ZSamplerTurboAdvanced._bias_status_strings(
            effective_noise_bias_scale=effective_noise_bias_scale,
            performing_inpainting=performing_inpainting,
            initial_noise_calibration=initial_noise_calibration,
            noise_bias_estimation=noise_bias_estimation,
            noise_bias_sample_size=noise_bias_sample_size,
            bias_was_computed=bias_was_computed,
            bias_from_cache=bias_from_cache,
        )

        t_s1 = stage_times.get("s1", 0.0)
        t_s2 = stage_times.get("s2", 0.0)
        t_s3 = stage_times.get("s3", 0.0)

        sigma_all = [v for v in (sigmas1_for_status + sigmas2_for_status + sigmas3_for_status) if v > 0.0]
        sigma_stats = _analyze_sigmas(sigma_all)
        s1_stats = _analyze_sigmas(sigmas1_for_status)
        s2_stats = _analyze_sigmas(sigmas2_for_status)
        s3_stats = _analyze_sigmas(sigmas3_for_status)

        lines = [
            div,
            "  Z-SAMPLER TURBO — SAMPLING REPORT",
            div, "",
            "  CORE", div2,
            f"  seed              : {seed}",
            f"  steps             : {steps}",
            f"  denoise           : {denoise:.2f}  ({img_mode})",
            "",
            "  SAMPLER", div2,
            f"  sigma_mode        : {mode_str}",
            f"  sampler  S1+S2    : {name12}",
            f"  report            : extended diagnostics",
            f"  sampler  S3       : {name3}",
            f"  custom_sigmas3    : {custom_sigmas3_status}",
            "",
            "  NOISE", div2,
            f"  calibration       : {initial_noise_calibration:.2f}",
            f"  overdose          : {noise_overdose:.2f}  →  amplitude: {initial_noise_amplitude:.4f}",
            f"  bias_scale        : {bias_str}",
            f"  bias_calculated   : {bias_calc_str}",
            "",
            "  SIGMA SCHEDULE", div2,
            f"  S1 ({len(sigmas1_for_status)-1} steps)     : {_fmt_sigmas_short(sigmas1_for_status)}",
            f"                    : {_fmt_sigmas_full(sigmas1_for_status)}",
        ]

        if performing_inpainting:
            lines.append("  S2                : — (merged into S1 for inpainting)")
        else:
            lines.append(f"  S2 ({len(sigmas2_for_status)-1} steps)     : {_fmt_sigmas_short(sigmas2_for_status)}")
            lines.append(f"                    : {_fmt_sigmas_full(sigmas2_for_status)}")

        lines += [
            f"  S3 ({len(sigmas3_for_status)-1} steps)     : {_fmt_sigmas_short(sigmas3_for_status)}",
            f"                    : {_fmt_sigmas_full(sigmas3_for_status)}",
            "",
            "  SIGMA ANALYSIS", div2,
            f"  sigma_max         : {sigma_stats.get('sigma_max', 0.0):.4f}" if sigma_stats else "  sigma_max         : —",
            f"  sigma_min         : {sigma_stats.get('sigma_min', 0.0):.4f}" if sigma_stats else "  sigma_min         : —",
            f"  sigma_ratio       : {sigma_stats.get('sigma_ratio', 0.0):.2f}x" if sigma_stats else "  sigma_ratio       : —",
            f"  S1_tail           : {s1_stats.get('tail_strength', '—')}" if s1_stats else "  S1_tail           : —",
            f"  S2_tail           : {s2_stats.get('tail_strength', '—')}" if s2_stats else "  S2_tail           : —",
            f"  S3_tail           : {s3_stats.get('tail_strength', '—')}" if s3_stats else "  S3_tail           : —",
            "",
            "  NOISE PROFILE", div2,
            f"  amplitude         : {initial_noise_amplitude:.4f}",
            f"  bias_norm         : {'computed' if (bias_was_computed or bias_from_cache) else 'off'}",
            f"  bias_source       : {'cache' if bias_from_cache else ('fresh' if bias_was_computed else 'disabled')}",
            f"  bias_scale_eff    : {effective_noise_bias_scale:.4f}",
            f"  calibration_eff   : {initial_noise_calibration:.2f}",
            "",
            "  STABILITY", div2,
            f"  sigma_tail_risk   : {'high' if (sigma_stats and sigma_stats.get('sigma_min', 1.0) < 0.16) else ('medium' if (sigma_stats and sigma_stats.get('sigma_min', 1.0) < 0.20) else 'low')}",
            f"  bias_risk         : {'low' if abs(effective_noise_bias_scale) < 0.05 else ('medium' if abs(effective_noise_bias_scale) < 0.15 else 'high')}",
            f"  sampler_risk      : {'low' if name12 in ('euler', 'dpmpp_2m', 'dpmpp_2m_sde') and name3 in ('euler', 'dpmpp_2m', 'dpmpp_2m_sde') else 'medium'}",
            "",
            "  TIMING", div2,
            f"  Bias estimation   : {t_bias_elapsed:.3f}s" + ("" if (bias_was_computed or bias_from_cache) else "  (skipped)"),
            f"  Stage 1 (form)    : {t_s1:.3f}s",
            f"  Stage 2 (content) : {t_s2:.3f}s" + ("  (merged into S1)" if performing_inpainting else ""),
            f"  Stage 3 (detail)  : {t_s3:.3f}s",
            f"  Denoise total     : {t_denoise_elapsed:.3f}s",
            f"  Pipeline total    : {t_total_elapsed:.3f}s",
            div,
        ]
        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════════════════════
    #  3-stage denoising pipeline
    # ══════════════════════════════════════════════════════════════════════════

    @classmethod
    def execute_3_stage_denoising(
        cls,
        latent_image,
        model: Any,
        seed: int,
        cfg: float,
        positive: list,
        negative: list,
        *,
        sampler_stage12: comfy.samplers.KSAMPLER,
        sampler_stage3: comfy.samplers.KSAMPLER,
        sigmas1,
        sigmas2,
        sigmas3,
        sigma_limit: float | None = None,
        initial_noise_bias=None,
        initial_noise_amplitude: float = 1.0,
        progress_preview: ProgressPreview,
    ) -> tuple[dict, dict]:
        stage_times: dict[str, float] = {"s1": 0.0, "s2": 0.0, "s3": 0.0}
        device = latent_image["samples"].device

        def _to_tensor(s) -> torch.Tensor | None:
            if s is None:
                return None
            t = torch.tensor(s, dtype=torch.float32) if isinstance(s, list) else s.float()
            return t.to(device)

        sigmas1 = _to_tensor(sigmas1)
        sigmas2 = _to_tensor(sigmas2)
        sigmas3 = _to_tensor(sigmas3)

        if sigma_limit is not None:
            sigmas1 = cls.truncate_sigmas(sigmas1, sigma_limit)
            sigmas2 = cls.truncate_sigmas(sigmas2, sigma_limit)
            sigmas3 = cls.truncate_sigmas(sigmas3, sigma_limit)

        n1 = (sigmas1.shape[-1] - 1) if sigmas1 is not None else 0
        n2 = (sigmas2.shape[-1] - 1) if sigmas2 is not None else 0
        n3 = (sigmas3.shape[-1] - 1) if sigmas3 is not None else 0
        total = max(n1 + n2 + n3, 1)

        logger.info(f"[ZTurbo] sigma_limit={sigma_limit}, stages=[S1:{n1}, S2:{n2}, S3:{n3}]")

        def _pct(steps_done: int) -> int:
            return 100 * steps_done // total

        if sigmas1 is not None and n1 > 0:
            t0 = time.perf_counter()
            latent_image = cls.execute_sampler(
                latent_image, model, seed, cfg, positive, negative,
                sampler=sampler_stage12, sigmas=sigmas1,
                noise_bias=initial_noise_bias,
                noise_amplitude=initial_noise_amplitude,
                keep_masked_area=True,
                progress_preview=ProgressPreview(n1, parent=(progress_preview, _pct(0), _pct(n1))),
            )
            stage_times["s1"] = time.perf_counter() - t0

        if sigmas2 is not None and n2 > 0:
            t0 = time.perf_counter()
            add_noise = sigmas1 is None
            latent_image = cls.execute_sampler(
                latent_image, model, seed, cfg, positive, negative,
                sampler=sampler_stage12, sigmas=sigmas2,
                noise_bias=0,
                noise_amplitude=1.0 if add_noise else 0.0,
                keep_masked_area=True,
                progress_preview=ProgressPreview(n2, parent=(progress_preview, _pct(n1), _pct(n1 + n2))),
            )
            stage_times["s2"] = time.perf_counter() - t0

        if sigmas3 is not None and n3 > 0:
            t0 = time.perf_counter()
            latent_image = cls.execute_sampler(
                latent_image, model, seed + 2, cfg, positive, negative,
                sampler=sampler_stage3, sigmas=sigmas3,
                noise_bias=0,
                noise_amplitude=1.0,
                keep_masked_area=True,
                progress_preview=ProgressPreview(n3, parent=(progress_preview, _pct(n1 + n2), 100)),
            )
            stage_times["s3"] = time.perf_counter() - t0

        return latent_image, stage_times

    # ══════════════════════════════════════════════════════════════════════════
    #  Single sampler execution
    # ══════════════════════════════════════════════════════════════════════════

    @classmethod
    def execute_sampler(
        cls,
        latent_image: dict[str, Any],
        model: Any,
        noise_seed: int,
        cfg: float,
        positive: list,
        negative: list,
        *,
        sampler: comfy.samplers.KSAMPLER,
        sigmas,
        noise_bias,
        noise_amplitude,
        keep_masked_area: bool = False,
        fix_empty_latent: bool = True,
        progress_preview: ProgressPreview | None = None,
    ) -> dict[str, Any]:
        """Emulates ComfyUI SamplerCustom with extra noise controls."""

        if sigmas is None:
            return latent_image.copy()
        if isinstance(sigmas, list):
            sigmas = torch.tensor(sigmas, dtype=torch.float32)
        if int(sigmas.shape[-1]) < 2:
            return latent_image.copy()

        for name, val in (("noise_bias", noise_bias), ("noise_amplitude", noise_amplitude)):
            if isinstance(val, torch.Tensor) and (val.ndim != 4 or val.shape[2:] != (1, 1)):
                raise ValueError(
                    f"Invalid `{name}` shape: expected [B, C, 1, 1], got {list(val.shape)}"
                )

        if isinstance(noise_bias, (float, int)) and abs(noise_bias) < 1e-9:
            noise_bias = None
        if isinstance(noise_amplitude, (float, int)) and abs(noise_amplitude) < 1e-9:
            noise_amplitude = None

        latent = latent_image.copy()
        samples = (
            comfy.sample.fix_empty_latent_channels(model, latent["samples"])
            if fix_empty_latent
            else latent["samples"]
        )
        noise_mask = latent.get("noise_mask")
        batch_index = latent.get("batch_index")
        n_steps = max(int(sigmas.shape[-1]) - 1, 0)
        device = samples.device
        original_samples = samples
        original_mask = noise_mask

        sigmas = sigmas.to(device=device)

        if noise_amplitude is None:
            noise = torch.zeros(samples.shape, dtype=samples.dtype, device=device)
        else:
            noise = comfy.sample.prepare_noise(samples, noise_seed, batch_index).to(
                device=device, dtype=samples.dtype
            )
            amp = noise_amplitude if isinstance(noise_amplitude, torch.Tensor) else float(noise_amplitude)
            noise = noise * amp

        noise = torch.clamp(noise, -_NOISE_CLAMP_MAX, _NOISE_CLAMP_MAX)

        if noise_bias is not None:
            if isinstance(noise_bias, torch.Tensor):
                noise_bias = noise_bias.to(device=device, dtype=samples.dtype)
            noise = noise + noise_bias

        progress_wrapper = ProgressPreview(n_steps, parent=(progress_preview, 1, n_steps + 1))

        with torch.inference_mode():
            samples = comfy.sample.sample_custom(
                model, noise, cfg, sampler, sigmas, positive, negative,
                samples,
                noise_mask=noise_mask,
                callback=progress_wrapper,
                disable_pbar=not comfy.utils.PROGRESS_BAR_ENABLED,
                seed=noise_seed,
            )

        if not torch.isfinite(samples).all():
            logger.warning("[ZTurbo] NaN/Inf detected in samples, clamping to safe values")
            samples = torch.nan_to_num(samples, nan=0.0, posinf=10.0, neginf=-10.0)

        if keep_masked_area and original_mask is not None:
            mask = comfy.sampler_helpers.prepare_mask(
                original_mask, original_samples.shape, original_samples.device
            )
            if mask is not None:
                samples = samples * mask + (1.0 - mask) * original_samples

        out = latent_image.copy()
        out["samples"] = samples
        return out

    # ══════════════════════════════════════════════════════════════════════════
    #  Bias calculation
    # ══════════════════════════════════════════════════════════════════════════

    @classmethod
    def calculate_denoise_bias(
        cls,
        latent_image,
        model: Any,
        seed: int,
        positive: list,
        negative: list,
        *,
        sampler: comfy.samplers.KSAMPLER,
        sigmas,
        method: str = "accurate",
        forced_size: int | None = None,
        progress_preview: ProgressPreview,
    ) -> torch.Tensor:
        """Calculate per-channel noise bias [B, C, 1, 1] via one denoising step."""
        if method not in ("accurate", "experimental"):
            raise ValueError(f"[ZTurbo] Invalid bias method: '{method}'")

        if isinstance(sigmas, list):
            sigmas = torch.tensor(sigmas, dtype=torch.float32)
        n_steps = int(sigmas.shape[-1]) - 1

        probe_latent = latent_image.copy()
        if isinstance(forced_size, (int, float)) and forced_size >= 8:
            samples = latent_image["samples"]
            lh = int(forced_size // 8)
            lw = int(forced_size // 8)
            probe_latent["samples"] = torch.zeros(
                samples.shape[:-2] + (lh, lw),
                dtype=samples.dtype,
                layout=samples.layout,
                device=samples.device,
            )

        result = cls.execute_sampler(
            probe_latent, model, seed, 1.0, positive, negative,
            sampler=sampler,
            sigmas=sigmas,
            noise_bias=0,
            noise_amplitude=1.0 if method == "accurate" else 0.1,
            progress_preview=ProgressPreview(n_steps, parent=(progress_preview, 0, 100)),
        )

        return torch.mean(result["samples"], dim=[2, 3], keepdim=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  Sigma truncation (for img2img / inpainting)
    # ══════════════════════════════════════════════════════════════════════════

    @classmethod
    def truncate_sigmas(
        cls,
        sigmas: torch.Tensor | None,
        limit: float,
    ) -> torch.Tensor | None:
        """Truncate a descending sigma schedule at `limit` without duplication.

        Returns None when all sigmas are above `limit` (nothing to denoise at
        this strength).  Callers must check for None and handle explicitly —
        returning the input latent silently would hide the fact that zero work
        was done.
        """
        if sigmas is None:
            return None

        le_mask = sigmas <= limit
        if not le_mask.any():
            # Every sigma exceeds the limit → this stage has no work to do.
            # Callers must handle None explicitly and log/warn as appropriate.
            logger.warning(
                f"[ZTurbo] truncate_sigmas: no sigma ≤ {limit:.4f} found — "
                "this stage will be skipped entirely"
            )
            return None
        if le_mask.all():
            return sigmas

        first_idx = torch.nonzero(le_mask, as_tuple=False)[0].item()
        truncated = sigmas[first_idx:]

        if abs(truncated[0].item() - limit) < 1e-6:
            return truncated

        limit_sigma = torch.tensor([limit], dtype=sigmas.dtype, device=sigmas.device)
        return torch.cat((limit_sigma, truncated))
