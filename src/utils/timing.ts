export interface Segment {
  text: string;
  startFrame: number;
  endFrame: number;
}

export function secondsToFrames(seconds: number, fps: number = 30): number {
  return Math.round(seconds * fps);
}

export function getOpacity(
  frame: number,
  startFrame: number,
  endFrame: number,
  fadeDuration: number = 5
): number {
  if (frame < startFrame || frame > endFrame) return 0;
  const fadeIn = Math.min((frame - startFrame) / fadeDuration, 1);
  const fadeOut = Math.min((endFrame - frame) / fadeDuration, 1);
  return Math.min(fadeIn, fadeOut);
}
