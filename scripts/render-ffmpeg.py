#!/usr/bin/env python3
"""Render 4K vertical video with Ken Burns, subtitles, and audio mixing."""
import subprocess, os, shutil

BASE = "/data/workspace/maira-youtube"
IMG_DIR = f"{BASE}/public/manga/chapter-232-hq"
OUT_DIR = f"{BASE}/videos/001-final-csm"
OUTPUT = f"{OUT_DIR}/short-01-4k.mp4"
VOICEOVER = f"{OUT_DIR}/audio-v4.mp3"
BGM = f"{OUT_DIR}/bgm-full.mp3"
FONT = "/tmp/Montserrat-Bold.ttf"
TMP = "/tmp/ffmpeg_render"

W, H, FPS, DUR = 2160, 3840, 30, 47

os.makedirs(TMP, exist_ok=True)

# Image segments: (file, start_s, end_s, effect)
segments = [
    ("page-03.jpg", 0, 6, "zoom_in", 1.0, 1.15),
    ("page-10.jpg", 6, 15, "zoom_in", 1.0, 1.08),
    ("page-22.jpg", 15, 28, "zoom_out", 1.15, 1.0),
    ("page-25.jpg", 28, 35, "zoom_in", 1.0, 1.08),
    ("page-28.jpg", 35, 47, "zoom_in", 1.0, 1.12),
]

# Step 1: Generate each segment with zoompan
seg_files = []
for i, (img, start, end, effect, z_start, z_end) in enumerate(segments):
    dur_s = end - start
    frames = dur_s * FPS
    img_path = f"{IMG_DIR}/{img}"
    out_path = f"{TMP}/seg{i}.mp4"
    seg_files.append(out_path)
    
    if os.path.exists(out_path):
        print(f"Segment {i} exists, skipping")
        continue
    
    # zoompan: z goes from z_start to z_end over frames
    # z = z_start + (z_end - z_start) * (on/frames)
    z_expr = f"{z_start}+({z_end}-{z_start})*(on/{frames})"
    # Center the zoom: x = iw/2-(iw/zoom/2), y = ih/2-(ih/zoom/2)
    x_expr = "iw/2-(iw/zoom/2)"
    y_expr = "ih/2-(ih/zoom/2)"
    
    # Dark overlay: colorchannelmixer to darken by 0.3
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
        "-vf", (
            f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
            f"crop={W*2}:{H*2},"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={W}x{H}:fps={FPS},"
            f"colorbalance=rs=-0.3:gs=-0.3:bs=-0.3,"
            f"format=yuv420p"
        ),
        "-t", str(dur_s), "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        out_path
    ]
    print(f"Rendering segment {i} ({img}, {dur_s}s)...")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Done: {out_path}")

# Step 2: Concatenate segments with crossfade transitions
print("Concatenating segments...")
# Use xfade filter for transitions
# Build complex filter
concat_input = []
for f in seg_files:
    concat_input.extend(["-i", f])

# Simple concat (xfade for transitions)
# Offsets for xfade: each transition is 0.5s
XFADE_DUR = 0.5
# seg durations: 6, 9, 13, 7, 12
seg_durs = [6, 9, 13, 7, 12]

# Build xfade chain
# offset_i = sum(durs[0..i]) - i*xfade_dur
filters = []
current = "[0:v]"
for i in range(1, len(seg_files)):
    offset = sum(seg_durs[:i]) - i * XFADE_DUR
    next_in = f"[{i}:v]"
    out_label = f"[v{i}]" if i < len(seg_files) - 1 else "[vout]"
    filters.append(f"{current}{next_in}xfade=transition=fade:duration={XFADE_DUR}:offset={offset}{out_label}")
    current = out_label

filter_str = ";".join(filters)

concat_out = f"{TMP}/concat.mp4"
cmd = ["ffmpeg", "-y"] + concat_input + [
    "-filter_complex", filter_str,
    "-map", "[vout]", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-pix_fmt", "yuv420p", concat_out
]
subprocess.run(cmd, check=True, capture_output=True)
print(f"Concatenated: {concat_out}")

# Step 3: Add subtitles via drawtext
# Phrases with timing and color
GOLD = "FFD700"
WHITE = "FFFFFF"

phrases = [
    (0.00, 1.32, "No debería decir esto", WHITE),
    (1.66, 2.34, "pero ya qué", GOLD),
    (2.82, 4.50, "232 capítulos", WHITE),
    (4.50, 7.28, "y Denji sigue queriendo\\nlo mismo que al inicio", WHITE),
    (7.78, 8.42, "una novia", GOLD),
    (8.78, 9.54, "comida caliente", GOLD),
    (10.00, 10.46, "un perro", GOLD),
    (10.92, 11.72, "y nada cambió", WHITE),
    (12.22, 13.36, "Pero eso no es lo triste", WHITE),
    (14.10, 16.54, "Lo que me destruyó es que\\nen el último capítulo", WHITE),
    (16.94, 18.26, "Denji suelta la motosierra", GOLD),
    (18.26, 21.30, "y la suelta para sostener\\na una chica", WHITE),
    (21.30, 22.38, "que ni sabe quién es él", GOLD),
    (22.86, 23.34, "y le dice", WHITE),
    (23.92, 25.12, "gracias Chainsaw Man", GOLD),
    (25.66, 27.12, "como si fuera\\ncualquier persona", WHITE),
    (27.12, 28.86, "Y ahí entendí todo", WHITE),
    (29.28, 31.20, "porque no se trata\\nde ganar la pelea", WHITE),
    (31.54, 32.72, "sino de elegir a alguien", GOLD),
    (33.06, 35.12, "aunque esa persona\\nno te elija de vuelta", GOLD),
    (35.78, 37.88, "Fujimoto no te dio\\nun final feliz", WHITE),
    (38.40, 39.82, "te dio un final honesto", GOLD),
    (40.18, 41.18, "y eso duele más", GOLD),
]

# Build drawtext filters
dt_filters = []
for start, end, text, color in phrases:
    # Escape special chars for drawtext
    escaped = text.replace("'", "'\\''").replace(":", "\\:").replace(",", "\\,")
    dt = (
        f"drawtext=fontfile='{FONT}':text='{escaped}'"
        f":fontsize=90:fontcolor=0x{color}"
        f":borderw=5:bordercolor=0x000000"
        f":x=(w-text_w)/2:y=(h-text_h)/2"
        f":enable='between(t,{start},{end})'"
    )
    dt_filters.append(dt)

subtitle_filter = ",".join(dt_filters)

# Step 4: Add subtitles + audio
print("Adding subtitles and audio...")
cmd = [
    "ffmpeg", "-y",
    "-i", concat_out,          # video
    "-i", VOICEOVER,           # voiceover
    "-ss", "30", "-t", "47", "-i", BGM,  # bgm from 30s
    "-filter_complex",
    f"[0:v]{subtitle_filter}[vfinal];"
    f"[1:a]apad=whole_dur=47[vo];"
    f"[2:a]volume=0.15,afade=t=out:st=44:d=3[bgm];"
    f"[vo][bgm]amix=inputs=2:duration=longest[aout]",
    "-map", "[vfinal]", "-map", "[aout]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-t", "47",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    OUTPUT
]
subprocess.run(cmd, check=True)
print(f"\nDone! Output: {OUTPUT}")

# Report
result = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration,size",
                          "-of", "default=noprint_wrappers=1", OUTPUT], capture_output=True, text=True)
print(result.stdout)
sz = os.path.getsize(OUTPUT)
print(f"File size: {sz/1024/1024:.1f} MB")
