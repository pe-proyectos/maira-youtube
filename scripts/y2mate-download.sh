#!/bin/bash
# y2mate-download.sh — Download YouTube audio/video via y2mate API
# Usage: ./y2mate-download.sh <youtube-video-id> <format:mp3|mp4> <output-path>
# Example: ./y2mate-download.sh dQw4w9WgXcQ mp3 ./output.mp3

set -euo pipefail

VIDEO_ID="${1:?Usage: $0 <youtube-video-id> <format> <output-path>}"
FORMAT="${2:-mp3}"
OUTPUT="${3:?Usage: $0 <youtube-video-id> <format> <output-path>}"

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REFERER="https://v1.y2mate.nu/es/"
ORIGIN="https://v1.y2mate.nu"

timestamp() { date +%s; }

# Step 0: Get auth params from y2mate page (dynamic, changes over time)
echo "[1/5] Fetching auth params from y2mate..."
AUTH_DATA=$(curl -sL "$REFERER" | grep -oP "var json = JSON.parse\('\K[^']+")
if [ -z "$AUTH_DATA" ]; then
  echo "ERROR: Could not extract auth data from y2mate page"
  exit 1
fi

# Decode auth using node (matches y2mate's JS exactly)
AUTH_PARAMS=$(node -e "
const json = JSON.parse('$AUTH_DATA');
let e = '';
for (let t = 0; t < json[0].length; t++)
  e += String.fromCharCode(json[0][t] - json[2][json[2].length - (t + 1)]);
if (json[1]) e = e.split('').reverse().join('');
if (e.length > 32) e = e.substring(0, 32);
const key = String.fromCharCode(json[6]);
console.log(key + '=' + e);
")

if [ -z "$AUTH_PARAMS" ]; then
  echo "ERROR: Could not decode auth params"
  exit 1
fi
echo "  Auth OK"

# Step 1: Initialize
echo "[2/5] Initializing conversion..."
INIT_RESP=$(curl -s "https://eta.etacloud.org/api/v1/init?${AUTH_PARAMS}&t=$(timestamp)" \
  -H "Referer: $REFERER" -H "Origin: $ORIGIN" -H "User-Agent: $UA")

INIT_ERROR=$(echo "$INIT_RESP" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('error','1'))" 2>/dev/null || echo "1")
if [ "$INIT_ERROR" != "0" ]; then
  echo "ERROR: Init failed: $INIT_RESP"
  exit 1
fi

CONVERT_URL=$(echo "$INIT_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['convertURL'])")
echo "  Init OK"

# Step 2: Convert (may redirect once)
echo "[3/5] Starting conversion..."
CONV_RESP=$(curl -s "${CONVERT_URL}&v=${VIDEO_ID}&f=${FORMAT}&t=$(timestamp)" \
  -H "Referer: $REFERER" -H "Origin: $ORIGIN" -H "User-Agent: $UA")

REDIRECT=$(echo "$CONV_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('redirect',0))" 2>/dev/null || echo "0")

if [ "$REDIRECT" = "1" ]; then
  REDIRECT_URL=$(echo "$CONV_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['redirectURL'])")
  CONV_RESP=$(curl -s "${REDIRECT_URL}&v=${VIDEO_ID}&f=${FORMAT}&t=$(timestamp)" \
    -H "Referer: $REFERER" -H "Origin: $ORIGIN" -H "User-Agent: $UA")
fi

PROGRESS_URL=$(echo "$CONV_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('progressURL',''))" 2>/dev/null || echo "")
DOWNLOAD_URL=$(echo "$CONV_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('downloadURL',''))" 2>/dev/null || echo "")
TITLE=$(echo "$CONV_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('title','unknown'))" 2>/dev/null || echo "unknown")

if [ -z "$DOWNLOAD_URL" ]; then
  echo "ERROR: No download URL received: $CONV_RESP"
  exit 1
fi
echo "  Title: $TITLE"

# Step 3: Wait for progress (if needed)
if [ -n "$PROGRESS_URL" ]; then
  echo "[4/5] Waiting for conversion..."
  for i in $(seq 1 30); do
    PROG_RESP=$(curl -s "${PROGRESS_URL}&t=$(timestamp)" \
      -H "Referer: $REFERER" -H "Origin: $ORIGIN" -H "User-Agent: $UA")
    PROG=$(echo "$PROG_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('progress',0))" 2>/dev/null || echo "0")
    
    if [ "$PROG" -ge 3 ] 2>/dev/null; then
      echo "  Conversion complete"
      break
    fi
    
    if [ "$i" -eq 30 ]; then
      echo "ERROR: Conversion timed out after 90s"
      exit 1
    fi
    sleep 3
  done
else
  echo "[4/5] No progress step needed"
fi

# Step 4: Download
echo "[5/5] Downloading..."
mkdir -p "$(dirname "$OUTPUT")"
curl -L -o "$OUTPUT" "${DOWNLOAD_URL}&s=3&v=${VIDEO_ID}&f=${FORMAT}" \
  -H "Referer: $REFERER" -H "Origin: $ORIGIN" -H "User-Agent: $UA" \
  --max-time 300

# Verify
SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
TYPE=$(file -b "$OUTPUT")
echo ""
echo "✅ Downloaded: $OUTPUT ($SIZE)"
echo "   Format: $TYPE"
echo "   Title: $TITLE"
