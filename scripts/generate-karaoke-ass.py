#!/usr/bin/env python3
"""Generate ASS subtitles with word-by-word highlight using karaoke timing.
Uses \\k (instant fill) per word instead of \\kf (gradual), so each word
highlights as a whole unit. One line per phrase, not per word."""
import json

BASE = '/data/workspace/maira-youtube/videos/002-jjk-voto'
OUTPUT = f'{BASE}/subtitles.ass'

with open(f'{BASE}/timestamps.json') as f:
    ts_data = json.load(f)

chars = ts_data['characters']
starts = ts_data['character_start_times_seconds']
ends = ts_data['character_end_times_seconds']

# Build words with timestamps
words = []
current_word = ''
word_start = None
for i, c in enumerate(chars):
    if c in (' ', '\n'):
        if current_word:
            words.append((current_word, word_start, ends[i-1]))
            current_word = ''
            word_start = None
    else:
        if word_start is None:
            word_start = starts[i]
        current_word += c
if current_word:
    words.append((current_word, word_start, ends[-1]))

def fmt_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

# Group into 3-5 word phrases
phrases = []
phrase_words = []
for w in words:
    phrase_words.append(w)
    if len(phrase_words) >= 4 or (len(phrase_words) >= 3 and w[0].rstrip().endswith(('.', ',', '?', '!'))):
        phrases.append(phrase_words[:])
        phrase_words = []
if phrase_words:
    phrases.append(phrase_words[:])

# ASS header
# PrimaryColour = white (before karaoke fills)
# SecondaryColour = highlight color (karaoke fills with this)
# Using \k (instant snap) instead of \kf (gradual fill)
HIGHLIGHT = "&H0000BFFF"  # Orange-ish in BGR
WHITE = "&H00FFFFFF"

ass = f"""[Script Info]
Title: Short 02 - JJK Voto Vinculante
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,72,{HIGHLIGHT},{WHITE},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# One dialogue line per phrase with \k tags per word
# \k = instant fill (whole word at once)
# PrimaryColour = filled (highlight), SecondaryColour = unfilled (white)
# So words start white and snap to highlight color
for phrase in phrases:
    p_start = phrase[0][1]
    p_end = phrase[-1][2]
    
    kara_text = ""
    for j, (word, ws, we) in enumerate(phrase):
        dur_cs = int((we - ws) * 100)
        if j > 0:
            kara_text += " "
        kara_text += f"{{\\k{dur_cs}}}{word}"
    
    ass += f"Dialogue: 0,{fmt_time(p_start)},{fmt_time(p_end)},Default,,0,0,0,,{kara_text}\n"

with open(OUTPUT, 'w') as f:
    f.write(ass)

print(f"✅ Karaoke ASS written: {OUTPUT}")
print(f"   Phrases: {len(phrases)} (one line each)")
print(f"   Total words: {len(words)}")
