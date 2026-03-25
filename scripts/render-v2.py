#!/usr/bin/env python3
"""Render YouTube Short with Ken Burns, xfade transitions, ASS subs, and audio mix."""
import subprocess, os, sys

BASE = '/data/workspace/maira-youtube/videos/001-final-csm'
IMG_DIR = '/data/workspace/maira-youtube/public/manga/chapter-232-hq'
FONT = '/tmp/Montserrat-Black.ttf'
W, H = 1080, 1920
TOTAL_DUR = 47  # seconds
FPS = 30
TRANS_DUR = 1  # transition duration in seconds

images = ['page-03.jpg', 'page-10.jpg', 'page-22.jpg', 'page-25.jpg', 'page-28.jpg']
# Segment durations (before transitions): must sum to TOTAL_DUR + (n-1)*TRANS_DUR
# Segments: 0-6, 6-15, 15-28, 28-35, 35-47 = 6,9,13,7,12 = 47
# With 4 transitions of 1s each, each segment needs +overlap
# segment_dur = [6+0.5, 9+1, 13+1, 7+1, 12+0.5] adjusted
# Actually for xfade: each segment just needs to be long enough
seg_durs = [7, 10, 14, 8, 12]  # slightly padded for transitions

# Zoompan expressions for each segment
# zoompan: z=zoom, x=pan_x, y=pan_y, d=duration_frames, s=output_size
zoompan_effects = [
    # Seg 1: Slow zoom in (center)
    f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={seg_durs[0]*FPS}:s={W}x{H}:fps={FPS}",
    # Seg 2: Vertical pan top to bottom
    f"zoompan=z='1.15':x='iw/2-(iw/zoom/2)':y='min(on*2,ih-ih/zoom)':d={seg_durs[1]*FPS}:s={W}x{H}:fps={FPS}",
    # Seg 3: Slow zoom out
    f"zoompan=z='if(eq(on,1),1.2,max(zoom-0.0005,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={seg_durs[2]*FPS}:s={W}x{H}:fps={FPS}",
    # Seg 4: Horizontal pan left to right
    f"zoompan=z='1.15':x='min(on*1.5,iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={seg_durs[3]*FPS}:s={W}x{H}:fps={FPS}",
    # Seg 5: Slow zoom in + vertical drift
    f"zoompan=z='min(zoom+0.0006,1.12)':x='iw/2-(iw/zoom/2)':y='min(on*0.5,ih/4)':d={seg_durs[4]*FPS}:s={W}x{H}:fps={FPS}",
]

transitions = ['slideright', 'dissolve', 'slideup', 'fade']

# Build ffmpeg command
inputs = []
filter_parts = []

# Input images
for i, img in enumerate(images):
    inputs.extend(['-loop', '1', '-i', f'{IMG_DIR}/{img}'])

# Input audio
inputs.extend(['-i', f'{BASE}/audio-timestamps.mp3'])  # input 5
inputs.extend(['-i', f'{BASE}/bgm-full.mp3'])  # input 6

# Build video filter
# Step 1: Scale + crop + zoompan for each image
for i in range(5):
    filter_parts.append(
        f"[{i}:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
        f"{zoompan_effects[i]},"
        f"setpts=PTS-STARTPTS,format=yuva420p[v{i}]"
    )

# Step 2: Chain xfade transitions
# xfade between v0 and v1
offsets = []
cumulative = 0
for i in range(4):
    cumulative += seg_durs[i] - TRANS_DUR
    offsets.append(cumulative)

filter_parts.append(
    f"[v0][v1]xfade=transition={transitions[0]}:duration={TRANS_DUR}:offset={offsets[0]}[x01]"
)
filter_parts.append(
    f"[x01][v2]xfade=transition={transitions[1]}:duration={TRANS_DUR}:offset={offsets[1]}[x02]"
)
filter_parts.append(
    f"[x02][v3]xfade=transition={transitions[2]}:duration={TRANS_DUR}:offset={offsets[2]}[x03]"
)
filter_parts.append(
    f"[x03][v4]xfade=transition={transitions[3]}:duration={TRANS_DUR}:offset={offsets[3]}[xfinal]"
)

# Step 3: Dark overlay + trim to exact duration
filter_parts.append(
    f"[xfinal]drawbox=x=0:y=0:w={W}:h={H}:color=black@0.3:t=fill,"
    f"trim=duration={TOTAL_DUR},setpts=PTS-STARTPTS[vdark]"
)

# Step 4: Burn ASS subtitles
ass_path = f'{BASE}/subtitles.ass'.replace(':', '\\:')
filter_parts.append(
    f"[vdark]ass='{ass_path}':fontsdir='/tmp/'[vout]"
)

# Step 5: Audio mix - voice + bgm from 30s at 15% volume, fade out last 3s
filter_parts.append(
    f"[6:a]atrim=start=30,asetpts=PTS-STARTPTS,volume=0.15,afade=t=out:st={TOTAL_DUR-3}:d=3[bgm]"
)
filter_parts.append(
    f"[5:a]apad=whole_dur={TOTAL_DUR}[voice]"
)
filter_parts.append(
    f"[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0,atrim=duration={TOTAL_DUR}[aout]"
)

filter_complex = ';\n'.join(filter_parts)

output = f'{BASE}/short-01-final.mp4'

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
    output
]

print("Running FFmpeg...")
print(f"Filter complex:\n{filter_complex}\n")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if result.returncode != 0:
    print("STDERR:", result.stderr[-3000:])
    sys.exit(1)

print(f"Output: {output}")
# Verify
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', output],
    capture_output=True, text=True
)
import json
info = json.loads(probe.stdout)
for s in info['streams']:
    if s['codec_type'] == 'video':
        print(f"Video: {s['width']}x{s['height']} {s['codec_name']} {s.get('r_frame_rate')}")
    elif s['codec_type'] == 'audio':
        print(f"Audio: {s['codec_name']} {s.get('sample_rate')}Hz")
fmt = info['format']
print(f"Duration: {float(fmt['duration']):.2f}s")
print(f"Size: {int(fmt['size'])/1024/1024:.1f}MB")
