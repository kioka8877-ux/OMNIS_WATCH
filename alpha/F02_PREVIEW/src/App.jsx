import React, { useState, useEffect } from 'react';
import { Player } from '@remotion/player';
import { OmniComposition } from './preview/OmniComposition';

/**
 * App — F02 PREVIEW
 * 
 * Charge dynamiquement le codex.json et la video depuis public/,
 * rend la composition en temps reel via @remotion/player.
 * 
 * L'operateur peut cliquer Play pour voir le resultat exact
 * avant de declencher le rendu GitHub Actions.
 */

export default function App() {
  const [codex, setCodex] = useState(null);
  const [videoSrc, setVideoSrc] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [validated, setValidated] = useState(false);

  // Charger le codex.json et la video au montage
  useEffect(() => {
    async function loadAssets() {
      try {
        // Charger le codex
        const codexResp = await fetch('./codex.json');
        if (!codexResp.ok) {
          throw new Error('codex.json non trouve dans public/');
        }
        const codexData = await codexResp.json();
        setCodex(codexData);

        // La video — on utilise un chemin relatif
        // L'operateur place video_coupee.mp4 dans public/
        setVideoSrc('./video_coupee.mp4');
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }
    loadAssets();
  }, []);

  // Ecran de chargement
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#0a0a0a',
        color: '#888',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', marginBottom: '10px' }}>Chargement...</div>
          <div style={{ fontSize: '14px' }}>Lecture du codex.json et de la video</div>
        </div>
      </div>
    );
  }

  // Ecran d'erreur
  if (error) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#0a0a0a',
        color: '#e94560',
        fontFamily: 'system-ui, sans-serif',
        padding: '20px',
      }}>
        <div style={{ textAlign: 'center', maxWidth: '500px' }}>
          <div style={{ fontSize: '24px', marginBottom: '15px' }}>Erreur</div>
          <div style={{ fontSize: '14px', marginBottom: '20px' }}>{error}</div>
          <div style={{ fontSize: '12px', color: '#666', textAlign: 'left',
            background: '#111', padding: '15px', borderRadius: '8px' }}>
            <p style={{ margin: '0 0 10px 0' }}><strong>Setup requis:</strong></p>
            <p style={{ margin: '0 0 5px 0' }}>1. Placez <code>codex.json</code> dans <code>public/</code></p>
            <p style={{ margin: '0 0 5px 0' }}>2. Placez <code>video_coupee.mp4</code> dans <code>public/</code></p>
            <p style={{ margin: '0' }}>3. Lancez <code>npm run build</code></p>
          </div>
        </div>
      </div>
    );
  }

  // Donnees du codex
  const fps = codex.video?.fps || 30;
  const totalFrames = codex.video?.total_frames || 300;
  const width = codex.video?.width || 1080;
  const height = codex.video?.height || 1920;
  const emotionMode = codex.emotion_mode || 'UNKNOWN';
  const textCount = codex.text_overlays?.length || 0;
  const zoomCount = codex.zoom_keyframes?.length || 0;
  const sfxCount = codex.sfx_timeline?.length || 0;

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
      {/* Header */}
      <div style={{ marginBottom: '20px', textAlign: 'center' }}>
        <h1 style={{ color: '#fff', margin: '0 0 5px 0', fontSize: '22px' }}>
          OMNIS-WATCH — F02 Preview
        </h1>
        <div style={{
          display: 'inline-block',
          padding: '4px 12px',
          background: emotionMode === 'TRISTE' ? '#1a1a3e' :
                      emotionMode === 'WHOLESOME' ? '#1a3e1a' : '#333',
          color: emotionMode === 'TRISTE' ? '#88aaff' :
                 emotionMode === 'WHOLESOME' ? '#88ff88' : '#fff',
          borderRadius: '4px',
          fontSize: '13px',
          fontWeight: 'bold',
        }}>
          Mode: {emotionMode}
        </div>
      </div>

      {/* Cadre telephone 9:16 */}
      <div style={{
        width: '100%',
        maxWidth: '405px',
        aspectRatio: '9/16',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        background: '#000',
      }}>
        <Player
          component={OmniComposition}
          inputProps={{ codex, videoSrc }}
          durationInFrames={totalFrames}
          fps={fps}
          compositionWidth={width}
          compositionHeight={height}
          style={{ width: '100%', height: '100%' }}
          controls
          loop
        />
      </div>

      {/* Infos codex */}
      <div style={{
        marginTop: '15px',
        display: 'flex',
        gap: '15px',
        fontSize: '13px',
        color: '#888',
      }}>
        <span>📝 {textCount} textes</span>
        <span>🔍 {zoomCount} zooms</span>
        <span>🔊 {sfxCount} SFX</span>
        <span>⏱️ {(totalFrames / fps).toFixed(1)}s</span>
      </div>

      {/* Bouton de validation */}
      <div style={{ marginTop: '20px' }}>
        {validated ? (
          <div style={{
            padding: '12px 32px',
            background: '#4ecca3',
            color: '#000',
            borderRadius: '8px',
            fontWeight: 'bold',
            fontSize: '16px',
          }}>
            ✓ Validé — Prêt pour le rendu GitHub Actions
          </div>
        ) : (
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
            onClick={() => setValidated(true)}
          >
            ✓ Valider et rendre
          </button>
        )}
      </div>

      {/* Liste des textes (debug) */}
      <div style={{
        marginTop: '20px',
        width: '100%',
        maxWidth: '405px',
        background: '#111',
        borderRadius: '8px',
        padding: '15px',
        fontSize: '12px',
        color: '#aaa',
      }}>
        <div style={{ marginBottom: '10px', color: '#fff', fontWeight: 'bold' }}>
          Textes du codex:
        </div>
        {codex.text_overlays?.map((overlay, i) => (
          <div key={i} style={{
            padding: '6px 0',
            borderBottom: i < textCount - 1 ? '1px solid #222' : 'none',
          }}>
            <span style={{ color: '#666' }}>f{overlay.start_frame}-{overlay.end_frame}</span>
            {' '}
            <span style={{ color: '#fff' }}>"{overlay.content}"</span>
            {' '}
            <span style={{ color: '#555' }}>({overlay.animation})</span>
          </div>
        ))}
      </div>
    </div>
  );
}
