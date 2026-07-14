import React from 'react';
import { Player } from '@remotion/player';
import { OmniComposition } from './preview/OmniComposition';

/**
 * App — F02 PREVIEW
 * 
 * Charge le codex.json et la video depuis public/,
 * rend la composition en temps reel via @remotion/player.
 * 
 * L'operateur peut cliquer Play pour voir le resultat exact
 * avant de declencher le rendu GitHub Actions.
 */

// Placeholder — sera connecte au codex.json et video au runtime
const PLACEHOLDER_CODEX = {
  version: '1.0',
  emotion_mode: 'TRISTE',
  narrative_arc: 'setup → twist → emotional_peak → resolution',
  video: {
    source: 'video_coupee.mp4',
    fps: 30,
    total_frames: 300,
    width: 1080,
    height: 1920,
  },
  text_overlays: [],
  zoom_keyframes: [{ frame: 0, scale: 1.0, target_x: 0.5, target_y: 0.5 }],
  color_preset: 'cold_desaturated',
  color_css_filter: 'contrast(0.95) saturate(0.6) brightness(0.9)',
  enhance_4k: true,
  sfx_timeline: [],
  tracking_source: 'tracking_data.json',
};

export default function App() {
  // A DEVELOPPER: charger codex.json et video_coupee.mp4 dynamiquement
  // fetch('/codex.json').then(r => r.json()).then(setCodex)
  // const videoSrc = '/video_coupee.mp4'

  const codex = PLACEHOLDER_CODEX;
  const videoSrc = ''; // sera defini au runtime

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#0a0a0a',
      padding: '20px',
      fontFamily: 'system-ui, sans-serif',
    }}>
      <h1 style={{ color: '#fff', marginBottom: '20px' }}>
        OMNIS-WATCH — F02 Preview
      </h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>
        Mode: {codex.emotion_mode} — Aperçu temps réel
      </p>

      {/* Cadre telephone 9:16 */}
      <div style={{
        width: '100%',
        maxWidth: '405px',
        aspectRatio: '9/16',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
      }}>
        {videoSrc ? (
          <Player
            component={OmniComposition}
            inputProps={{ codex, videoSrc }}
            durationInFrames={codex.video.total_frames}
            fps={codex.video.fps}
            compositionWidth={codex.video.width}
            compositionHeight={codex.video.height}
            style={{ width: '100%', height: '100%' }}
            controls
            loop
          />
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#666',
            textAlign: 'center',
            padding: '20px',
          }}>
            <div>
              <p>Chargement...</p>
              <p style={{ fontSize: '12px', marginTop: '10px' }}>
                Placez codex.json et video_coupee.mp4 dans public/
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Bouton de validation */}
      <div style={{ marginTop: '20px' }}>
        <button
          style={{
            padding: '12px 32px',
            fontSize: '16px',
            background: '#4ecca3',
            color: '#000',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
          onClick={() => {
            // A DEVELOPPER: declencher le rendu GitHub Actions
            alert('Validation — le rendu F03A sera declenche sur GitHub Actions');
          }}
        >
          ✓ Valider et rendre
        </button>
      </div>
    </div>
  );
}
