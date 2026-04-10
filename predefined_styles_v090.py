# predefined_styles_v090.py
# Focus: Light Physics, Color Atmosphere, Mood. 
# Excluded: Object descriptions, skin textures, specific materials.

PREDEFINED_STYLES = {
    # --- ETALON CORE ---
    "GQ": (
        "high-contrast editorial fashion profile, global cool-spectrum illumination, "
        "physically plausible blue ambient light with natural falloff, deep shadows with cyan-teal bias, "
        "crisp neutral-cool highlights, ultra-high micro-contrast, strict colour separation, "
        "sharp clean punchy rendering, cold high-fashion mood"
    ),
    "Dramatic_Light_Shadow": (
        "dramatic lighting, heavy shadows, chiaroscuro, high contrast, moody atmosphere, "
        "volumetric lighting, rim light, deep blacks, cinematic tension, mysterious, "
        "sculpted light, preserved texture, slight highlight glow"
    ),

    # --- STUDIO LIGHTING VARIANTS (Geometry & Hardness) ---
    "Studio_Rembrandt": (
        "studio lighting, rembrandt pattern, triangular cheek highlight, dramatic shadow side, "
        "classic portrait geometry, controlled fall-off, moody depth"
    ),
    "Studio_Butterfly": (
        "studio lighting, butterfly pattern, paramount lighting, shadow under nose, "
        "symmetrical frontal light, glamour aesthetic, smooth transitions, high key potential"
    ),
    "Studio_Split": (
        "studio lighting, split pattern, 90-degree key light, half-face illumination, "
        "strong lateral shadow, dramatic duality, high contrast geometry"
    ),
    "Studio_Loop": (
        "studio lighting, loop pattern, small nose shadow connecting to cheek shadow, "
        "30-45 degree key angle, dimensional modeling, standard portrait geometry"
    ),
    "Studio_Clamshell": (
        "studio lighting, clamshell pattern, dual frontal sources, fill from below, "
        "minimized shadows, soft even illumination, beauty dish aesthetic, flat but dimensional"
    ),
    "Studio_HighKey": (
        "studio lighting, high key setup, overexposed background, minimal shadows, "
        "bright even illumination, airy atmosphere, low contrast ratio, clean white dominance"
    ),
    "Studio_LowKey": (
        "studio lighting, low key setup, dark background, dominant shadows, "
        "isolated highlights, high contrast ratio, mysterious atmosphere, deep black dominance"
    ),
    "Studio_Rim": (
        "studio lighting, rim light pattern, back-lighting only, silhouette emphasis, "
        "halo effect, separation from background, edge definition, dark center"
    ),
    "Studio_Broad": (
        "studio lighting, broad lighting pattern, key light on wide side of face, "
        "filling frame with light, lower contrast feel, open shadow geometry"
    ),
    "Studio_Short": (
        "studio lighting, short lighting pattern, key light on narrow side of face, "
        "shadow side towards camera, slimming effect, higher contrast feel, dramatic geometry"
    ),

    # --- COLORED AMBIENT (Physics of Colored Light) ---
    "Ambient_Blue": (
        "global blue ambient illumination, cool spectrum dominance, natural blue falloff, "
        "cyan-teal shadow bias, crisp cool highlights, cold atmospheric mood, physical blue scattering"
    ),
    "Ambient_Green": (
        "global green ambient illumination, forest spectrum dominance, natural green falloff, "
        "mossy shadow bias, neutral-green highlights, eerie or natural mood, physical green scattering"
    ),
    "Ambient_Orange": (
        "global orange ambient illumination, warm spectrum dominance, natural orange falloff, "
        "amber shadow bias, golden highlights, cozy or sunset mood, physical orange scattering"
    ),
    "Ambient_Red": (
        "global red ambient illumination, intense warm spectrum dominance, natural red falloff, "
        "crimson shadow bias, bright red highlights, passionate or danger mood, physical red scattering"
    ),

    # --- NATURAL & ENVIRONMENTAL LIGHT ---
    "Natural_Window": (
        "natural window light, directional soft source, large area illumination, "
        "gradual fall-off, soft shadows, realistic indoor physics, neutral daylight balance"
    ),
    "Golden_Hour": (
        "golden hour sunlight, low angle warm source, long soft shadows, "
        "orange-gold spectrum, lens flare potential, dreamy warm atmosphere, natural glow"
    ),
    "Blue_Hour": (
        "blue hour twilight, diffused cool ambient, no direct sun, "
        "deep blue uniform illumination, soft shadowless look, calm evening mood, urban cool"
    ),
    "Neon_Night": (
        "neon night lighting, multiple colored point sources, hard localized shadows, "
        "high saturation spill, wet surface reflections, cyberpunk atmosphere, mixed color temperature"
    ),
    "Candlelight": (
        "candlelight illumination, single warm point source, flickering dynamic, "
        "rapid fall-off, deep warm shadows, orange-yellow spectrum, intimate dark mood"
    ),
    "Volumetric_Fog": (
        "volumetric fog lighting, visible light beams, god rays, scattering medium, "
        "atmospheric depth, hazy glow, soft diffusion, ethereal mood"
    ),

    # --- CINEMATIC & SPECIAL ---
    "Cinematic_Teal_Orange": (
        "cinematic teal and orange grade, complementary color contrast, "
        "teal shadows, orange skin tones (neutral), movie blockbusters look, color graded balance"
    ),
    "Noir_Monochrome": (
        "noir monochrome lighting, black and white spectrum, extreme contrast, "
        "hard shadows, venetian blind patterns, mystery atmosphere, grainy texture light"
    ),
    "Cyberpunk_Cool": (
        "cyberpunk cool lighting, blue and magenta mix, futuristic neon sources, "
        "dark background, high saturation, sci-fi atmosphere, artificial light physics"
    )
}

def get_style(name: str) -> str:
    """Returns style string or fallback to GQ."""
    return PREDEFINED_STYLES.get(name, PREDEFINED_STYLES["GQ"])

def list_styles() -> list:
    """Returns list of all available style keys."""
    return list(PREDEFINED_STYLES.keys())
