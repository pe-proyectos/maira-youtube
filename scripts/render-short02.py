#!/usr/bin/env python3
"""Render Short 02 - JJK Voto Vinculante. Deterministic FFmpeg pipeline."""
import subprocess, sys, os, json

BASE = '/data/workspace/maira-youtube/videos/002-jjk-voto'
ASSETS_JJK = '/data/workspace/maira-youtube/assets/jujutsu-kaisen/images'
ASSETS_CSM = '/data/workspace/maira-youtube/assets/chainsaw-man/images'
ASSETS_MISC = '/data/workspace/maira-youtube/assets/misc'
BGM = '/data/workspace/maira-youtube/assets/jujutsu-kaisen/music/kaikai-kitan-cover-es.mp3'
VOICE = f'{BASE}/audio.mp3'
OUTPUT = f'{BASE}/short-02-v1.mp4'

W, H = 1080, 1920
FPS = 30
TOTAL_DUR = 62  # seconds (rounded up from 61.7)
BGM_VOL = 0.12
BGM_START = 15  # start bgm from 15s into the song
TRANS_DUR = 0.5  # transition duration

# Segments: (start, end, image_path, zoompan_effect)
# For segments with 2 images, we handle specially
segments = [
    # 0: Intro - use binding vow as placeholder (no pngtuber yet)
    (0.0, 3.0, f'{ASSETS_JJK}/binding-vow-manga.jpg', 'zoom_in'),
    # 1: Gojo
    (3.0, 8.0, f'{ASSETS_JJK}/gojo-anime.jpg', 'pan_right'),
    # 2: Binding vow anime
    (8.0, 11.0, f'{ASSETS_JJK}/binding-vow-anime.jpg', 'zoom_in_fast'),
    # 3: Reddit post
    (11.0, 14.0, f'{ASSETS_MISC}/jjk-binding-vow-reddit.png', 'static'),
    # 4: Denji defeated
    (14.0, 20.0, f'{ASSETS_CSM}/denji-defeated.jpg', 'zoom_in'),
    # 5: Denji bodies
    (20.0, 29.5, f'{ASSETS_CSM}/denji-bodies.jpg', 'pan_up'),
    # 6: Denji (will crossfade to yuji mid-segment)
    (29.5, 36.0, f'{ASSETS_CSM}/denji.png', 'zoom_in'),
    # 7: Reddit post again
    (36.0, 41.6, f'{ASSETS_MISC}/jjk-binding-vow-reddit.png', 'shake'),
    # 8: Sukuna binding vow
    (41.6, 50.0, f'{ASSETS_JJK}/sukuna-binding-vow-anime.jpg', 'pan_right'),
    # 9: Gojo blindfold + yuji finger
    (50.0, 57.9, f'{ASSETS_JJK}/yuji-finger.jpg', 'zoom_out'),
    # 10: Sukuna on black - fade to black
    (57.9, 62.0, f'{ASSETS_JJK}/sukuna.png', 'zoom_in'),
]

def zoompan_expr(effect, dur_frames):
    """Generate zoompan filter expression."""
    if effect == 'zoom_in':
        return f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'zoom_in_fast':
        return f"zoompan=z='min(zoom+0.002,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'zoom_out':
        return f"zoompan=z='if(eq(on,1),1.2,max(zoom-0.0006,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'pan_right':
        return f"zoompan=z='1.15':x='min(on*1.5,iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'pan_up':
        return f"zoompan=z='1.15':x='iw/2-(iw/zoom/2)':y='max(ih/zoom*0.1, ih/2-(ih/zoom/2)-on*0.8)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'static':
        return f"zoompan=z='1.0':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"
    elif effect == 'shake':
        return f"zoompan=z='1.05':x='iw/2-(iw/zoom/2)+sin(on*0.5)*10':y='ih/2-(ih/zoom/2)+cos(on*0.7)*8':d={dur_frames}:s={W}x{H}:fps={FPS}"
    else:
        return f"zoompan=z='1.0':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur_frames}:s={W}x{H}:fps={FPS}"

# Build FFmpeg command
inputs = []
filter_parts = []
n = len(segments)

# Add image inputs
for i, (start, end, img, effect) in enumerate(segments):
    inputs.extend(['-loop', '1', '-i', img])

# Add audio inputs
voice_idx = n
bgm_idx = n + 1
inputs.extend(['-i', VOICE])
inputs.extend(['-i', BGM])

# Process each segment with zoompan
for i, (start, end, img, effect) in enumerate(segments):
    dur = end - start + TRANS_DUR  # pad for transitions
    dur_frames = int(dur * FPS)
    zp = zoompan_expr(effect, dur_frames)
    # Scale input to fit vertical, pad with black if needed
    filter_parts.append(
        f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
        f"{zp},setsar=1[v{i}]"
    )

# Chain with xfade transitions
transitions = ['dissolve', 'fadeblack', 'dissolve', 'slideleft', 'dissolve', 'fadeblack', 'slideleft', 'dissolve', 'fadeblack', 'fade']
offsets = []
for i in range(n):
    start, end = segments[i][0], segments[i][1]
    if i == 0:
        offsets.append(0)
    # offset for xfade = cumulative duration - transition overlap
    
# Calculate xfade offsets
cumulative = 0
xfade_offsets = []
for i in range(n - 1):
    dur_i = segments[i][1] - segments[i][0]
    cumulative += dur_i
    xfade_offsets.append(cumulative - TRANS_DUR)

# Build xfade chain
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

# Add dark overlay for text readability
filter_parts.append(
    f"[vmerged]drawbox=c=black@0.3:replace=1:t=fill[vdark]"
)

# Fade to black at the end (last 2 seconds)
filter_parts.append(
    f"[vdark]fade=t=out:st={TOTAL_DUR-2}:d=2,trim=duration={TOTAL_DUR},setpts=PTS-STARTPTS[vout]"
)

# Audio: voice + bgm mixed
filter_parts.append(
    f"[{bgm_idx}:a]atrim=start={BGM_START},asetpts=PTS-STARTPTS,"
    f"volume={BGM_VOL},afade=t=in:d=2,afade=t=out:st={TOTAL_DUR-3}:d=3[bgm]"
)
filter_parts.append(
    f"[{voice_idx}:a]apad=whole_dur={TOTAL_DUR}[voice]"
)
filter_parts.append(
    f"[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0,"
    f"atrim=duration={TOTAL_DUR}[aout]"
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
print("RENDERING SHORT 02 - JJK Voto Vinculante")
print("=" * 60)
print(f"\nSegments: {n}")
print(f"Duration: {TOTAL_DUR}s")
print(f"Output: {OUTPUT}")
print(f"\nFilter complex:\n{filter_complex}\n")
print("Running FFmpeg...\n")

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
print(f"✅ Duration: {float(fmt['duration']):.2f}s")
print(f"✅ Size: {int(fmt['size'])/1024/1024:.1f}MB")
print(f"\n🎬 Output: {OUTPUT}")
