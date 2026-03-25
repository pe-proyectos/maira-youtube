import { useCurrentFrame } from "remotion";
import { type Segment, getOpacity } from "../utils/timing";

interface SubtitlesProps {
  segments: Segment[];
}

export const Subtitles: React.FC<SubtitlesProps> = ({ segments }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: "absolute",
        bottom: "25%",
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 60px",
      }}
    >
      {segments.map((segment, i) => {
        const opacity = getOpacity(frame, segment.startFrame, segment.endFrame);
        if (opacity <= 0) return null;
        return (
          <div
            key={i}
            style={{
              opacity,
              color: "#ffffff",
              fontSize: 64,
              fontWeight: 800,
              fontFamily: "Arial, Helvetica, sans-serif",
              textAlign: "center",
              textShadow:
                "0 0 20px rgba(0,0,0,0.9), 0 4px 8px rgba(0,0,0,0.8), 2px 2px 0 #000, -2px -2px 0 #000",
              lineHeight: 1.3,
              letterSpacing: "-0.02em",
            }}
          >
            {segment.text}
          </div>
        );
      })}
    </div>
  );
};
