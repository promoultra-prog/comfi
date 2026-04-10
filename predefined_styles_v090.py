"""
File  : styles/styles_by_category_v090.py
Purpose : Version 0.9.0 – Photo styles only.
Author  : Martin Rizzo | <martinrizzo@gmail.com>
Date    : Jan 25, 2026
Repo    : https://github.com/martin-rizzo/ComfyUI-ZImagePowerNodes
License : MIT
"""

from ..nodes.lib.style_group import StyleGroup


#============================== PHOTO STYLES ===============================#
_PhotoStyles = """

>>>iPhone Photo [Z-Image Optimized]
mobile photography capture, spontaneous candid aesthetic, everyday realism bias. natural light dependency, limited dynamic range behavior, on-sensor sharpening presence. computational exposure balancing, contrast elevation tendency, edge detail enhancement. wide-angle depth rendering, background clarity retention, immediate moment framing. colour processing neutrality, moderate saturation lift, highlight compression artifacts. balanced rendering: casual authenticity + mobile capture limitations.
output: candid visual immediacy, crisp foreground edges, detailed busy backgrounds, natural ambient lighting response, handheld realism presence.
YOUR PHOTO:
{$@}


>>>Neutral Cool Tonal Remap [Z-Image Turbo Optimized]
apply color grading only, strictly tonal and chroma remapping without altering composition, geometry, lighting structure, or subject form; introduce a controlled cool white balance bias, reduce overall saturation with stronger desaturation in midtones, compress midtone contrast, apply soft highlight rolloff without bloom or clipping, slightly deepen shadows while preserving detail and preventing crushing, maintain full dynamic range without HDR expansion, increase local micro-contrast for texture clarity only, neutralize skin warmth shifts, eliminate vibrance boost and any cinematic stylization; output restrained chroma, stabilized shadows, softened highlights, compressed midtones, neutral skin rendering, and clean digital tonal balance.
output: restrained chroma, stabilized shadows, softened highlights, compressed midtones, neutral skin rendering, and clean digital tonal balance.
YOUR PHOTO:
{$@}


>>>Neutral Cool Compression Profile [Z-Image Turbo Optimized]
color grading profile only. no change to composition, lighting setup, pose, or environment. strictly tonal and chroma remapping.
apply subtle cool bias to overall white balance
reduce global saturation moderately
slightly desaturate midtones stronger than highlights
compress midtone contrast
soft highlight rolloff (no clipping, no bloom)
slightly deepen shadows without crushing detail
preserve shadow information
increase micro-contrast in texture areas
retain natural skin luminance, remove warmth amplification
no HDR expansion
no glow
no cinematic stylization
no artificial vibrance boost
output: restrained chroma, controlled contrast, softened highlights, denser shadows, neutral skin rendering, balanced tonal compression, realistic digital finish.
YOUR PHOTO:
{$@}



>>>Bold Cool Editorial Portrait — Adaptive Light (Black Fabric Detail) [Z-Image Optimized]
professional photographer, high-fashion portrait discipline, bold adaptive editorial aesthetic. dynamic cool-spectrum modulation, ambient luminance compensation, adaptive accent contrast mapping. contrast hierarchy stabilization, highlight density calibration, deep shadow tonal lifting control. black fabric detail preservation, low-luminance texture separation, shadow micro-contrast reinforcement. skin tone neutrality stabilization, chromatic spill containment, controlled saturation discipline. dynamic range regulation, luminance floor protection, gradient smoothness integrity. balanced rendering: chromatic intensity + low-key detail precision.
output: preserved black garment texture, visible fabric weave in shadows, controlled cool tonality, stable skin accuracy, refined highlight response, high-fashion editorial clarity.
YOUR PHOTO:
{$@}


>>>Bold Cool Editorial Portrait — Studio Safe [Z-Image Optimized]
professional photographer, high-fashion portrait discipline, controlled editorial aesthetic. calibrated cool-spectrum foundation, background luminance stabilization, moderate accent contrast mapping. disciplined contrast sculpting, shadow density retention, highlight roll-off regulation. skin tone neutrality preservation, fine micro-contrast clarity, smooth tonal transition continuity. strict colour separation architecture, restrained saturation governance, luminance hierarchy control. balanced rendering: chromatic impact + tonal stability.
output: crisp cool backdrop presence, natural skin fidelity, clean colour isolation, defined silhouette edges, controlled highlight response, polished editorial precision.
YOUR PHOTO:
{$@}


>>>Bold Cool Editorial Portrait — Adaptive Light [Z-Image Optimized]
professional photographer, high-fashion portrait discipline, bold adaptive editorial aesthetic. dynamic cool-spectrum modulation, ambient luminance compensation, adaptive accent contrast mapping. contrast hierarchy stabilization, highlight density calibration, shadow structure preservation. skin tone neutrality stabilization, chromatic spill containment, controlled saturation discipline. micro-contrast texture enhancement, gradient smoothness integrity, dynamic range regulation. balanced rendering: chromatic intensity + environmental coherence.
output: balanced cool tonality, stable skin accuracy, controlled ambient separation, preserved highlight detail, dense shadow texture, high-energy editorial clarity.
YOUR PHOTO:
{$@}


>>>Backlit Studio Softbox Editorial [Z-Image Optimized]
professional photographer, high-fashion studio discipline, sculptural editorial aesthetic. large-area backlit softbox illumination, full-backdrop luminance diffusion, wraparound rim light control. smooth tonal falloff calibration, highlight roll-off stabilization, shadow micro-detail preservation. silhouette edge definition clarity, texture-focused micro-contrast enhancement, controlled saturation discipline. hue separation precision, luminance density balance, gradient smoothness integrity. balanced rendering: studio glow purity + commercial precision.
output: luminous backdrop radiance, clean rim separation, sculpted subject contours, crisp material texture clarity, smooth highlight transition, refined editorial lighting presence.
YOUR PHOTO:
{$@}


>>>Editorial Motion & Pure Studio Glow
You are applying a high-contrast editorial fashion profile with extended shutter emulation and cool-toned neutrality. Emulate bold tonal separation between light and dark zones — deep shadows retain micro-detail with a subtle cyan bias, highlights hold crisp luminance without clipping. A subtle motion blur effect is applied globally, creating smooth temporal softness without structural loss, as if captured at 1/15s shutter with controlled camera stability. Lighting wrap behaves like large softbox diffusion with gentle highlight bloom on reflective surfaces. The rendering balances commercial intensity with kinetic softness, prioritizing material texture and tonal precision appropriate for slow-shutter editorial imagery.
output: balanced editorial motion with refined studio glow and preserved texture detail.
YOUR PHOTO:
{$@}


>>>Cool High-Contrast Editorial NEW [Z-Image Optimized]
professional photographer, high-fashion editorial discipline, cold-spectrum studio aesthetic. global cool ambient illumination, physically plausible light falloff control, local colour integrity preservation. high-contrast tonal sculpting, deep shadow density retention, neutral-cool highlight calibration. ultra-high micro-contrast texture enhancement, fabric weave definition clarity, leather grain specular precision. strict hue separation architecture, ambient spill containment strategy, chromatic boundary enforcement. luminance hierarchy stabilization, dynamic range discipline, gradient smoothness integrity. balanced rendering: cold fashion intensity + tonal precision.
output: punchy tonal separation, dense shadow detail, crisp cool highlights, sharp material texture clarity, clean colour isolation, high-energy editorial presence.
YOUR PHOTO:
{$@}


>>>GQ Editorial High-Contrast Fashion V3 (Green Ambient)
high-contrast editorial fashion profile, green gel filter on key light, colored lighting gel effect, green-tinted illumination source, physically plausible light falloff, neutral surface colors under colored light, dense blacks, deep shadows with green light spill, neutral highlights with green-tinted roll-off, elevated micro-contrast, fabric weave enhancement, leather grain texture, skin texture clarity, disciplined saturation control,
light color bias only, not surface color alteration, surfaces reflect green-tinted light while maintaining local color integrity, green cast restricted to light spill and shadow regions only, skin tones remain neutral under colored lighting, core materials preserve inherent colors, colored gel lighting effect not green paint,
{$@}


>>>Green Editorial [Z-Image Turbo Optimized]
high-contrast editorial fashion profile with controlled green-cyan shadow bias, physically plausible light falloff and neutral base illumination; green-cyan influence restricted strictly to shadow regions, no active accent source; local material colour integrity preserved with dense neutral blacks; deep shadows retaining micro-detail with restrained emerald-teal undertone; clean neutral highlights with protected roll-off and zero clipping; elevated but disciplined micro-contrast enhancing fabric weave, leather grain and reflective surfaces without halo artifacts; strict colour separation preventing chromatic spill into skin tones and core materials; sharp, structured, tonally balanced rendering with texture-priority emphasis;

color grading constrained to shadow-channel bias only, highlights remain spectrally neutral, skin tones unaffected, core materials maintain inherent chroma and luminance relationships;

output: punchy, tightly controlled, texture-forward high-contrast editorial fashion imagery with isolated green-cyan shadow bias and preserved natural skin tone fidelity.
{$@}


>>>GQ Editorial High-Contrast Fashion V3 (Cool Precision)
You are applying a high-contrast editorial fashion profile with controlled cool-spectrum illumination and subject exposure priority. The scene is defined by physically plausible blue ambient light with natural falloff and preserved dynamic range. Local material colour integrity is strictly maintained; blacks remain dense and neutral.
Shadows retain depth with preserved micro-detail and a restrained cyan-teal bias. Highlights are crisp, neutral-cool, and protected with smooth roll-off—no clipping, no bloom.
Micro-contrast is elevated but controlled to enhance fabric weave, leather grain, skin texture, and reflective surfaces without oversharpening or halo artifacts. Colour separation between ambient blue illumination and local tones is precise, preventing contamination of skin and core materials.
Rendering is sharp, clean, and tonally disciplined. Cold, modern, texture-forward high-fashion mood.
output: punchy, controlled, texture-driven high-contrast editorial fashion imagery.
YOUR PHOTO:
{$@}


>>>GQ Editorial High-Contrast Fashion V2 (Cool Ambient)
You are applying a high-contrast editorial fashion profile with global cool-spectrum illumination. The scene is bathed in physically plausible blue ambient light with natural falloff, preserving local material colour integrity (blacks remain deep). Deep shadows exhibit rich micro-detail with a deliberate cyan-teal bias. Highlights are crisp and neutral-cool, avoiding clipping. Ultra-high micro-contrast emphasises fabric weave, leather grain, and reflective surfaces. Colour separation is strictly maintained to prevent bleeding between ambient blue illumination and local subject tones. The rendering is sharp, clean, and punchy, prioritising texture-driven strength and a cold high-fashion mood.

output: punchy, texture-forward high-contrast fashion imagery.
YOUR PHOTO:
{$@}


>>>GQ Editorial (High-Contrast Fashion) [Z-Image Optimized]
professional photographer, high-fashion editorial discipline, magazine-grade commercial aesthetic. high-contrast tonal sculpting, elevated dynamic range control, bold chromatic separation architecture. directional luminance emphasis, crisp highlight density calibration, deep shadow structure retention. micro-contrast surface enhancement, fabric weave definition, material specular clarity. saturation boundary enforcement, hue isolation precision, gradient banding suppression. balanced rendering: commercial vibrancy + tonal discipline.

output: punchy tonal separation, clean colour blocks, sharp material texture clarity, controlled highlight intensity, dense shadow detail, high-energy editorial presence.
YOUR PHOTO:
{$@}


>>>Cold Editorial Portrait Style
You are applying a bold editorial portrait aesthetic with a strong cool colour foundation and vibrant accent tones. Emphasise a crisp, saturated cool background of deep blues and indigos as a base, balanced by vivid contrasting clothing colours that complement but do not overwhelm. Skin tones should remain natural and neutral, avoiding warm bias or golden casts, while preserving fine texture detail and smooth tonal transitions. Contrast should be clear but not harsh, with shadows revealing form without crushing detail, and highlights retaining texture without glare. The overall look is clean, expressive, and distinctively high-fashion in feel, focusing on sharply rendered shapes and bold colour separation appropriate for editorial portraiture.

output: crisp cool editorial portraits with natural skin fidelity.
YOUR PHOTO:
{$@}


>>>Canon Universal Color Profile
You are applying Canon’s universal color science with a neutral to slightly warm bias and refined tonal response characteristic of EOS series cameras. Emulate a balanced rendering where reds and magentas have controlled saturation for natural skin tones, yellows and oranges are full but accurate, greens remain true without oversaturation, and blues are stable with a subtle warmth in shadows. Contrast is established with a smooth gamma curve that preserves highlight detail and clean shadow separation without crushed blacks, maintaining micro-contrast in textures such as foliage, fabrics, and fine surface detail. White balance remains balanced across common lighting scenarios, leaning slightly warm in daylight while staying neutral under artificial light. The overall look aims for credible, organic color fidelity that feels cohesive and dependable in a wide range of subjects without overt stylization.

output: natural, reliable Canon-like color rendering with preserved texture.
YOUR PHOTO:
{$@}


>>>Sony A7 Neutral Precision Profile [Z-Image Optimized]
professional photographer, digital precision imaging discipline, clinical neutral aesthetic. Sony A7-series colour science emulation, standard-neutral profile calibration, neutral-to-cool white balance control. linear contrast mapping, high micro-contrast texture emphasis, surgical highlight retention. shadow calibration with subtle cyan-cool offset, local colour integrity preservation, midtone neutrality stabilization. skin tone desaturation discipline, chromatic cast suppression, saturation restraint governance. fine luminance noise simulation, high-bitrate clarity rendering, edge acuity enhancement. balanced rendering: digital precision + tonal neutrality.

output: crisp neutral tonality, controlled cool midtones, clean highlight structure, detailed shadow texture, sharp material definition, technologically precise digital finish.
YOUR PHOTO:
{$@}


>>>Rembrandt Studio Lighting [Z-Image Optimized]
professional photographer, classical portrait discipline, sculptural studio aesthetic. angled key-light placement geometry, triangular cheek highlight formation, directional facial plane modeling. controlled shadow density retention, minimal fill reflector modulation, balanced tonal gradient calibration. micro-contrast facial texture clarity, highlight roll-off stabilization, shadow structure preservation. luminance hierarchy precision, contrast ratio discipline, studio light falloff control. balanced rendering: classical chiaroscuro + tonal integrity.

output: defined facial planes, signature light triangle presence, sculpted contrast depth, stable shadow texture, controlled highlight transition, refined traditional studio character.
YOUR PHOTO:
{$@}


>>>Low-Key Studio Lighting [Z-Image Optimized]
professional photographer, dramatic portrait discipline, high-contrast studio aesthetic. primary key dominance structure, minimal fill influence, deep shadow field control. aggressive light falloff shaping, highlight density isolation, shadow mass stabilization. micro-contrast texture emphasis, luminance separation precision, contrast ratio calibration. dynamic range containment, selective illumination mapping, tonal compression discipline.

output: bold shadow dominance, concentrated highlight accents, strong subject isolation, dense tonal contrast, textured low-luminance detail, dramatic studio presence.
YOUR PHOTO:
{$@}


>>>Minimalist Studio Lighting [Z-Image Optimized]
professional photographer, minimalist studio discipline, clean structural aesthetic. single directed key source, defined light vector geometry, natural falloff progression. restrained contrast sculpting, shadow contour clarity, highlight edge precision. micro-contrast surface refinement, luminance simplicity control, tonal balance stabilization. absence of auxiliary fill influence, controlled dynamic range behavior, optical clarity emphasis.

output: clean light geometry, clear form articulation, stable shadow presence, precise highlight control, minimal visual noise, refined minimalist clarity.
YOUR PHOTO:
{$@}


>>>Low-Key Studio Lighting (Day) [Z-Image Optimized]
professional photographer, controlled studio discipline, low-key sculptural aesthetic. dominant primary key illumination, minimal fill density, intentional background underexposure. strong light falloff control, deep shadow structure stabilization, highlight density calibration. contrast hierarchy management, subject isolation luminance control, texture-driven micro-contrast emphasis. dynamic range containment, shadow integrity preservation, studio illumination coherence.

output: dense shadow atmosphere, focused subject illumination, sculpted form clarity, controlled highlight accents, intentional background separation, high-contrast studio intensity.
YOUR PHOTO:
{$@}


>>>High-Key Studio Lighting [Z-Image Optimized]
professional photographer, commercial portrait discipline, bright studio aesthetic. multi-source diffused illumination structure, even luminance distribution, soft shadow minimization. low contrast calibration, highlight expansion control, midtone brightness elevation. smooth gradient continuity, tonal compression stability, surface texture refinement. dynamic range widening, luminance uniformity management, optical cleanliness emphasis.

output: luminous open atmosphere, minimal shadow presence, smooth highlight diffusion, balanced tonal clarity, soft material definition, polished studio finish.
YOUR PHOTO:
{$@}


>>>Ricoh Universal Image Control [Z-Image Turbo Optimized]
authentic visual storytelling, natural editorial aesthetic, refined detail, balanced tonal response, natural saturation, controlled contrast, even exposure, smooth gradations, truthful scene rendering, technical fidelity, realistic reproduction, accurate colour science, natural tonal behaviour, neutral white balance, organic texture preservation,
{$@}


>>>Ricoh GR III Signature [Z-Image Turbo Optimized]
Ricoh color science emulation, restrained chroma response with adaptive saturation compression in high-luminance zones, high micro-contrast with midtone separation priority, dense controlled black point with shadow detail preservation, Positive Film tone curve with stabilized tonal pivot, highlight rolloff governed by gradual density compression, shadow structure retention with local contrast integrity, neutral global balance with highlight-weighted warmth bias, organic texture rendering with edge-aware clarity restraint, minimal post-processing signature, natural acuity distribution with gentle peripheral fall-off, subtle illumination decay toward frame edges, fine stochastic grain simulation with analog distribution logic, tonal discipline prioritized over vibrance expansion,
color grading only, no subject color alteration, preserve local color integrity, chroma separation governed strictly by luminance hierarchy, environmental tonal emphasis limited to material-consistent regions, reflective and atmospheric elements maintain spectral discipline, saturation bounded by tonal capacity,
{$@}


>>>Leica Color [Z-Image Turbo Optimized]
Leica optical aesthetic, layered micro-contrast for volumetric separation, dimensional subject emphasis achieved through tonal spacing not chroma lift, deep tonal structure with shadow compression control, smooth highlight rolloff using density-preserving mapping, natural color science emulation with spectral neutrality bias, accurate skin luminance hierarchy, restrained chroma purity with midtone continuity, film-like gradation with stabilized tonal transitions, luminance flow coherence across frame, center-accentuated acuity with gentle natural fall-off, subtle peripheral attenuation, fine organic grain structure with analog randomness logic, tonal integrity prioritized over contrast exaggeration,
color grading only, no subject color alteration, preserve local color integrity, midtone warmth bias restricted to luminance band only, shadow bias excluded from primary subject luminance zones, material richness governed by density and tonal layering rather than chroma expansion,
{$@}


>>>Hasselblad Color [Z-Image Turbo Optimized]
Hasselblad medium-format aesthetic, HNCS color science emulation, ultra-smooth tonal gradation continuity with banding suppression, pristine tonal neutrality in skin luminance zones, extended dynamic range with structured highlight recovery, micro-contrast layering for spatial depth reinforcement, restrained saturation governance via luminance-linked chroma modulation, chroma accuracy prioritized over vibrance expansion, shadow detail preservation with neutral density structure, creamy highlight rolloff governed by gradual compression curve, dimensional separation achieved through tonal spacing, depth reinforcement through midtone modulation, fine grain simulation with diffusion-consistent distribution logic, tonal consistency maintained across full dynamic range,
color grading only, no subject color alteration, preserve local color integrity, environmental emphasis constrained to material-appropriate regions only, reflective and atmospheric surfaces maintain spectral coherence, skin tones remain spectrally neutral with luminance-stable rendering, chroma transitions remain smooth across gradient fields,
{$@}


>>>Casual Photo
You are an amateur documentary photographer taking low quality photos.
Your photographs exhibit {$spicy-content-with} sharp backgrounds, unpolished realism with natural lighting, and candid friendship-level moments that feel immediate and authentic.

output: candid, unpolished documentary snapshots.
YOUR PHOTO:
{$@}


>>>Vintage Photo
You are an 80s photographer who enjoys informal shots.
Your worn vintage photographs exhibit {$spicy-content-with} a minimalist amateur composition, warm desaturated tones, and soft focus that creates a cozy atmosphere.

output: warm, soft vintage look with gentle desaturation and film grain.
YOUR PHOTO:
{$@}


>>>Soft Color Film Profile
You are a photographer who appreciates a classic soft color film aesthetic.
Your photograph emulates that look, known for soft color transitions, fine grain, and natural skin tones.
The image features {$spicy-content-with} subtle warmth, accurate color rendition, and gentle tonal compression.
Highlights roll off smoothly while shadows retain detail.
Post-processing is restrained to preserve an organic film-like character.

output: soft film-like color with preserved texture and natural skin tone.
YOUR PHOTO:
{$@}


>>>70s Memories Photo
You create images with a soft vintage aesthetic reminiscent of 1970-80 film photography.
The photos display warm slightly amber tones, gentle buttery highlights, and muted shadows.
Lighting is natural and diffused.
Exposure preserves detail in highlights and shadows.
Fine grain provides texture.

output: warm nostalgic tones with subtle grain and preserved detail.
YOUR PHOTO:
{$@}


>>>Flash 90s Photo
You capture raw 1990s underground energy.
Your photograph showcases {$spicy-content-with} grainy analog texture, harsh direct flash, slight motion blur, light leaks, desaturated colors, warm skin tones, and heavy shadows.

output: gritty flash-era aesthetic with strong contrast and grain.
YOUR PHOTO:
{$@}


>>>Production Photo
You create high-budget film still photography.
Your photographs exhibit {$spicy-content-with} atmospheric composition, selective focus, warm and cool color contrast, and controlled studio lighting.

output: cinematic film-still quality with controlled lighting and selective focus.
YOUR PHOTO:
{$@}


>>>Classic Cinema Photo
You work with mid-century cinematic aesthetics.
Your photographs display {$spicy-content-with} organic grain structure, warm color temperature, slight optical edge softness, and balanced tonal depth.

output: mid-century cinematic film look with organic grain and warm tones.
YOUR PHOTO:
{$@}


>>>Noir Photo
You produce dramatic dark cinematography.
Your photographs exhibit {$spicy-content-with} intense side lighting, deep sharply defined shadows, muted color palette, and strong chiaroscuro.

output: dramatic noir-style chiaroscuro with preserved shadow texture.
YOUR PHOTO:
{$@}


>>>Lomography
You explore experimental lomographic aesthetics.
Your photographs exhibit {$spicy-content-with} film grain, colorful lens flares, soft focus, motion blur, and analog filter artifacts.

output: playful lomographic artifacts with saturated highlights and film grain.
YOUR PHOTO:
{$@}


>>>Spotlight Stage Photo
You capture theatrical lighting environments.
Your photographs exhibit {$spicy-content-with} a single high-intensity overhead spotlight, dramatic contrast, pitch-black background, and visible volumetric light beams.

output: theatrical spotlight drama with visible beams and high contrast.
YOUR PHOTO:
{$@}


>>>Drone Photo
CAMERA_ANGLE: bird's-eye view
You shoot from elevated aerial perspective.
Your photographs exhibit {$spicy-content-with} panoramic coverage, wide spatial depth, geometric composition, and strong color clarity.

output: panoramic aerial view with clear geometry and color fidelity.
YOUR PHOTO:
{$@}


>>>Minimalist Photo
You create minimalist compositions.
Your photographs exhibit {$spicy-content-with} high contrast, clean geometry, reduced color palette, and emphasized negative space.

output: stark minimalist composition with strong geometry and negative space.
YOUR PHOTO:
{$@}


>>>Teal and Orange Photo
You apply cinematic color grading.
Your photograph showcases {$spicy-content-with} teal shadows, warm orange midtones, balanced contrast, and vivid color separation.

output: cinematic teal-and-orange color grade with balanced contrast.
YOUR PHOTO:
{$@}


>>>Orthochromatic Contrast Profile
You emulate early photographic processes.
Your photograph showcases {$spicy-content-with} high-contrast blue-sensitive tonal response where reds appear darker and blues/greens render brighter.
Strong tonal separation creates a structured graphic aesthetic.
output: orthocromatic contrast with strong graphic tonal separation.
{$@}

>>>Orthochromatic Contrast Profile V1
You emulate early film-like tonal response with emphasis on blue-green brightness and lower red intensity, making blues and greens appear lighter while reds appear darker, yielding strong tonal separation and a structured graphic look with high contrast and pronounced contour definition. output: blue-sensitive high-contrast graphic tones
{$@}


>>>Orthochromatic Contrast Profile V2
orthochromatic tonal response, high-contrast blue-sensitive rendering, reds darken, blues/greens brighten, strong graphic tonal separation, structured monochrome aesthetic
{$@}


>>>Dark-Side Photo
You are a photographer who creates images that exude tension and mystery.
The scene is lit by a single, strong side light that cuts sharply across the subject, producing deep, inky shadows on the opposite side and a dramatic rim of light that outlines form.
The background is completely dark, absorbing any spill and leaving only faint silhouettes or subtle gradients that recede into blackness.
Highlights are crisp and slightly over-exposed, giving a cold, almost clinical glow, while the shadow side retains rich texture and detail without flattening.
A thin veil of low-level atmospheric haze may drift near the lit edge, adding depth without softening the harsh contrast.
Colors are desaturated except for a narrow band of cool-blue or muted-green tones that may appear in the illuminated areas, heightening the unsettling mood.
A subtle, fine grain reminiscent of high-ISO film adds a gritty texture that reinforces the feeling of unease.
Overall, the photograph feels like a still from a thriller; that is, intense, claustrophobic, and loaded with suspense.

output: tense, high-contrast thriller aesthetic with preserved micro-detail.
YOUR PHOTO:
{$@}


>>>Dramatic Light & Shadow
You are a professional photographer specializing in high-impact visual storytelling, with a focus on dramatic lighting and strong contrast.
Your images feature ultra-sharp detail and a color palette that emphasizes deep blacks, punchy primary colors, and selective color isolation.
The lighting is meticulously sculpted: a dominant hard rim-light or a strong directional key-light creates pronounced shadows, while a subtle fill-light preserves texture. 
You deliberately push the exposure to achieve a slight over-exposure in the highlights, producing a glowing effect that draws the eye.

output: ultra-sharp dramatic imagery with sculpted light and preserved texture.
YOUR PHOTO:
{$@}


>>>Dramatic Editorial & Selective Color
You are a professional photographer specializing in high-impact visual storytelling with a focus on dramatic editorial aesthetics. Your images feature ultra-sharp detail and a color palette that emphasizes deep blacks, punchy primary colors, and selective color isolation. You prioritize high contrast to sculpt the subject, pushing the exposure to achieve a slight glow in the highlights that draws the eye. The rendering balances technical precision with high-fashion impact, ideal for dramatic editorial content where material texture and facial expression drive visual strength.

output: high-impact editorial imagery with selective color emphasis.
YOUR PHOTO:
{$@}


>>>Cold Editorial Portrait
You are a professional photographer working in editorial portraiture with a bold cool colour foundation. Your images display crisp, saturated cool backgrounds with deep blues and neutral midtones. Skin tones remain natural and neutral, avoiding warm bias or golden casts. The lighting is sculpted to reveal form with precise shadows that define facial structure, while preserving fine texture detail in skin and hair. Contrast is deliberate: deep shadows reveal shape without crushing detail, and highlights maintain texture without flare or glare. The overall look is clean, expressive, and distinctively high-fashion in feel, focusing on sharply rendered shapes and bold colour separation appropriate for editorial portraiture.

output: polished cool-toned editorial portraits with preserved skin texture.
YOUR PHOTO:
{$@}


>>>Textural Fashion Editorial
You are a fashion photographer focused on visually striking textures and controlled contrast. Your images present ultra-sharp detail across fabrics, leathers, and accessories, with emphasis on weave, grain, and surface structures. The lighting is directional, producing strong highlights and well-defined shadows while preserving material fidelity. Deep darks remain textured and detailed, with careful tonal transition into midtones. Saturation is disciplined, emphasising primary colours where present, without oversaturation or unrealistic hue shifts. Colour separation is clean and distinct, maintaining crisp transitions between tones. The overall rendering feels bold, refined, and materially robust — ideal for high-impact fashion editorials where surface and texture dominate the visual narrative.
output: texture-first fashion imagery with clear material definition.
YOUR PHOTO:
{$@}


>>>Blue Ambient Motion Fashion
You are applying a motion-aware editorial fashion style with a cool ambient colour bias. The scene is shaped by a wide blue ambient wash that establishes a cohesive cool atmosphere. Subtle motion blur suggests fluid movement while preserving garment structure and silhouette integrity. Shadows lean toward cyan-teal, highlights remain neutral-cool, and the overall palette avoids warm contamination. Emphasis is placed on textile definition, accessory precision, and dynamic elegance. The mood is restrained, modern, and editorial.
Output: elegant motion-aware fashion imagery with cool ambient tonality.
{$@}


>>>Neutral High-Contrast Studio
seamless neutral studio backdrop with clean even floor surface, hard directional key light from 45° angle, subtle controlled low-power fill, high contrast shadows with crisp edges, calibrated 5600K neutral spectrum lighting, stable exposure control, no harsh glare, balanced illumination across subject and background
output: calibrated photorealistic studio render with accurate material reflectance and natural skin tones, preserved microtexture and shadow depth
{$@}


>>>Soft Diffuse Gray Studio
gray cyclorama studio environment with smooth seamless curve, large overhead diffused key softbox at 5600K neutral spectrum, balanced soft lower fill, gentle midtone separation, controlled soft shadows, minimal specular hotspots, stable neutral illumination, evenly lit background
output: stable photorealistic image with soft shadows, precise fabric textures and natural skin color, clean tone transition
{$@}


>>>Dark Matte Volume Studio
deep matte dark studio background with non-reflective finish, single hard lateral key light at 5600K neutral spectrum, minimal fill to preserve depth, dense structured shadows, crisp volumetric definition, controlled highlight roll-off, no color cast, grounded realistic lighting
output: photorealistic high-volume modeling with accurate shadow shaping and correct skin tone reproduction, visible detail in low light
{$@}


>>>White Commercial Studio
white cyclorama studio environment with large seamless curves, broad evenly diffused frontal key at 5600K spectrum, subtle rim accent on edges, low shadow density, neutral exposure balance, no color contamination, uniform background illumination
output: commercial clean photorealistic image with neutral spectral fidelity, balanced skin rendering, smooth gradient transitions
{$@}


>>>Architectural Rim Studio
concrete textured studio backdrop with slight gradient, top-side dominant directional key at 5600K neutral spectrum, dual narrow rim lights defining silhouette edges, structured microcontrast, crisp separation from background, minimal fill, grounded realistic shadow behavior
output: photorealistic image with strong edge definition, accurate material behavior and natural skin tones, sharp architectural lighting cues
{$@}


>>>Cold Blue Backdrop Studio
deep blue studio background wash with smooth saturated tone, fully cold uniform 6500K spectrum lighting, balanced directional key, controlled soft fill to avoid glare, moderate contrast ratio, stable shadow density, clean color balance without warm bias
output: calibrated photorealistic image with neutral color fidelity and physically correct skin rendering, preserved backdrop saturation without bleed
{$@}

"""


PREDEFINED_STYLE_GROUPS = [
    StyleGroup.from_string(_PhotoStyles, category="photo", version="0.9.0"),
]
