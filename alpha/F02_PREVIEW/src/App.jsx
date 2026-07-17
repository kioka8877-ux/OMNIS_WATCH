import React, { useState, useEffect, useRef } from 'react';
import { Player } from '@remotion/player';
import { OmniComposition } from './preview/OmniComposition';

/**
 * App — F02 PREVIEW
 *
 * Charge le codex.json et la vidéo depuis public/,
 * rend la composition en temps réel via @remotion/player.
 *
 * L'opérateur peut :
 *  - Cliquer Play pour voir le résultat exact
 *  - Modifier les textes, couleurs, glow, positions, animations
 *  - Modifier les effets (color grading, vignette, grain, zoom)
 *  - Exporter le codex modifié
 *  - Valider (Gate 2)
 */

export default function App() {
  const [codex, setCodex] = useState(null);
  const [videoSrc, setVideoSrc] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [validated, setValidated] = useState(false);
  const [activeTab, setActiveTab] = useState('text');
  const [selectedText, setSelectedText] = useState(0);
  const playerRef = useRef(null);

  // Charger le codex.json et la vidéo au montage
  useEffect(() => {
    async function loadAssets() {
      try {
        const codexResp = await fetch('./codex.json');
        if (!codexResp.ok) {
          throw new Error('codex.json non trouvé dans public/');
        }
        const codexData = await codexResp.json();
        setCodex(codexData);
        setVideoSrc('./video_coupee.mp4');
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }
    loadAssets();
  }, []);

  // Écran de chargement
  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳ Chargement...</div>
        <div style={{ fontSize: '14px', color: '#666' }}>Lecture du codex.json et de la vidéo</div>
      </div>
    );
  }

  // Écran d'erreur
  if (error) {
    return (
      <div style={styles.loading}>
        <div style={{ fontSize: '24px', color: '#ff4444', marginBottom: '10px' }}>❌ Erreur</div>
        <div style={{ fontSize: '14px', color: '#888' }}>{error}</div>
        <div style={{ marginTop: '20px', fontSize: '13px', color: '#666', textAlign: 'left' }}>
          <strong>Setup requis:</strong>
          <br />
          1. Placez <code>codex.json</code> dans <code>public/</code>
          <br />
          2. Placez <code>video_coupee.mp4</code> dans <code>public/</code>
          <br />
          3. Lancez <code>npm run build</code>
        </div>
      </div>
    );
  }

  // Données du codex
  const fps = codex.video?.fps || 30;
  const totalFrames = codex.video?.total_frames || 300;
  const vidWidth = codex.video?.width || 1080;
  const vidHeight = codex.video?.height || 1920;
  const emotionMode = codex.emotion_mode || 'UNKNOWN';
  const textCount = codex.text_overlays?.length || 0;
  const zoomCount = codex.zoom_keyframes?.length || 0;
  const sfxCount = codex.sfx_timeline?.length || 0;

  // Helpers pour modifier le codex
  const updateTextOverlay = (index, key, value) => {
    const newCodex = { ...codex };
    newCodex.text_overlays = [...(newCodex.text_overlays || [])];
    newCodex.text_overlays[index] = { ...newCodex.text_overlays[index], [key]: value };
    setCodex(newCodex);
  };

  const updateCodexField = (key, value) => {
    setCodex({ ...codex, [key]: value });
  };

  const applyToAll = (key, value) => {
    const newCodex = { ...codex };
    newCodex.text_overlays = (newCodex.text_overlays || []).map((o) => ({
      ...o,
      [key]: value,
    }));
    setCodex(newCodex);
  };

  const exportCodex = () => {
    const blob = new Blob([JSON.stringify(codex, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'codex.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const currentOverlay = codex.text_overlays?.[selectedText];

  return (
    <div style={styles.app}>
      {/* Header */}
      <div style={styles.header}>
        <div style={{ fontSize: '18px', fontWeight: 900, letterSpacing: '0.05em' }}>
          OMNIS-WATCH — F02 Preview
        </div>
        <div style={{ fontSize: '13px', color: '#888' }}>
          Mode: <span style={{ color: '#00ff88' }}>{emotionMode}</span>
          {'  |  '}
          📝 {textCount} textes
          {'  |  '}
          🔍 {zoomCount} zooms
          {'  |  '}
          🔊 {sfxCount} SFX
          {'  |  '}
          ⏱️ {(totalFrames / fps).toFixed(1)}s
        </div>
      </div>

      {/* Main layout: player + panels */}
      <div style={styles.mainLayout}>
        {/* Player (centered, compact) */}
        <div style={styles.playerContainer}>
          <Player
            ref={playerRef}
            component={OmniComposition}
            inputProps={{ codex, videoSrc }}
            durationInFrames={totalFrames}
            fps={fps}
            compositionWidth={vidWidth}
            compositionHeight={vidHeight}
            style={{
              width: '100%',
              maxWidth: '300px',
              aspectRatio: '9 / 16',
              borderRadius: '12px',
              overflow: 'hidden',
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            }}
            controls
            loop
          />
        </div>

        {/* Right panel */}
        <div style={styles.panel}>
          {/* Tabs */}
          <div style={styles.tabs}>
            <button
              style={activeTab === 'text' ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab('text')}
            >
              📝 Texte
            </button>
            <button
              style={activeTab === 'effects' ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab('effects')}
            >
              🎨 Effets
            </button>
            <button
              style={activeTab === 'sharp' ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab('sharp')}
            >
              🔍 Netteté
            </button>
          </div>

          {/* Text panel */}
          {activeTab === 'text' && currentOverlay && (
            <div style={styles.panelContent}>
              {/* Text selector */}
              <div style={styles.textSelector}>
                {(codex.text_overlays || []).map((o, i) => (
                  <button
                    key={i}
                    style={selectedText === i ? styles.textBtnActive : styles.textBtn}
                    onClick={() => setSelectedText(i)}
                  >
                    {i + 1}. {(o.content || '').substring(0, 20)}
                  </button>
                ))}
              </div>

              {/* Content */}
              <label style={styles.label}>Contenu</label>
              <input
                style={styles.input}
                type="text"
                value={currentOverlay.content || ''}
                onChange={(e) => updateTextOverlay(selectedText, 'content', e.target.value)}
              />

              {/* Animation */}
              <label style={styles.label}>Animation</label>
              <select
                style={styles.select}
                value={currentOverlay.animation || 'word_by_word'}
                onChange={(e) => updateTextOverlay(selectedText, 'animation', e.target.value)}
              >
                <option value="word_by_word">Mot par mot</option>
                <option value="pop">Pop</option>
                <option value="fade_in">Fade in</option>
                <option value="fade_in_slow">Fade in lent</option>
              </select>

              {/* Font */}
              <label style={styles.label}>Police</label>
              <select
                style={styles.select}
                value={currentOverlay.font || 'Impact, Arial Black, sans-serif'}
                onChange={(e) => {
                  updateTextOverlay(selectedText, 'font', e.target.value);
                }}
              >
                <option value="Impact, Arial Black, sans-serif">Impact</option>
                <option value="Arial Black, sans-serif">Arial Black</option>
                <option value="Bebas Neue, sans-serif">Bebas Neue</option>
                <option value="Helvetica, sans-serif">Helvetica</option>
              </select>

              {/* Size */}
              <label style={styles.label}>
                Taille: {currentOverlay.size || 96}px
              </label>
              <input
                style={styles.slider}
                type="range"
                min="40"
                max="150"
                value={currentOverlay.size || 96}
                onChange={(e) =>
                  updateTextOverlay(selectedText, 'size', parseInt(e.target.value))
                }
              />

              {/* Color */}
              <label style={styles.label}>Couleur</label>
              <input
                style={styles.colorPicker}
                type="color"
                value={currentOverlay.color || '#FFFFFF'}
                onChange={(e) => updateTextOverlay(selectedText, 'color', e.target.value)}
              />

              {/* Glow intensity */}
              <label style={styles.label}>
                Glow néon: {currentOverlay.glow_intensity || 0}%
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="100"
                value={currentOverlay.glow_intensity || 0}
                onChange={(e) =>
                  updateTextOverlay(selectedText, 'glow_intensity', parseInt(e.target.value))
                }
              />

              {/* Stroke width */}
              <label style={styles.label}>
                Contour: {currentOverlay.stroke_width || 0}px
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="8"
                value={currentOverlay.stroke_width || 0}
                onChange={(e) =>
                  updateTextOverlay(selectedText, 'stroke_width', parseInt(e.target.value))
                }
              />

              {/* Position */}
              <label style={styles.label}>Position</label>
              <select
                style={styles.select}
                value={currentOverlay.position || 'center'}
                onChange={(e) => updateTextOverlay(selectedText, 'position', e.target.value)}
              >
                <option value="center">Centre</option>
                <option value="center_bottom">Centre bas</option>
                <option value="top">Haut</option>
                <option value="center_left">Centre gauche</option>
                <option value="bottom">Bas</option>
              </select>

              {/* Timing */}
              <label style={styles.label}>
                Timing: {((currentOverlay.start_frame || 0) / fps).toFixed(1)}s -{' '}
                {((currentOverlay.end_frame || 0) / fps).toFixed(1)}s
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  style={{ ...styles.input, flex: 1 }}
                  type="number"
                  step="0.1"
                  value={((currentOverlay.start_frame || 0) / fps).toFixed(1)}
                  onChange={(e) =>
                    updateTextOverlay(
                      selectedText,
                      'start_frame',
                      Math.round(parseFloat(e.target.value) * fps)
                    )
                  }
                />
                <input
                  style={{ ...styles.input, flex: 1 }}
                  type="number"
                  step="0.1"
                  value={((currentOverlay.end_frame || 0) / fps).toFixed(1)}
                  onChange={(e) =>
                    updateTextOverlay(
                      selectedText,
                      'end_frame',
                      Math.round(parseFloat(e.target.value) * fps)
                    )
                  }
                />
              </div>

              {/* Apply to all */}
              <button
                style={styles.applyBtn}
                onClick={() => {
                  applyToAll('font', currentOverlay.font);
                  applyToAll('size', currentOverlay.size);
                  applyToAll('color', currentOverlay.color);
                  applyToAll('glow_intensity', currentOverlay.glow_intensity);
                  applyToAll('stroke_width', currentOverlay.stroke_width);
                  applyToAll('position', currentOverlay.position);
                }}
              >
                📋 Appliquer style à tous les textes
              </button>
            </div>
          )}

          {/* Effects panel */}
          {activeTab === 'effects' && (
            <div style={styles.panelContent}>              {/* Color preset */}
              <label style={styles.label}>Color preset</label>
              <select
                style={styles.select}
                value={codex.color_preset || 'warm_vibrant'}
                onChange={(e) => {
                  const preset = e.target.value;
                  const filters = {
                    warm_vibrant: 'contrast(1.2) saturate(1.15) brightness(1.05) hue-rotate(3deg)',
                    cold_desaturated: 'contrast(1.1) saturate(0.6) brightness(0.95) hue-rotate(-10deg)',
                    high_contrast: 'contrast(1.5) saturate(1.3) brightness(1.0)',
                    punchy: 'contrast(1.3) saturate(1.5) brightness(1.1)',
                    sepia_soft: 'sepia(0.3) contrast(1.1) saturate(0.9) brightness(1.05)',
                  };
                  updateCodexField('color_preset', preset);
                  updateCodexField('color_css_filter', filters[preset] || '');
                }}
              >
                <option value="warm_vibrant">Warm Vibrant</option>
                <option value="cold_desaturated">Cold Desaturated</option>
                <option value="high_contrast">High Contrast</option>
                <option value="punchy">Punchy</option>
                <option value="sepia_soft">Sepia Soft</option>
              </select>

              {/* Enhance 4K */}
              <label style={styles.label}>
                <input
                  type="checkbox"
                  checked={codex.enhance_4k || false}
                  onChange={(e) => updateCodexField('enhance_4k', e.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                Enhance 4K
              </label>

              {/* Vignette */}
              <label style={styles.label}>
                Vignette: {Math.round((codex.vignette || 0) * 100)}%
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="100"
                value={Math.round((codex.vignette || 0) * 100)}
                onChange={(e) => updateCodexField('vignette', parseInt(e.target.value) / 100)}
              />

              {/* Grain */}
              <label style={styles.label}>
                Grain: {Math.round((codex.grain_intensity || 0) * 100)}%
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="100"
                value={Math.round((codex.grain_intensity || 0) * 100)}
                onChange={(e) =>
                  updateCodexField('grain_intensity', parseInt(e.target.value) / 100)
                }
              />

              {/* Slow motion */}
              <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #333' }}>
                <label style={{ ...styles.label, color: '#00ff88', fontSize: '14px' }}>
                  ⏩ Slow Motion + Cut brutal
                </label>

                <label style={styles.label}>
                  Cut start: {((codex.slowmo_start_frame || 0) / fps).toFixed(1)}s
                </label>
                <input
                  style={styles.slider}
                  type="range"
                  min="0"
                  max={totalFrames}
                  step={fps}
                  value={codex.slowmo_start_frame || 0}
                  onChange={(e) => updateCodexField('slowmo_start_frame', parseInt(e.target.value))}
                />

                <label style={styles.label}>
                  Vitesse: {Math.round((codex.slowmo_speed || 1.0) * 100)}%
                </label>
                <input
                  style={styles.slider}
                  type="range"
                  min="10"
                  max="100"
                  value={Math.round((codex.slowmo_speed || 1.0) * 100)}
                  onChange={(e) => updateCodexField('slowmo_speed', parseInt(e.target.value) / 100)}
                />

                <label style={styles.label}>
                  Flash blanc: {codex.cut_flash_frames || 0} frames
                </label>
                <input
                  style={styles.slider}
                  type="range"
                  min="0"
                  max="10"
                  value={codex.cut_flash_frames || 0}
                  onChange={(e) => updateCodexField('cut_flash_frames', parseInt(e.target.value))}
                />
              </div>

              {/* Zoom intensity */}
              <label style={styles.label}>
                Zoom max:{' '}
                {codex.zoom_keyframes?.length > 0
                  ? codex.zoom_keyframes[codex.zoom_keyframes.length - 1].scale.toFixed(2) + 'x'
                  : '1.0x'}
              </label>
              <input
                style={styles.slider}
                type="range"
                min="100"
                max="200"
                value={
                  codex.zoom_keyframes?.length > 0
                    ? Math.round(codex.zoom_keyframes[codex.zoom_keyframes.length - 1].scale * 100)
                    : 100
                }
                onChange={(e) => {
                  const maxScale = parseInt(e.target.value) / 100;
                  const newCodex = { ...codex };
                  if (newCodex.zoom_keyframes?.length > 0) {
                    newCodex.zoom_keyframes = newCodex.zoom_keyframes.map((k, i) => ({
                      ...k,
                      scale: 1.0 + (maxScale - 1.0) * (i / (newCodex.zoom_keyframes.length - 1)),
                    }));
                  }
                  setCodex(newCodex);
                }}
              />
            </div>
          )}

          {/* Sharpness panel */}
          {activeTab === 'sharp' && (
            <div style={styles.panelContent}>
              <label style={styles.label}>
                Sharpening: {codex.sharpening || 0}%
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="100"
                value={codex.sharpening || 0}
                onChange={(e) => updateCodexField('sharpening', parseInt(e.target.value))}
              />

              <label style={styles.label}>
                Débruitage: {codex.denoising || 0}%
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="100"
                value={codex.denoising || 0}
                onChange={(e) => updateCodexField('denoising', parseInt(e.target.value))}
              />

              <label style={styles.label}>
                Grain: {Math.round((codex.grain_intensity || 0) * 100)}%
              </label>
              <input
                style={styles.slider}
                type="range"
                min="0"
                max="100"
                value={Math.round((codex.grain_intensity || 0) * 100)}
                onChange={(e) =>
                  updateCodexField('grain_intensity', parseInt(e.target.value) / 100)
                }
              />

              <label style={styles.label}>
                <input
                  type="checkbox"
                  checked={codex.enhance_4k || false}
                  onChange={(e) => updateCodexField('enhance_4k', e.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                Enhance 4K
              </label>

              <div style={{ marginTop: '12px', padding: '10px', background: '#1a1a1a', borderRadius: '8px', fontSize: '12px', color: '#888' }}>
                <strong style={{ color: '#00ff88' }}>Valeurs de référence (vidéo analysée) :</strong>
                <br />
                Sharpening: 75% | Débruitage: 15% | Grain: 15%
                <br />
                En production (F01) : unsharp=5:5:1.5 + hqdn3d=1.5:1.5:6
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div style={styles.actions}>
            <button style={styles.exportBtn} onClick={exportCodex}>
              ⬇ Télécharger codex.json
            </button>
            <button
              style={validated ? styles.validatedBtn : styles.validateBtn}
              onClick={() => setValidated(true)}
            >
              {validated ? '✓ Validé — Prêt pour le rendu' : '✓ Valider et rendre'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────
 * Styles
 * ────────────────────────────────────────────────────────────── */

const styles = {
  app: {
    background: '#0a0a0a',
    color: '#e0e0e0',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    background: '#0a0a0a',
    color: '#888',
    fontFamily: 'system-ui, sans-serif',
  },
  header: {
    padding: '12px 20px',
    borderBottom: '1px solid #222',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '8px',
  },
  mainLayout: {
    display: 'flex',
    flexDirection: 'row',
    flex: 1,
    gap: '20px',
    padding: '20px',
    alignItems: 'flex-start',
  },
  playerContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  panel: {
    width: '320px',
    minWidth: '280px',
    maxHeight: '85vh',
    overflowY: 'auto',
    background: '#141414',
    borderRadius: '12px',
    border: '1px solid #222',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  tabs: {
    display: 'flex',
    gap: '4px',
    marginBottom: '8px',
  },
  tab: {
    flex: 1,
    padding: '8px 12px',
    background: '#1a1a1a',
    border: '1px solid #222',
    borderRadius: '8px',
    color: '#888',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
  },
  tabActive: {
    flex: 1,
    padding: '8px 12px',
    background: '#2a2a2a',
    border: '1px solid #00ff88',
    borderRadius: '8px',
    color: '#00ff88',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
  },
  panelContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  textSelector: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    marginBottom: '8px',
  },
  textBtn: {
    padding: '4px 8px',
    background: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '6px',
    color: '#888',
    cursor: 'pointer',
    fontSize: '12px',
  },
  textBtnActive: {
    padding: '4px 8px',
    background: '#2a2a2a',
    border: '1px solid #00ff88',
    borderRadius: '6px',
    color: '#00ff88',
    cursor: 'pointer',
    fontSize: '12px',
  },
  label: {
    fontSize: '13px',
    color: '#aaa',
    fontWeight: 600,
    marginTop: '4px',
  },
  input: {
    padding: '8px 10px',
    background: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '6px',
    color: '#e0e0e0',
    fontSize: '14px',
    outline: 'none',
  },
  select: {
    padding: '8px 10px',
    background: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '6px',
    color: '#e0e0e0',
    fontSize: '14px',
    outline: 'none',
    cursor: 'pointer',
  },
  slider: {
    width: '100%',
    accentColor: '#00ff88',
    cursor: 'pointer',
  },
  colorPicker: {
    width: '100%',
    height: '36px',
    border: '1px solid #333',
    borderRadius: '6px',
    cursor: 'pointer',
    background: '#1a1a1a',
  },
  applyBtn: {
    marginTop: '8px',
    padding: '8px 12px',
    background: '#1a2a1a',
    border: '1px solid #2a4a2a',
    borderRadius: '6px',
    color: '#88ff88',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 600,
  },
  actions: {
    marginTop: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  exportBtn: {
    padding: '10px 16px',
    background: '#1a1a2a',
    border: '1px solid #2a2a4a',
    borderRadius: '8px',
    color: '#88aaff',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
  },
  validateBtn: {
    padding: '10px 16px',
    background: '#1a2a1a',
    border: '1px solid #2a4a2a',
    borderRadius: '8px',
    color: '#88ff88',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 700,
  },
  validatedBtn: {
    padding: '10px 16px',
    background: '#2a4a2a',
    border: '1px solid #4a8a4a',
    borderRadius: '8px',
    color: '#aaffaa',
    cursor: 'default',
    fontSize: '14px',
    fontWeight: 700,
  },
};
