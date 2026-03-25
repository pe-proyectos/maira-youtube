import { Composition } from "remotion";
import { Short01 } from "./compositions/Short01";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Short01"
        component={Short01}
        durationInFrames={1230}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
