import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Background } from "../components/Background";
import { Subtitles } from "../components/Subtitles";
import { type Segment, secondsToFrames } from "../utils/timing";

const segments: Segment[] = [
  {
    text: "No debería decir esto pero ya qué.",
    startFrame: 0,
    endFrame: 90,
  },
  {
    text: "232 capítulos y Denji sigue queriendo lo mismo que al inicio una novia comida caliente un perro y nada cambió pero eso no es lo triste.",
    startFrame: 90,
    endFrame: 360,
  },
  {
    text: "Lo que me destruyó es que en el último capítulo Denji suelta la motosierra y la suelta para sostener a una chica que ni sabe quién es él y le dice gracias Chainsaw Man como si fuera cualquier persona.",
    startFrame: 360,
    endFrame: 690,
  },
  {
    text: "Y ahí entendí todo porque no se trata de ganar la pelea sino de elegir a alguien aunque esa persona no te elija de vuelta.",
    startFrame: 690,
    endFrame: 930,
  },
  {
    text: "Fujimoto no te dio un final feliz te dio un final honesto y eso duele más.",
    startFrame: 930,
    endFrame: 1230,
  },
];

const panels = [
  { src: "manga/chapter-232/page-03.jpg", startFrame: 0, endFrame: 90 },
  { src: "manga/chapter-232/page-10.jpg", startFrame: 90, endFrame: 225 },
  { src: "manga/chapter-232/page-20.jpg", startFrame: 225, endFrame: 360 },
  { src: "manga/chapter-232/page-22.jpg", startFrame: 360, endFrame: 525 },
  { src: "manga/chapter-232/page-23.jpg", startFrame: 525, endFrame: 690 },
  { src: "manga/chapter-232/page-25.jpg", startFrame: 690, endFrame: 930 },
  { src: "manga/chapter-232/page-28.jpg", startFrame: 930, endFrame: 1080 },
  { src: "manga/chapter-232/page-15.jpg", startFrame: 1080, endFrame: 1230 },
];

export const Short01: React.FC = () => {
  return (
    <AbsoluteFill>
      <Background panels={panels} />
      <Subtitles segments={segments} />
      <Audio src={staticFile("audio/short-01.mp3")} />
    </AbsoluteFill>
  );
};
