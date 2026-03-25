#!/bin/bash
# Render Short 02 v2 - JJK Voto Vinculante
# Strategy: render each segment separately, then concat + add audio + subs
set -euo pipefail

BASE="/data/workspace/maira-youtube/videos/002-jjk-voto"
JJK="/data/workspace/maira-youtube/assets/jujutsu-kaisen/images"
CSM="/data/workspace/maira-youtube/assets/chainsaw-man/images"
MISC="/data/workspace/maira-youtube/assets/misc"
BGM="/data/workspace/maira-youtube/assets/jujutsu-kaisen/music/kaikai-kitan-cover-es.mp3"
VOICE="$BASE/audio.mp3"
SUBS="$BASE/subtitles.ass"
OUTPUT="$BASE/short-02-v2.mp4"
TMPDIR="$BASE/tmp-segments"

W=1080; H=1920; FPS=30

mkdir -p "$TMPDIR"
echo "=== RENDERING SHORT 02 v2 (segmented) ==="

# Define segments: image, duration, effect
declare -a IMAGES=(
  "$JJK/binding-vow-manga.jpg"
  "$JJK/gojo-anime.jpg"
  "$JJK/binding-vow-anime.jpg"
  "$MISC/jjk-binding-vow-reddit.png"
  "$CSM/denji-defeated.jpg"
  "$CSM/denji-bodies.jpg"
  "$CSM/denji.png"
  "$MISC/jjk-binding-vow-reddit.png"
  "$JJK/sukuna-binding-vow-anime.jpg"
  "$JJK/yuji-finger.jpg"
  "$JJK/sukuna.png"
)

# Duration in seconds for each segment (including 0.5s transition overlap)
declare -a DURS=(3.5 5.5 3.5 3.5 6.5 10.0 7.0 6.1 8.9 8.4 9.6)

# Zoompan expressions
declare -a EFFECTS=(
  "z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
  "z='1.15':x='min(on*1.5,iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
  "z='min(zoom+0.002,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
  "z='1.0':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
  "z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
  "z='1.15':x='iw/2-(iw/zoom/2)':y='max(ih/zoom*0.1,ih/2-(ih/zoom/2)-on*0.8)'"
  "z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
  "z='1.05':x='iw/2-(iw/zoom/2)+sin(on*0.5)*10':y='ih/2-(ih/zoom/2)+cos(on*0.7)*8'"
  "z='1.15':x='min(on*1.5,iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
  "z='if(eq(on,1),1.2,max(zoom-0.0006,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
  "z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
)

# Step 1: Render each segment individually
echo "[1/4] Rendering segments..."
for i in "${!IMAGES[@]}"; do
  IMG="${IMAGES[$i]}"
  DUR="${DURS[$i]}"
  EFFECT="${EFFECTS[$i]}"
  FRAMES=$(python3 -c "print(int($DUR * $FPS))")
  SEG_OUT="$TMPDIR/seg-$(printf '%02d' $i).mp4"
  
  echo "  Segment $i: $(basename "$IMG") (${DUR}s, ${FRAMES} frames)"
  
  ffmpeg -y -loop 1 -i "$IMG" \
    -filter_complex "
      scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},
      zoompan=${EFFECT}:d=${FRAMES}:s=${W}x${H}:fps=${FPS},
      setsar=1,drawbox=c=black@0.3:replace=1:t=fill
    " \
    -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
    -t "$DUR" \
    "$SEG_OUT" 2>/dev/null
  
  echo "    ✅ Done ($(ls -lh "$SEG_OUT" | awk '{print $5}'))"
done

# Step 2: Create concat file with xfade transitions
echo "[2/4] Concatenating with transitions..."
# Use simple concat (xfade is too memory-heavy for 11 segments)
# Instead, use concat demuxer
CONCAT_FILE="$TMPDIR/concat.txt"
> "$CONCAT_FILE"
for i in "${!IMAGES[@]}"; do
  echo "file 'seg-$(printf '%02d' $i).mp4'" >> "$CONCAT_FILE"
done

ffmpeg -y -f concat -safe 0 -i "$CONCAT_FILE" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  "$TMPDIR/video-concat.mp4" 2>/dev/null

echo "  ✅ Video concatenated"

# Step 3: Add audio (voice + bgm) and subtitles
echo "[3/4] Adding audio + subtitles..."
SUBS_ESC="${SUBS//:/\\:}"

ffmpeg -y \
  -i "$TMPDIR/video-concat.mp4" \
  -i "$VOICE" \
  -i "$BGM" \
  -filter_complex "
    [2:a]atrim=start=15,asetpts=PTS-STARTPTS,volume=0.12,afade=t=in:d=2[bgm];
    [1:a]apad=whole_dur=67[voice];
    [voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0,atrim=duration=67[aout];
    [0:v]ass='${SUBS_ESC}':fontsdir='/tmp/'[vout]
  " \
  -map '[vout]' -map '[aout]' \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -shortest \
  -movflags +faststart \
  "$OUTPUT" 2>/dev/null

echo "  ✅ Final video with audio + subtitles"

# Step 4: Cleanup
echo "[4/4] Cleaning up..."
rm -rf "$TMPDIR"

echo ""
echo "=== RENDER COMPLETE ==="
ls -lh "$OUTPUT"
ffprobe -v quiet -show_entries format=duration,size -show_entries stream=width,height,codec_name -of json "$OUTPUT" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for s in d['streams']:
    if 'width' in s: print(f'✅ Video: {s[\"width\"]}x{s[\"height\"]} {s[\"codec_name\"]}')
    elif s.get('codec_name'): print(f'✅ Audio: {s[\"codec_name\"]}')
f=d['format']
print(f'✅ Duration: {float(f[\"duration\"]):.1f}s')
print(f'✅ Size: {int(f[\"size\"])/1024/1024:.1f}MB')
"
