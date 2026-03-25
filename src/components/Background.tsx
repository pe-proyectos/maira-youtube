import { AbsoluteFill, Img, useCurrentFrame, interpolate, staticFile } from "remotion";

interface PanelSegment {
  src: string;
  startFrame: number;
  endFrame: number;
}

interface BackgroundProps {
  panels: PanelSegment[];
}

export const Background: React.FC<BackgroundProps> = ({ panels }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }}>
      {panels.map((panel, i) => {
        if (frame < panel.startFrame || frame > panel.endFrame) return null;

        const progress = (frame - panel.startFrame) / (panel.endFrame - panel.startFrame);
        const scale = interpolate(progress, [0, 1], [1.0, 1.12]);
        const translateY = interpolate(progress, [0, 1], [0, -15]);

        const opacity = interpolate(
          frame,
          [panel.startFrame, panel.startFrame + 10, panel.endFrame - 5, panel.endFrame],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        return (
          <AbsoluteFill key={i} style={{ opacity }}>
            <Img
              src={staticFile(panel.src)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center",
                transform: `scale(${scale}) translateY(${translateY}px)`,
              }}
            />
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: "rgba(0,0,0,0.4)",
              }}
            />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
