import React from 'react';
import { Composition, staticFile, continueRender, delayRender } from 'remotion';
import { OmniComposition } from './components/OmniComposition';
import fs from 'fs';
import path from 'path';

// Read codex.json at build time
const codexPath = path.join(process.cwd(), 'public', 'codex.json');
const codexRaw = fs.readFileSync(codexPath, 'utf-8');
const codex = JSON.parse(codexRaw);

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
