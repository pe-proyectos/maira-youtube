#!/bin/bash
# Render Short 02 v3 - Segment-by-segment approach (robust, no hangs)
# ONE ffmpeg at a time, each segment rendered individually then concatenated.
set -euo pipefail

BASE="/data/workspace/maira-youtube/videos/002-jjk-voto"
JJK="/data/workspace/maira-youtube/assets/jujutsu-kaisen/images"
CSM="/data/workspace/maira-youtube/assets/chainsaw-man/images"
MISC="/data/workspace/maira-youtube/assets/misc"
BGM="/data/workspace/maira-youtube/assets/jujutsu-kaisen/music/kaikai-kitan-cover-es.mp3"
VOICE="$BASE/audio.mp3"
SUBS="$BASE/subtitles.ass"
OUTPUT="$BASE/short-02-v3.mp4"
TMP="$BASE/tmp_segments"
W=1080; H=1920; FPS=30

# Clean
rm -rf "$TMP"
mkdir -p "$TMP"

echo "=== RENDERING SHORT 02 v3 (segment-by-segment) ==="

# Segments: image duration effect
# Duration includes 0.1s extra for concat safety
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
declare -a DURS=(3.0 5.0 3.0 3.0 6.0 9.5 6.5 5.6 8.4 7.9 9.14)
declare -a EFFECTS=(zoom_in pan_right zoom_in_fast zoom_in zoom_in_pan pan_up pan_left shake pan_right zoom_out zoom_in)

echo "[1/4] Rendering ${#IMAGES[@]} segments..."

for i in "${!IMAGES[@]}"; do
  IMG="${IMAGES[$i]}"
  DUR="${DURS[$i]}"
  EFF="${EFFECTS[$i]}"
  FRAMES=$(python3 -c "print(int($DUR * $FPS))")
  OUTFILE="$TMP/seg_$(printf '%02d' $i).mp4"
  
  # Calculate zoom speed to fill exactly the duration
  ZOOM_SPEED=$(python3 -c "print(round(0.15 / $FRAMES, 7))")
  FAST_SPEED=$(python3 -c "print(round(0.25 / $FRAMES, 7))")
  PAN_SPEED=$(python3 -c "print(round(140 / $FRAMES, 4))")
  PAN_Y_SPEED=$(python3 -c "print(round(250 / $FRAMES, 4))")
  
  case "$EFF" in
    zoom_in)
      ZP="zoompan=z='1+on*$ZOOM_SPEED':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    zoom_in_fast)
      ZP="zoompan=z='1+on*$FAST_SPEED':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    zoom_out)
      ZP="zoompan=z='1.15-on*$ZOOM_SPEED':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    pan_right)
      ZP="zoompan=z='1.15':x='on*$PAN_SPEED':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    pan_left)
      ZP="zoompan=z='1.15':x='iw-iw/zoom-on*$PAN_SPEED':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    pan_up)
      ZP="zoompan=z='1.15':x='iw/2-(iw/zoom/2)':y='ih/zoom*0.5-on*$PAN_Y_SPEED':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    zoom_in_pan)
      ZP="zoompan=z='1+on*$ZOOM_SPEED':x='on*$PAN_SPEED':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    shake)
      ZP="zoompan=z='1.05+on*$(python3 -c "print(round(0.05/$FRAMES,7))")':x='iw/2-(iw/zoom/2)+sin(on*0.3)*15':y='ih/2-(ih/zoom/2)+cos(on*0.4)*12':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
    *)
      ZP="zoompan=z='1+on*$ZOOM_SPEED':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${W}x${H}:fps=$FPS" ;;
  esac
  
  echo -n "  Seg $i: $(basename $IMG) (${DUR}s, $FRAMES frames) "
  
  ffmpeg -y -loop 1 -i "$IMG" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},${ZP},setsar=1,drawbox=c=black@0.3:replace=1:t=fill" \
    -t "$DUR" -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
    -an "$OUTFILE" 2>/dev/null
  
  SIZE=$(ls -lh "$OUTFILE" | awk '{print $5}')
  echo "✅ Done ($SIZE)"
done

echo ""
echo "[2/4] Concatenating segments..."

# Create concat list
> "$TMP/concat.txt"
for i in "${!IMAGES[@]}"; do
  echo "file 'seg_$(printf '%02d' $i).mp4'" >> "$TMP/concat.txt"
done

ffmpeg -y -f concat -safe 0 -i "$TMP/concat.txt" \
  -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
  -an "$TMP/video_only.mp4" 2>/dev/null

echo "✅ Video concatenated"

echo ""
echo "[3/4] Adding audio + subtitles..."

VOICE_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$VOICE")
TOTAL_DUR=$(python3 -c "print(round($VOICE_DUR + 5, 2))")

ASS_ESC=$(echo "$SUBS" | sed 's/:/\\:/g')

ffmpeg -y -i "$TMP/video_only.mp4" -i "$VOICE" -i "$BGM" \
  -filter_complex \
    "[0:v]trim=duration=$TOTAL_DUR,setpts=PTS-STARTPTS,ass='$ASS_ESC':fontsdir='/tmp/'[vout]; \
     [2:a]atrim=start=15,asetpts=PTS-STARTPTS,volume=0.12,afade=t=in:d=2[bgm]; \
     [1:a]apad=whole_dur=$TOTAL_DUR[voice]; \
     [voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0,atrim=duration=$TOTAL_DUR[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest -movflags +faststart \
  "$OUTPUT" 2>/dev/null

echo "✅ Final video with audio + subtitles"

echo ""
echo "[4/4] Cleaning up..."
rm -rf "$TMP"

echo ""
echo "=== RENDER COMPLETE ==="
ls -lh "$OUTPUT"

ffprobe -v quiet -print_format json -show_format -show_streams "$OUTPUT" | python3 -c "
import sys,json
info=json.load(sys.stdin)
for s in info['streams']:
    if s['codec_type']=='video': print(f\"✅ Video: {s['width']}x{s['height']} {s['codec_name']}\")
    elif s['codec_type']=='audio': print(f\"✅ Audio: {s['codec_name']}\")
fmt=info['format']
print(f\"✅ Duration: {float(fmt['duration']):.1f}s\")
print(f\"✅ Size: {int(fmt['size'])/1024/1024:.1f}MB\")
"
