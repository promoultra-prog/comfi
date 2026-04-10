"""
File    : style_prompt_encoder_2.py
Purpose : Node to get conditioning embeddings from a given style + prompt (version 2)
Author  : Martin Rizzo | <martinrizzo@gmail.com>
Date    : Jan 16, 2026
Repo    : https://github.com/martin-rizzo/ComfyUI-ZImagePowerNodes
License : MIT
Fixes   : - FIX#1: get_predefined_style_template strips quotes before lookup
          - FIX#2: validate_inputs no longer blocks on None clip
          - FIX#3: removed self-alias "zeiss_100mm_macro": "zeiss_100mm_macro"
          - FIX#4: tech_preset_options() shows only canonical keys, not aliases
          - FIX#5: xCOMFY_NODE_ID kept as "" to match saved workflow node IDs
Changes : - Removed gallery and spacer inputs
          - Camera angles, tech presets, prompt assembly moved to prompt_components.py
          - Removed conditioning encode cache (direct encode execution)
"""
from functools import cache
from comfy_api.latest import io
from .lib.system import logger
from .lib.style_group import StyleGroup
from ..styles.predefined_styles import PREDEFINED_STYLE_GROUPS
from .prompt_components import (
    camera_angle_options,
    tech_preset_options,
    build_prompt,
)

__all__ = [
    "StylePromptEncoder2",
    "_resolve_template",
]


# ───────────────────────── TEMPLATE RESOLUTION ───────────────────────────────

def _resolve_template(style: str, customization: str) -> str | None:
    if not isinstance(style, str) or style == "none":
        return None
    custom_styles = StyleGroup.from_string(customization)
    return (
        custom_styles.get_style_template(style)
        or StylePromptEncoder2.get_predefined_style_template(style)
    )


# ──────────────── Legacy compatibility shim ───────────────────────────────────

def _resolve_inputs(args, kwargs, style_candidates, default_style):
    """
    Backward-compatible resolver for style_prompt_encoder_3stage.py.
    Returns: (customization, style, text, camera_angle, tech_preset)
    """
    customization = kwargs.get("customization", "") or ""
    style         = kwargs.get("style", default_style) or default_style
    text          = kwargs.get("text", "") or ""
    camera_angle  = kwargs.get("camera_angle", "none") or "none"
    tech_preset   = kwargs.get("tech_preset", "none") or "none"

    pos = list(args)
    if len(pos) >= 1:
        first = pos[0]
        if isinstance(first, str) and first.strip() in style_candidates:
            style = first.strip()
            if len(pos) > 1 and isinstance(pos[1], str): text          = pos[1]
            if len(pos) > 2 and isinstance(pos[2], str): customization = pos[2]
            if len(pos) > 3 and isinstance(pos[3], str): camera_angle  = pos[3]
            if len(pos) > 4 and isinstance(pos[4], str): tech_preset   = pos[4]
        else:
            if len(pos) > 0 and isinstance(pos[0], str): customization = pos[0]
            if len(pos) > 1 and isinstance(pos[1], str): style         = pos[1]
            if len(pos) > 2 and isinstance(pos[2], str): text          = pos[2]
            if len(pos) > 3 and isinstance(pos[3], str): camera_angle  = pos[3]
            if len(pos) > 4 and isinstance(pos[4], str): tech_preset   = pos[4]

    return (customization, style, text, camera_angle, tech_preset)


# ───────────────────────── NODE DEFINITION ───────────────────────────────────

class StylePromptEncoder2(io.ComfyNode):
    xTITLE         = "Style & Prompt Encoder"
    xCATEGORY      = ""
    xCOMFY_NODE_ID = ""
    xDEPRECATED    = False

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            display_name  = cls.xTITLE,
            category      = cls.xCATEGORY,
            node_id       = cls.xCOMFY_NODE_ID,
            is_deprecated = cls.xDEPRECATED,
            description   = "Transforms a text prompt into embeddings, adapting style and camera angle.",
            inputs=[
                io.Clip.Input("clip",
                    tooltip="CLIP model for encoding."),
                io.String.Input("customization", optional=True, multiline=True,
                    force_input=True,
                    tooltip='Optional custom style definitions (>>>name lines).'),
                io.Combo.Input("style",
                    options=cls.style_names(),
                    tooltip="Pick predefined style."),
                io.String.Input("text",
                    multiline=True, dynamic_prompts=True,
                    tooltip="Prompt text."),
                io.Combo.Input("camera_angle",
                    options=camera_angle_options(), default="none",
                    tooltip="Optional camera angle prepended to prompt."),
                io.Combo.Input("tech_preset",
                    options=tech_preset_options(),
                    default="none",
                    tooltip=(
                        "Technical lens/quality preset appended after '|' separator. "
                        "Compact 'lens_*': token-efficient. Detailed 'tech_*': more descriptive."
                    )),
            ],
            outputs=[
                io.Conditioning.Output(tooltip="Encoded conditioning"),
                io.String.Output(tooltip="Final assembled prompt"),
            ],
        )

    @classmethod
    def validate_inputs(cls, **kwargs) -> bool | str:
        return True

    @classmethod
    def execute(cls, clip=None, customization="", style=None,
                text="", camera_angle="none", tech_preset="none",
                **kwargs) -> io.NodeOutput:

        if clip is None:
            raise RuntimeError(
                "clip input is None — connect a CLIP output from a checkpoint "
                "or CLIP loader node before running."
            )

        customization = customization or ""
        style         = style or cls.style_names()[0]
        text          = text or ""
        camera_angle  = camera_angle or "none"
        tech_preset   = tech_preset or "none"

        template = _resolve_template(style, customization)
        prompt   = build_prompt(text, template, camera_angle, tech_preset)

        logger.debug(
            f"[StyleEncoder] style={style!r} template={'yes' if template else 'none'} "
            f"angle={camera_angle!r} tech={tech_preset!r} len={len(prompt)}"
        )

        tokens = clip.tokenize(prompt)
        conditioning = clip.encode_from_tokens_scheduled(tokens)

        return io.NodeOutput(conditioning, prompt)

    # ── Cached option builders ────────────────────────────────────────────────

    @staticmethod
    @cache
    def style_names() -> list[str]:
        names = ["none"]
        for group in PREDEFINED_STYLE_GROUPS:
            names.extend(group.get_names(quoted=True))
        logger.info(f'[StyleEncoder] loaded {len(names) - 1} styles.')
        return names

    @staticmethod
    @cache
    def _predefined_style_index() -> dict[str, str]:
        index: dict[str, str] = {}
        for group in PREDEFINED_STYLE_GROUPS:
            for name in group.get_names(quoted=False):
                tmpl = group.get_style_template(name)
                if tmpl:
                    index[name] = tmpl
        return index

    @classmethod
    def get_predefined_style_template(cls, style_name: str) -> str:
        normalized = style_name.strip('"').strip("'").strip()
        return cls._predefined_style_index().get(normalized, "")
