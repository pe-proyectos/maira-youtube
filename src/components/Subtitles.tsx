import { useCurrentFrame, interpolate } from "remotion";
import { type Segment } from "../utils/timing";

interface SubtitlesProps {
  segments: Segment[];
}

function splitIntoPhrases(text: string): string[] {
  // Split on natural pauses - roughly every 8-12 words
  const words = text.split(" ");
  const phrases: string[] = [];
  let current: string[] = [];

  for (const word of words) {
    current.push(word);
    // Break at natural points or when we hit ~8 words
    if (current.length >= 8 || word.endsWith(".") || word.endsWith(",")) {
      phrases.push(current.join(" "));
      current = [];
    }
  }
  if (current.length > 0) {
    phrases.push(current.join(" "));
  }
  return phrases;
}

export const Subtitles: React.FC<SubtitlesProps> = ({ segments }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: "absolute",
        bottom: "8%",
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 60px",
      }}
    >
      {segments.map((segment, i) => {
        if (frame < segment.startFrame || frame > segment.endFrame) return null;

        const phrases = splitIntoPhrases(segment.text);
        const segDuration = segment.endFrame - segment.startFrame;
        const phraseDuration = segDuration / phrases.length;

        return (
          <div
            key={i}
            style={{
              maxWidth: 900,
              textAlign: "center",
            }}
          >
            {phrases.map((phrase, j) => {
              const phraseStart = segment.startFrame + j * phraseDuration;
              const phraseEnd = segment.startFrame + (j + 1) * phraseDuration;

              const opacity = interpolate(
                frame,
                [phraseStart, phraseStart + 8, phraseEnd - 5, phraseEnd],
                [0, 1, 1, 0],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
              );

              if (opacity <= 0) return null;

              return (
                <div
                  key={j}
                  style={{
                    opacity,
                    color: "#ffffff",
                    fontSize: 52,
                    fontWeight: 700,
                    fontFamily: "Arial, Helvetica, sans-serif",
                    textAlign: "center",
                    textShadow:
                      "0 0 20px rgba(0,0,0,0.9), 0 4px 8px rgba(0,0,0,0.8), 2px 2px 0 #000, -2px -2px 0 #000, -2px 2px 0 #000, 2px -2px 0 #000",
                    lineHeight: 1.3,
                    letterSpacing: "-0.01em",
                  }}
                >
                  {phrase}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};
