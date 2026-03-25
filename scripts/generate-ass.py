#!/usr/bin/env python3
"""Generate ASS subtitle file from ElevenLabs with-timestamps response."""
import json, re

BASE = '/data/workspace/maira-youtube/videos/001-final-csm'

with open(f'{BASE}/tts-response.json') as f:
    data = json.load(f)

alignment = data['alignment']
chars = alignment['characters']
starts = alignment['character_start_times_seconds']
ends = alignment['character_end_times_seconds']

# Build words from characters
words = []
current_word = ''
word_start = None
word_end = None

for i, ch in enumerate(chars):
    if ch in ('\n', ' ', '\t'):
        if current_word:
            words.append((current_word, word_start, word_end))
            current_word = ''
            word_start = None
    else:
        if ch in ('.',',','!','?',':',';'):
            # attach punctuation to previous word
            if current_word:
                current_word += ch
                word_end = ends[i]
            elif words:
                w, ws, we = words[-1]
                words[-1] = (w + ch, ws, ends[i])
            continue
        if word_start is None:
            word_start = starts[i]
        current_word += ch
        word_end = ends[i]

if current_word:
    words.append((current_word, word_start, word_end))

print(f"Total words: {len(words)}")
for w in words[:10]:
    print(f"  {w[0]:20s} {w[1]:.3f} - {w[2]:.3f}")

# Gold phrases - words that should be highlighted
gold_phrases = [
    "pero ya qué",
    "una novia", "comida caliente", "un perro",
    "lo triste",
    "destruyó",
    "suelta la motosierra",
    "quién es él",
    "gracias Chainsaw Man",
    "elegir a alguien",
    "no te elija de vuelta",
    "final honesto",
    "duele más",
]

# Build full text to find gold word indices
full_words_lower = [w[0].lower().rstrip('.,!?;:') for w in words]

gold_indices = set()
for phrase in gold_phrases:
    phrase_words = phrase.lower().split()
    plen = len(phrase_words)
    for i in range(len(full_words_lower) - plen + 1):
        if full_words_lower[i:i+plen] == phrase_words:
            for j in range(i, i + plen):
                gold_indices.add(j)

print(f"Gold word indices: {sorted(gold_indices)}")

# Group words into display chunks (1-2 words)
# Short words get paired, long words stay alone
chunks = []
i = 0
while i < len(words):
    w1 = words[i]
    # Try to pair short words
    if i + 1 < len(words) and len(w1[0]) <= 4 and len(words[i+1][0]) <= 6:
        w2 = words[i+1]
        text = f"{w1[0]} {w2[0]}"
        is_gold = i in gold_indices or (i+1) in gold_indices
        chunks.append((text, w1[1], w2[2], is_gold))
        i += 2
    else:
        is_gold = i in gold_indices
        chunks.append((w1[0], w1[1], w1[2], is_gold))
        i += 1

def fmt_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

# Write ASS
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,100,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,2,0,1,5,0,5,50,50,10,1
Style: Gold,Montserrat Black,100,&H0000D7FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,2,0,1,5,0,5,50,50,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

for text, start, end, is_gold in chunks:
    style = "Gold" if is_gold else "Default"
    # Add small padding to end time for readability
    end_padded = min(end + 0.05, chunks[chunks.index((text,start,end,is_gold)) + 1][1] if (text,start,end,is_gold) != chunks[-1] else end + 0.5)
    ass += f"Dialogue: 0,{fmt_time(start)},{fmt_time(end_padded)},{style},,0,0,0,,{text}\n"

with open(f'{BASE}/subtitles.ass', 'w') as f:
    f.write(ass)

print(f"\nASS file written with {len(chunks)} dialogue lines")
print(f"Duration: {chunks[0][1]:.2f}s - {chunks[-1][2]:.2f}s")
