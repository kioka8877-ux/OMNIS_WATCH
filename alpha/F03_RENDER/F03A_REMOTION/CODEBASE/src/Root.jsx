import React from 'react';
import { Composition, staticFile } from 'remotion';
import { OmniComposition } from './components/OmniComposition';
import codex from '../public/codex.json';

export const Root = () => {
  const fps = codex.video?.fps || 30;
  const totalFrames = codex.video?.total_frames || 300;
  const width = codex.video?.width || 1080;
  const height = codex.video?.height || 1920;

  return (
    <>
      <Composition
        id="OmniComposition"
        component={OmniComposition}
        durationInFrames={totalFrames}
        fps={fps}
        width={width}
        height={height}
        props={{
          codex,
          videoSrc: staticFile('video_coupee.mp4'),
        }}
      />
    </>
  );
};
