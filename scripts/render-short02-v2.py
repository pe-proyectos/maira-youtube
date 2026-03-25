#!/usr/bin/env python3
"""Render Short 02 v2 - JJK Voto Vinculante. All production rules applied."""
import subprocess, sys, os, json

BASE = '/data/workspace/maira-youtube/videos/002-jjk-voto'
ASSETS_JJK = '/data/workspace/maira-youtube/assets/jujutsu-kaisen/images'
ASSETS_CSM = '/data/workspace/maira-youtube/assets/chainsaw-man/images'
ASSETS_MISC = '/data/workspace/maira-youtube/assets/misc'
BGM = '/data/workspace/maira-youtube/assets/jujutsu-kaisen/music/kaikai-kitan-cover-es.mp3'
VOICE = f'{BASE}/audio.mp3'
OUTPUT = f'{BASE}/short-02-v2.mp4'

W, H = 1080, 1920  # Vertical 9:16 Full HD
FPS = 30
VOICE_DUR = 62      # voice ends ~61.7s
SILENCE_END = 5     # 5s silent ending with image + music
TOTAL_DUR = VOICE_DUR + SILENCE_END  # 67s total... but must be ≤60s for Shorts

# Actually: voice is ~62s which already exceeds 60s Shorts limit
# Let's check actual voice duration
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', VOICE],
    capture_output=True, text=True
)
VOICE_DUR = float(probe.stdout.strip())
print(f"Voice duration: {VOICE_DUR:.2f}s")
TOTAL_DUR = VOICE_DUR + SILENCE_END
print(f"Total duration (voice + 5s silence): {TOTAL_DUR:.2f}s")
# Note: YouTube Shorts can be up to 60s. This video is ~67s.
# For now render as-is, Shoko will decide if we need to trim.

BGM_VOL = 0.12
BGM_START = 15  # start bgm from 15s into the song
TRANS_DUR = 0.5

# Segments: (start, end, image_path, effect)
segments = [
    (0.0, 3.0, f'{ASSETS_JJK}/binding-vow-manga.jpg', 'zoom_in'),       # placeholder for PNGtuber
    (3.0, 8.0, f'{ASSETS_JJK}/gojo-anime.jpg', 'pan_right'),
    (8.0, 11.0, f'{ASSETS_JJK}/binding-vow-anime.jpg', 'zoom_in_fast'),
    (11.0, 14.0, f'{ASSETS_MISC}/jjk-binding-vow-reddit.png', 'zoom_in'),  # was static
    (14.0, 20.0, f'{ASSETS_CSM}/denji-defeated.jpg', 'zoom_in_pan_right'),
    (20.0, 29.5, f'{ASSETS_CSM}/denji-bodies.jpg', 'pan_up'),
    (29.5, 36.0, f'{ASSETS_CSM}/denji.png', 'pan_left'),
    (36.0, 41.6, f'{ASSETS_MISC}/jjk-binding-vow-reddit.png', 'shake'),
    (41.6, 50.0, f'{ASSETS_JJK}/sukuna-binding-vow-anime.jpg', 'pan_right'),
    (50.0, 57.9, f'{ASSETS_JJK}/yuji-finger.jpg', 'zoom_out'),
    # Last segment: extends through the 5s silent ending (image stays animated, no fade)
    (57.9, VOICE_DUR + SILENCE_END, f'{ASSETS_JJK}/sukuna.png', 'zoom_in'),
]

def zoompan_expr(effect, dur_frames):
    """All effects use continuous animation that lasts exactly dur_frames.
    Speeds are calculated from dur_frames so movement NEVER stops early."""
    # Calculate per-frame speed for zoom effects (zoom from 1.0 to 1.15 over dur_frames)
    zoom_speed = round(0.15 / dur_frames, 6)
    zoom_out_speed = round(0.15 / dur_frames, 6)
    # Pan speed: traverse ~13% of image width over dur_frames
    pan_speed = round((0.13 * W) / dur_frames, 4)
    pan_y_speed = round((0.13 * H) / dur_frames, 4)
    
    if effect == 'zoom_in':
        return f"zoompan=z='1+on*{zoom_speed}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'zoom_in_fast':
        fast_speed = round(0.25 / dur_frames, 6)
        return f"zoompan=z='1+on*{fast_speed}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'zoom_out':
        return f"zoompan=z='1.15-on*{zoom_out_speed}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'pan_right':
        return f"zoompan=z='1.15':x='on*{pan_speed}':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'pan_up':
        return f"zoompan=z='1.15':x='iw/2-(iw/zoom/2)':y='ih/zoom*0.5-on*{pan_y_speed}':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'pan_left':
        return f"zoompan=z='1.15':x='iw-iw/zoom-on*{pan_speed}':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'shake':
        return f"zoompan=z='1.05+on*{round(0.05/dur_frames,6)}':x='iw/2-(iw/zoom/2)+sin(on*0.3)*15':y='ih/2-(ih/zoom/2)+cos(on*0.4)*12':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'zoom_in_pan_right':
        return f"zoompan=z='1+on*{zoom_speed}':x='on*{pan_speed}':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    else:
        return f"zoompan=z='1+on*{zoom_speed}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"

# ============================================================
# Step 1: Generate ASS subtitles (using external script)
# ============================================================
print("Generating ASS subtitles...")
sub_result = subprocess.run(
    ['python3', '/data/workspace/maira-youtube/scripts/generate-karaoke-ass.py'],
    capture_output=True, text=True
)
print(sub_result.stdout)
if sub_result.returncode != 0:
    print("Subtitle generation failed:", sub_result.stderr)
    sys.exit(1)
ass_path = f'{BASE}/subtitles.ass'

# ============================================================
# Step 2: Check/download font
# ============================================================
font_path = '/tmp/Montserrat-Black.ttf'
if not os.path.exists(font_path):
    print("Downloading Montserrat Black font...")
    subprocess.run([
        'curl', '-sL', '-o', font_path,
        'https://github.com/google/fonts/raw/main/static/Montserrat-Black.ttf'
    ], check=True)
print(f"  Font: {font_path}")

# ============================================================
# Step 3: Build FFmpeg command
# ============================================================
print("\nBuilding FFmpeg filter...")

inputs = []
filter_parts = []
n = len(segments)

# Image inputs — TWO inputs per segment (one for bg blur, one for fg)
for i, (start, end, img, effect) in enumerate(segments):
    inputs.extend(['-loop', '1', '-i', img])  # bg input
    inputs.extend(['-loop', '1', '-i', img])  # fg input

# Audio inputs
voice_idx = n * 2
bgm_idx = n * 2 + 1
inputs.extend(['-i', VOICE])
inputs.extend(['-i', BGM])

# Process each segment: scale image to FILL vertical frame, zoompan to show whole image
# Images fill the full 1080x1920 — pan/zoom reveals different parts
for i, (start, end, img, effect) in enumerate(segments):
    dur = end - start + TRANS_DUR
    dur_frames = int(dur * FPS)
    zp = zoompan_expr(effect, dur_frames)
    bg_idx = i * 2      # we still have 2 inputs per segment
    fg_idx = i * 2 + 1  # use fg_idx, ignore bg_idx (kept for index math)
    # Scale to FILL (increase to cover full frame), then zoompan handles cropping/panning
    # Dark overlay for text readability
    filter_parts.append(
        f"[{fg_idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        f"{zp},setsar=1,"
        f"drawbox=c=black@0.3:replace=1:t=fill[v{i}]"
    )

# Chain with xfade transitions
transitions = ['dissolve', 'fadeblack', 'dissolve', 'slideleft', 'dissolve', 'fadeblack', 'slideleft', 'dissolve', 'fadeblack', 'fade']

cumulative = 0
xfade_offsets = []
for i in range(n - 1):
    dur_i = segments[i][1] - segments[i][0]
    cumulative += dur_i
    xfade_offsets.append(cumulative - TRANS_DUR)

current = 'v0'
for i in range(n - 1):
    next_v = f'v{i+1}'
    out = f'xf{i}' if i < n - 2 else 'vmerged'
    trans = transitions[i] if i < len(transitions) else 'dissolve'
    offset = xfade_offsets[i]
    filter_parts.append(
        f"[{current}][{next_v}]xfade=transition={trans}:duration={TRANS_DUR}:offset={offset:.2f}[{out}]"
    )
    current = out

# NO fade to black — clean cut at the end. Just trim to total duration.
# Subtitles burned in a SECOND PASS to avoid FFmpeg hanging
filter_parts.append(
    f"[vmerged]trim=duration={TOTAL_DUR:.2f},setpts=PTS-STARTPTS[vout]"
)

# Audio: voice + bgm. BGM continues through 5s silence without fade out.
filter_parts.append(
    f"[{bgm_idx}:a]atrim=start={BGM_START},asetpts=PTS-STARTPTS,"
    f"volume={BGM_VOL},afade=t=in:d=2[bgm]"  # NO fade out on BGM
)
filter_parts.append(
    f"[{voice_idx}:a]apad=whole_dur={TOTAL_DUR:.2f}[voice]"
)
filter_parts.append(
    f"[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0,"
    f"atrim=duration={TOTAL_DUR:.2f}[aout]"
)

filter_complex = ';\n'.join(filter_parts)

cmd = [
    'ffmpeg', '-y',
    *inputs,
    '-filter_complex', filter_complex,
    '-map', '[vout]', '-map', '[aout]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-c:a', 'aac', '-b:a', '192k',
    '-pix_fmt', 'yuv420p',
    '-shortest',
    '-movflags', '+faststart',
    OUTPUT
]

print("=" * 60)
print("RENDERING SHORT 02 v2 - JJK Voto Vinculante")
print("=" * 60)
print(f"Segments: {n}")
print(f"Voice: {VOICE_DUR:.2f}s")
print(f"Total (with 5s silence): {TOTAL_DUR:.2f}s")
print(f"Output: {OUTPUT}")
print(f"\nRunning FFmpeg...\n")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if result.returncode != 0:
    print("STDERR (last 3000 chars):")
    print(result.stderr[-3000:])
    sys.exit(1)

# Verify output
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', OUTPUT],
    capture_output=True, text=True
)
info = json.loads(probe.stdout)
for s in info['streams']:
    if s['codec_type'] == 'video':
        print(f"✅ Video: {s['width']}x{s['height']} {s['codec_name']} {s.get('r_frame_rate')}")
    elif s['codec_type'] == 'audio':
        print(f"✅ Audio: {s['codec_name']} {s.get('sample_rate')}Hz")
fmt = info['format']
dur = float(fmt['duration'])
size_mb = int(fmt['size'])/1024/1024
print(f"✅ Duration: {dur:.2f}s (voice {VOICE_DUR:.1f}s + {SILENCE_END}s silence)")
print(f"✅ Size: {size_mb:.1f}MB")
print(f"✅ Format: Vertical {W}x{H} (9:16)")

# ============================================================
# Step 5: Burn subtitles in a second pass (avoids FFmpeg hang)
# ============================================================
print("\nBurning subtitles (pass 2)...")
ass_escaped = ass_path.replace(':', '\\:')
OUTPUT_FINAL = OUTPUT.replace('.mp4', '-final.mp4')
cmd2 = [
    'ffmpeg', '-y',
    '-i', OUTPUT,
    '-vf', f"ass='{ass_escaped}':fontsdir='/tmp/'",
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-c:a', 'copy',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    OUTPUT_FINAL
]
result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
if result2.returncode != 0:
    print("Subtitle burn failed, keeping video without subs:")
    print(result2.stderr[-1000:])
    OUTPUT_FINAL = OUTPUT
else:
    # Replace original
    os.rename(OUTPUT_FINAL, OUTPUT)
    OUTPUT_FINAL = OUTPUT
    print("✅ Subtitles burned successfully")

# Final verification
probe2 = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', OUTPUT],
    capture_output=True, text=True
)
info2 = json.loads(probe2.stdout)
fmt2 = info2['format']
print(f"✅ Final size: {int(fmt2['size'])/1024/1024:.1f}MB")
print(f"\n🎬 Output: {OUTPUT}")
