import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Background } from "../components/Background";
import { Subtitles } from "../components/Subtitles";
import { PNGtuber } from "../components/PNGtuber";
import { type Segment, secondsToFrames } from "../utils/timing";

const segments: Segment[] = [
  {
    text: "No debería decir esto pero ya qué.",
    startFrame: secondsToFrames(0),
    endFrame: secondsToFrames(3),
  },
  {
    text: "232 capítulos y Denji sigue queriendo lo mismo que al inicio una novia comida caliente un perro y nada cambió pero eso no es lo triste.",
    startFrame: secondsToFrames(3),
    endFrame: secondsToFrames(12),
  },
  {
    text: "Lo que me destruyó es que en el último capítulo Denji suelta la motosierra y la suelta para sostener a una chica que ni sabe quién es él y le dice gracias Chainsaw Man como si fuera cualquier persona.",
    startFrame: secondsToFrames(12),
    endFrame: secondsToFrames(23),
  },
  {
    text: "Y ahí entendí todo porque no se trata de ganar la pelea sino de elegir a alguien aunque esa persona no te elija de vuelta.",
    startFrame: secondsToFrames(23),
    endFrame: secondsToFrames(31),
  },
  {
    text: "Fujimoto no te dio un final feliz te dio un final honesto y eso duele más.",
    startFrame: secondsToFrames(31),
    endFrame: secondsToFrames(41),
  },
];

export const Short01: React.FC = () => {
  return (
    <AbsoluteFill>
      <Background />
      <PNGtuber />
      <Subtitles segments={segments} />
      <Audio src={staticFile("audio/short-01.mp3")} />
    </AbsoluteFill>
  );
};
