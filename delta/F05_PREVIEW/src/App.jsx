import React, { useState, useRef } from 'react';

/* Helpers couleur */
const hexToRgba = (hex, alpha = 1) => {
  if (!hex) return `rgba(0,0,0,${alpha})`;
  const h = hex.replace('#', '');
  if (h.length === 3) return hexToRgba('#' + h.split('').map(c => c + c).join(''), alpha);
  if (h.length !== 6) return `rgba(0,0,0,${alpha})`;
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
};

const normalizeColor = (color) => {
  if (!color) return '#000000';
  const m = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (m) {
    return '#' + [m[1], m[2], m[3]].map(v => (+v).toString(16).padStart(2, '0')).join('');
  }
  return color;
};

/**
 * App — F05 PREVIEW (DELTA MODE)
 * ==============================
 * Formulaire pour configurer le STYLE des vidéos.
 * 
 * Ce codex_STYLE.json sera utilisé pour TOUS les clips.
 * Les timings (text_overlays, zoom, SFX) viennent de timing.json
 * et sont générés automatiquement par merge_codex.py
 */

const DEFAULT_STYLE = {
  version: "2.0",
  emotion_mode: "WHOLESOME",
  narrative_arc: "setup → context → climax → emotional_peak → action → resolution",
  title: "",
  video: {
    fps: 30,
    width: 1080,
    height: 1920
  },
  text_defaults: {
    font: "Anton, Arial Black, sans-serif",
    size: 96,
    color: "#FFFFFF",
    color_strong: "#FFFFFF",
    stroke_color: "#000000",
    stroke_width: 4,
    shadow: "2px 4px 8px rgba(0,0,0,0.9)",
    position: "bottom",
    letter_spacing: "0em",
    glow_intensity: 0,
    depth_3d: 0,
    animation: "word_by_word"
  },
  title_defaults: {
    font: "Anton, Arial Black, sans-serif",
    size: 96,
    color: "#FFFFFF",
    color_strong: "#FFFFFF",
    stroke_color: "#000000",
    stroke_width: 4,
    shadow: "2px 4px 8px rgba(0,0,0,0.9)",
    position: "center",
    letter_spacing: "0em",
    glow_intensity: 0,
    depth_3d: 0,
    animation: "fade_in",
    background: {
      enabled: false,
      color: "rgba(0,0,0,0.6)",
      radius: 16,
      thickness: 20
    }
  },
  zoom: {
    min_scale: 1.0,
    max_scale: 1.3,
    gap_sec: 3,
    on_strong_word: true
  },
  color_preset: "warm_vibrant",
  color_css_filter: "contrast(1.2) saturate(1.15) brightness(1.05) hue-rotate(3deg)",
  enhance_4k: true,
  sharpening: 80,
  vignette: 0.25,
  grain_intensity: 0.2,
  sfx_defaults: {
    types: ["keyboard", "whoosh", "pop", "ding"],
    volume: 0.3,
    on_strong_word: true
  }
};

const buildSegments = (timing) => {
  if (!timing) return [];
  if (Array.isArray(timing.segments)) return timing.segments;
  const words = Array.isArray(timing.words) ? timing.words : [];
  const segments = [];
  let current = null;
  const SENTENCE_MAX_WORDS = 8;
  for (const w of words) {
    const word = (w.word || '').trim();
    if (!word) continue;
    if (!current) {
      current = { start: w.start, end: w.end, text: word, is_strong: !!w.is_strong };
      continue;
    }
    current.text += ' ' + word;
    current.end = w.end;
    current.is_strong = current.is_strong || !!w.is_strong;
    const endsSentence = /[.!?…»]$/.test(word);
    const wordCount = current.text.split(' ').length;
    if (endsSentence || wordCount >= SENTENCE_MAX_WORDS) {
      segments.push(current);
      current = null;
    }
  }
  if (current) segments.push(current);
  return segments;
};

const getTitleFromTiming = (styleObj, timing) => {
  if (styleObj?.title && styleObj.title.trim()) return styleObj.title.trim();
  if (!timing) return null;
  if (timing.title) return timing.title;
  if (Array.isArray(timing.text_overlays)) {
    const t = timing.text_overlays.find(o => o.role === 'title');
    if (t) return t.content || t.text || null;
  }
  return null;
};
export default function App() {
  const [style, setStyle] = useState(DEFAULT_STYLE);
  const [activeTab, setActiveTab] = useState('preview');
  const [exported, setExported] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [timingJson, setTimingJson] = useState(null);
  const [previewStyle, setPreviewStyle] = useState('style');
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef(null);

  const handleVideoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoUrl(URL.createObjectURL(file));
    }
  };

  const handleTimingUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const json = JSON.parse(event.target.result);
          setTimingJson(json);
        } catch (err) {
          alert('Invalid JSON file');
        }
      };
      reader.readAsText(file);
    }
  };

  const exportMergedCodex = () => {
    const mergedCodex = {
      ...style,
      title: getTitleFromTiming(style, timingJson),
      text_overlays: timingJson?.text_overlays || [],
      zoom_keyframes: timingJson?.zoom_keyframes || [],
      sfx_keyframes: timingJson?.sfx_keyframes || [],
      _merged_from: {
        codex_STYLE_version: style.version,
        timing_file: timingJson?.filename || 'unknown'
      }
    };
    const blob = new Blob([JSON.stringify(mergedCodex, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'codex_final.json';
    a.click();
    URL.revokeObjectURL(url);
    setExported(true);
  };

  const updateField = (path, value) => {
    setStyle(prevStyle => {
      const newStyle = JSON.parse(JSON.stringify(prevStyle));
      const keys = path.split('.');
      let obj = newStyle;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return newStyle;
    });
    setExported(false);
  };

  const exportCodexStyle = () => {
    const blob = new Blob([JSON.stringify(style, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'codex_STYLE.json';
    a.click();
    URL.revokeObjectURL(url);
    setExported(true);
  };

  const presets = {
    WHOLESOME: {
      color_preset: "warm_vibrant",
      color_css_filter: "contrast(1.2) saturate(1.15) brightness(1.05) hue-rotate(3deg)",
      text_defaults: { color: "#FFB6C1", color_strong: "#FFD700", stroke_color: "#8B0000", stroke_width: 3 },
      title_defaults: { color: "#FFFFFF", color_strong: "#FFD700", stroke_color: "#8B0000", stroke_width: 3, background: { enabled: true, color: "rgba(0,0,0,0.6)", radius: 16, thickness: 20 } }
    },
    DRAMATIC: {
      color_preset: "cinematic",
      color_css_filter: "contrast(1.3) saturate(0.9) brightness(0.95)",
      text_defaults: { color: "#FFFFFF", color_strong: "#FFFFFF", stroke_color: "#000000", stroke_width: 4 },
      title_defaults: { color: "#FFFFFF", color_strong: "#FFFFFF", stroke_color: "#000000", stroke_width: 4, background: { enabled: true, color: "rgba(0,0,0,0.7)", radius: 12, thickness: 24 } }
    },
    COMEDY: {
      color_preset: "high_contrast",
      color_css_filter: "contrast(1.1) saturate(1.3) brightness(1.1)",
      text_defaults: { color: "#FFFF00", color_strong: "#FF4500", stroke_color: "#FF4500", stroke_width: 3 },
      title_defaults: { color: "#FFFF00", color_strong: "#FF4500", stroke_color: "#FF4500", stroke_width: 3, background: { enabled: false, color: "rgba(0,0,0,0.5)", radius: 12, thickness: 20 } }
    },
    ACTION: {
      color_preset: "high_contrast",
      color_css_filter: "contrast(1.4) saturate(1.2) brightness(1.0)",
      text_defaults: { color: "#FF4500", color_strong: "#FFFF00", stroke_color: "#000000", stroke_width: 4 },
      title_defaults: { color: "#FF4500", color_strong: "#FFFF00", stroke_color: "#000000", stroke_width: 4, background: { enabled: true, color: "rgba(20,20,20,0.75)", radius: 8, thickness: 28 } }
    },
    MYSTERIOUS: {
      color_preset: "cool_moody",
      color_css_filter: "contrast(1.2) saturate(0.8) brightness(0.9) hue-rotate(10deg)",
      text_defaults: { color: "#9370DB", color_strong: "#DDA0DD", stroke_color: "#4B0082", stroke_width: 3 },
      title_defaults: { color: "#9370DB", color_strong: "#DDA0DD", stroke_color: "#4B0082", stroke_width: 3, background: { enabled: true, color: "rgba(10,5,30,0.7)", radius: 20, thickness: 22 } }
    },
    MOTIVATION: {
      color_preset: "high_energy",
      color_css_filter: "contrast(1.35) saturate(1.4) brightness(1.1) hue-rotate(-5deg)",
      text_defaults: { color: "#FFD700", color_strong: "#FFFFFF", stroke_color: "#000000", stroke_width: 5 },
      title_defaults: { color: "#FFD700", color_strong: "#FFFFFF", stroke_color: "#000000", stroke_width: 5, background: { enabled: true, color: "rgba(0,0,0,0.65)", radius: 14, thickness: 26 } }
    },
    GRIS: {
      color_preset: "argent",
      color_css_filter: "contrast(1.3) saturate(0.15) brightness(0.85) grayscale(0.8)",
      text_defaults: { color: "#C0C0C0", color_strong: "#E0E0E0", stroke_color: "#000000", stroke_width: 4 },
      title_defaults: { color: "#C0C0C0", color_strong: "#E0E0E0", stroke_color: "#000000", stroke_width: 4, background: { enabled: true, color: "rgba(30,30,30,0.7)", radius: 10, thickness: 24 } }
    }
  };

  return (
    <div style={styles.app}>
      {/* Header */}
      <div style={styles.header}>
        <div style={{ fontSize: '20px', fontWeight: 900, letterSpacing: '0.05em' }}>
          OMNIS-WATCH — DELTA PREVIEW
        </div>
        <div style={{ fontSize: '13px', color: '#888' }}>
          Configure le STYLE → 1 seul codex_STYLE.json pour tous les clips
        </div>
      </div>

      {/* Main layout */}
      <div style={styles.mainLayout}>
        {/* Panel gauche: résumé */}
        <div style={styles.panel}>
          <h3 style={{ margin: '0 0 16px 0', color: '#00ff88' }}>Résumé</h3>
          
          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Mode:</span>
            <span style={{ ...styles.summaryValue, color: '#ffcc00' }}>{style.emotion_mode}</span>
          </div>
          
          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Preset:</span>
            <span style={styles.summaryValue}>{style.color_preset}</span>
          </div>
          
          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>4K:</span>
            <span style={styles.summaryValue}>{style.enhance_4k ? 'ON' : 'OFF'}</span>
          </div>
          
          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Sharp:</span>
            <span style={styles.summaryValue}>{style.sharpening}%</span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Vignette:</span>
            <span style={styles.summaryValue}>{Math.round(style.vignette * 100)}%</span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Grain:</span>
            <span style={styles.summaryValue}>{Math.round(style.grain_intensity * 100)}%</span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Texte:</span>
            <span style={styles.summaryValue}>{style.text_defaults.size}px</span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Couleur:</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ 
                width: '16px', 
                height: '16px', 
                background: style.text_defaults.color, 
                borderRadius: '3px',
                border: '1px solid #333'
              }}></span>
            </span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Zoom:</span>
            <span style={styles.summaryValue}>x{style.zoom.max_scale}</span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Gap zoom:</span>
            <span style={styles.summaryValue}>{style.zoom.gap_sec || 3}s</span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Titre:</span>
            <span style={{ ...styles.summaryValue, color: getTitleFromTiming(style, timingJson) ? '#00ff88' : '#666' }}>
              {getTitleFromTiming(style, timingJson) ? '✓ présent' : 'absent'}
            </span>
          </div>

          <div style={styles.summaryItem}>
            <span style={styles.summaryLabel}>Fond titre:</span>
            <span style={{ ...styles.summaryValue, color: style.title_defaults.background?.enabled ? '#00ff88' : '#888' }}>
              {style.title_defaults.background?.enabled ? 'ON' : 'OFF'}
            </span>
          </div>
        </div>

        {/* Panel droit: configuration */}
        <div style={{ ...styles.panel, flex: 2 }}>
          {/* Tabs */}
          <div style={styles.tabs}>
            <button style={activeTab === 'preview' ? styles.tabActive : styles.tab} onClick={() => setActiveTab('preview')}>Preview</button>
            <button style={activeTab === 'style' ? styles.tabActive : styles.tab} onClick={() => setActiveTab('style')}>Style</button>
            <button style={activeTab === 'text' ? styles.tabActive : styles.tab} onClick={() => setActiveTab('text')}>Texte</button>
            <button style={activeTab === 'title' ? styles.tabActive : styles.tab} onClick={() => setActiveTab('title')}>Titre</button>
            <button style={activeTab === 'video' ? styles.tabActive : styles.tab} onClick={() => setActiveTab('video')}>Video</button>
            <button style={activeTab === 'zoom' ? styles.tabActive : styles.tab} onClick={() => setActiveTab('zoom')}>Zoom</button>
          </div>

          {/* Preview tab */}
          {activeTab === 'preview' && (
            <div style={styles.tabContent}>
              {/* Upload section */}
              <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
                <div style={{ flex: 1 }}>
                  <label style={styles.label}>Video (MP4)</label>
                  <input 
                    type="file" 
                    accept="video/*" 
                    onChange={handleVideoUpload}
                  />
                  {videoUrl && <span style={{ color: '#00ff88', fontSize: '12px' }}>✓ Video chargée</span>}
                </div>
                <div style={{ flex: 1 }}>
                  <label style={styles.label}>Timing JSON (de D04)</label>
                  <input 
                    type="file" 
                    accept=".json" 
                    onChange={handleTimingUpload}
                  />
                  {timingJson && <span style={{ color: '#00ff88', fontSize: '12px' }}>✓ Timing chargé</span>}
                </div>
              </div>

              {/* Video preview */}
              {videoUrl && (
                <div style={styles.videoContainer}>
                  <div style={styles.videoWrapper}>
                    <video
                      ref={videoRef}
                      src={videoUrl}
                      controls
                      autoPlay
                      loop
                      onTimeUpdate={() => setCurrentTime(videoRef.current?.currentTime || 0)}
                      style={{
                        width: '100%',
                        maxHeight: '300px',
                        borderRadius: '8px',
                        filter: style.color_css_filter + 
                          (style.enhance_4k ? ' contrast(1.15) saturate(1.2) brightness(1.08)' : ''),
                        transform: `scale(${style.zoom.min_scale})`,
                        transition: 'filter 0.3s, transform 0.3s'
                      }}
                    />
                    {/* Vignette overlay */}
                    <div style={{
                      position: 'absolute',
                      top: 0, left: 0, right: 0, bottom: 0,
                      borderRadius: '8px',
                      boxShadow: `inset 0 0 ${style.vignette * 200}px rgba(0,0,0,${style.vignette})`,
                      pointerEvents: 'none'
                    }} />
                    {/* Full sentence subtitles with typewriter effect */}
                    {(() => {
                      const currentSegment = buildSegments(timingJson).find(s => 
                        currentTime >= s.start && currentTime <= s.end
                      );
                      if (!currentSegment) return null;
                      
                      const segmentDuration = currentSegment.end - currentSegment.start;
                      const segmentProgress = Math.min(1, Math.max(0, (currentTime - currentSegment.start) / segmentDuration));
                      
                      const fullText = currentSegment.text;
                      const totalChars = fullText.length;
                      
                      // Speed factor based on animation setting
                      const speedMap = { fast: 2.0, normal: 1.2, slow: 0.6 };
                      const speedFactor = speedMap[style.text_defaults.animation] || 1.2;
                      
                      const charsToShow = Math.floor(segmentProgress * totalChars * speedFactor);
                      const visibleText = fullText.substring(0, Math.min(charsToShow, totalChars));
                      
                      // Couleur: mot fort → color_strong, sinon couleur texte
                      const textColor = currentSegment.is_strong 
                        ? (style.text_defaults.color_strong || style.text_defaults.color)
                        : style.text_defaults.color;
                      
                      // Glow
                      const glowPx = style.text_defaults.glow_intensity * 4;
                      const glowShadow = glowPx > 0 
                        ? `0 0 ${glowPx}px ${textColor}, 0 0 ${glowPx * 2}px ${textColor}`
                        : '';
                      
                      // Position
                      const pos = style.text_defaults.position;
                      const posStyle = {
                        top: pos === 'top' ? '15%' : (pos === 'center' ? '45%' : 'auto'),
                        bottom: pos === 'bottom' ? '15%' : 'auto',
                      };
                      
                      return (
                        <div
                          style={{
                            position: 'absolute',
                            ...posStyle,
                            left: '50%',
                            transform: 'translateX(-50%)',
                            color: textColor,
                            fontSize: `${style.text_defaults.size * 0.35}px`,
                            fontFamily: style.text_defaults.font,
                            fontWeight: 'bold',
                            textShadow: glowShadow
                              ? `${style.text_defaults.stroke_width}px ${style.text_defaults.stroke_width}px 0 ${style.text_defaults.stroke_color}, -${style.text_defaults.stroke_width}px -${style.text_defaults.stroke_width}px 0 ${style.text_defaults.stroke_color}, ${glowShadow}`
                              : `${style.text_defaults.stroke_width}px ${style.text_defaults.stroke_width}px 0 ${style.text_defaults.stroke_color}, -${style.text_defaults.stroke_width}px -${style.text_defaults.stroke_width}px 0 ${style.text_defaults.stroke_color}`,
                            textAlign: 'center',
                            whiteSpace: 'normal',
                            maxWidth: '90%',
                            pointerEvents: 'none',
                            letterSpacing: style.text_defaults.letter_spacing,
                            zIndex: 10,
                            opacity: segmentProgress > 0.1 ? 1 : segmentProgress * 10
                          }}
                        >
                          {visibleText}
                          {charsToShow < totalChars && <span style={{ opacity: 0.7 }}>|</span>}
                        </div>
                      );
                    })()}
                    {/* Titre (bande fond) — actif seulement si le JSON contient un titre */}
                    {(() => {
                      const titleText = getTitleFromTiming(style, timingJson);
                      if (!titleText) return null;
                      
                      const t = style.title_defaults;
                      const bg = t.background || {};
                      const bgEnabled = bg.enabled === true;
                      
                      // Fond actif → glow et autres effets annulés (simple bande)
                      const glowPx = bgEnabled ? 0 : (t.glow_intensity || 0) * 4;
                      const glowShadow = glowPx > 0
                        ? `0 0 ${glowPx}px ${t.color}, 0 0 ${glowPx * 2}px ${t.color}`
                        : '';
                      
                      const pos = t.position;
                      const posStyle = {
                        top: pos === 'top' ? '8%' : (pos === 'center' ? '40%' : 'auto'),
                        bottom: pos === 'bottom' ? '8%' : 'auto',
                      };
                      
                      const bandStyle = bgEnabled ? {
                        backgroundColor: bg.color || 'rgba(0,0,0,0.6)',
                        borderRadius: `${bg.radius || 0}px`,
                        padding: `${bg.thickness || 0}px 28px`,
                      } : null;
                      
                      return (
                        <div
                          style={{
                            position: 'absolute',
                            ...posStyle,
                            left: '50%',
                            transform: 'translateX(-50%)',
                            ...bandStyle,
                            color: t.color,
                            fontSize: `${t.size * 0.35}px`,
                            fontFamily: t.font,
                            fontWeight: 'bold',
                            textShadow: glowShadow
                              ? `${t.stroke_width}px ${t.stroke_width}px 0 ${t.stroke_color}, -${t.stroke_width}px -${t.stroke_width}px 0 ${t.stroke_color}, ${glowShadow}`
                              : `${t.stroke_width}px ${t.stroke_width}px 0 ${t.stroke_color}, -${t.stroke_width}px -${t.stroke_width}px 0 ${t.stroke_color}`,
                            textAlign: 'center',
                            whiteSpace: 'normal',
                            maxWidth: '90%',
                            pointerEvents: 'none',
                            letterSpacing: t.letter_spacing,
                            zIndex: 11,
                          }}
                        >
                          {titleText}
                        </div>
                      );
                    })()}
                  </div>
                  <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
                    Filtre: {style.color_css_filter}
                  </div>
                </div>
              )}
              
              {!videoUrl && (
                <div style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#666',
                  border: '2px dashed #333',
                  borderRadius: '8px',
                  marginBottom: '20px'
                }}>
                  Uploade une video MP4 pour tester le style
                </div>
              )}

              {/* Timing info */}
              {timingJson && (
                <div style={{ ...styles.infoBox, marginBottom: '20px' }}>
                  <strong style={{ color: '#00ff88' }}>Timing chargé:</strong><br/>
                  {buildSegments(timingJson).length} segments de sous-titres<br/>
                  {timingJson.words?.length || 0} mots<br/>
                  {timingJson.word_count || 0} mots (compteur D04)
                </div>
              )}

              {/* Export merged codex */}
              <button 
                style={exported ? styles.exportedBtn : styles.exportBtn}
                onClick={exportMergedCodex}
                disabled={!timingJson}
              >
                {exported ? '✓ codex_final.json téléchargé!' : 'Exporter codex_final.json'}
              </button>
              {!timingJson && (
                <div style={{ fontSize: '11px', color: '#666', marginTop: '8px' }}>
                  (Uploade le timing JSON pour activer l'export)
                </div>
              )}
            </div>
          )}

          {/* Style tab */}
          {activeTab === 'style' && (
            <div style={styles.tabContent}>
              <label style={styles.label}>Mode emotionnel</label>
              <select style={styles.select} value={style.emotion_mode} onChange={(e) => {
                updateField('emotion_mode', e.target.value);
                if (presets[e.target.value]) {
                  Object.entries(presets[e.target.value]).forEach(([k, v]) => updateField(k, v));
                }
              }}>
                <option value="WHOLESOME">Wholesome</option>
                <option value="DRAMATIC">Dramatique</option>
                <option value="COMEDY">Comedie</option>
                <option value="ACTION">Action</option>
                <option value="MYSTERIOUS">Mysterieux</option>
                <option value="MOTIVATION">Motivation</option>
                <option value="GRIS">Gris / Argent</option>
              </select>

              <label style={styles.label}>Preset couleur</label>
              <select style={styles.select} value={style.color_preset} onChange={(e) => {
                const val = e.target.value;
                updateField('color_preset', val);
                // Apply specific filter for argent (black + silver, no blue)
                if (val === 'argent') {
                  updateField('color_css_filter', 'contrast(1.3) saturate(0.15) brightness(0.85) grayscale(0.8)');
                }
              }}>
                <option value="warm_vibrant">Warm Vibrant</option>
                <option value="cool_moody">Cool Moody</option>
                <option value="cinematic">Cinematic</option>
                <option value="high_contrast">High Contrast</option>
                <option value="argent">Argent Scintillant</option>
                <option value="none">None</option>
              </select>

              <label style={styles.label}>Filter CSS</label>
              <div style={styles.codeBlock}>{style.color_css_filter}</div>

              <label style={styles.label}>Vignette: {Math.round(style.vignette * 100)}%</label>
              <input style={styles.slider} type="range" min="0" max="100" value={Math.round(style.vignette * 100)} onChange={(e) => updateField('vignette', parseInt(e.target.value) / 100)} />

              <label style={styles.label}>Grain: {Math.round(style.grain_intensity * 100)}%</label>
              <input style={styles.slider} type="range" min="0" max="100" value={Math.round(style.grain_intensity * 100)} onChange={(e) => updateField('grain_intensity', parseInt(e.target.value) / 100)} />
            </div>
          )}

          {/* Text tab */}
          {activeTab === 'text' && (
            <div style={styles.tabContent}>
              <label style={styles.label}>Police</label>
              <select style={styles.select} value={style.text_defaults.font} onChange={(e) => updateField('text_defaults.font', e.target.value)}>
                <option value="Anton, Arial Black, sans-serif">Anton</option>
                <option value="Impact, Arial Black, sans-serif">Impact</option>
                <option value="Bebas Neue, Impact, sans-serif">Bebas Neue</option>
                <option value="Arial Black, Arial, sans-serif">Arial Black</option>
                <option value="Helvetica Neue, Helvetica, Arial, sans-serif">Helvetica</option>
              </select>

              <label style={styles.label}>Taille: {style.text_defaults.size}px</label>
              <input 
                style={styles.slider} 
                type="range" 
                min="20" 
                max="200" 
                step="1"
                value={style.text_defaults.size || 96} 
                onChange={(e) => updateField('text_defaults.size', Number(e.target.value))} 
              />

              <label style={styles.label}>Couleur texte</label>
              <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={style.text_defaults.color} onChange={(e) => updateField('text_defaults.color', e.target.value)} />

              <label style={styles.label}>
                <input type="checkbox" checked={!!style.text_defaults.color_strong && style.text_defaults.color_strong !== style.text_defaults.color} onChange={(e) => {
                  if (e.target.checked) {
                    updateField('text_defaults.color_strong', style.text_defaults.color_strong || style.text_defaults.color);
                  } else {
                    updateField('text_defaults.color_strong', style.text_defaults.color);
                  }
                }} style={{ marginRight: '8px' }} />
                Mot fort : couleur différente
              </label>
              {!!style.text_defaults.color_strong && style.text_defaults.color_strong !== style.text_defaults.color && (
                <>
                  <label style={styles.label}>Couleur mot fort</label>
                  <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={style.text_defaults.color_strong} onChange={(e) => updateField('text_defaults.color_strong', e.target.value)} />
                </>
              )}

              <label style={styles.label}>Couleur contour</label>
              <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={style.text_defaults.stroke_color} onChange={(e) => updateField('text_defaults.stroke_color', e.target.value)} />

              <label style={styles.label}>Epaisseur contour: {style.text_defaults.stroke_width}px</label>
              <input style={styles.slider} type="range" min="0" max="10" value={style.text_defaults.stroke_width} onChange={(e) => updateField('text_defaults.stroke_width', parseInt(e.target.value))} />

              <label style={styles.label}>Position</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[['top', 'TOP'], ['center', 'CENTER'], ['bottom', 'BOTTOM']].map(([pos, label]) => (
                  <button key={pos} style={style.text_defaults.position === pos ? styles.posBtnActive : styles.posBtn} onClick={() => updateField('text_defaults.position', pos)}>{label}</button>
                ))}
              </div>

              <label style={styles.label}>Glow: {style.text_defaults.glow_intensity}</label>
              <input 
                style={styles.slider} 
                type="range" 
                min="0" 
                max="100" 
                step="1"
                value={style.text_defaults.glow_intensity || 0} 
                onChange={(e) => updateField('text_defaults.glow_intensity', Number(e.target.value))} 
              />

              <label style={styles.label}>Vitesse typewriter</label>
              <select 
                style={styles.select} 
                value={style.text_defaults.animation || 'normal'} 
                onChange={(e) => updateField('text_defaults.animation', e.target.value)}
              >
                <option value="fast">Rapide</option>
                <option value="normal">Normal</option>
                <option value="slow">Lent</option>
              </select>
            </div>
          )}

          {/* Title tab */}
          {activeTab === 'title' && (
            <div style={styles.tabContent}>
              <label style={styles.label}>Texte du titre (vide = pas de titre)</label>
              <input 
                type="text" 
                style={{ ...styles.select, width: '100%' }}
                placeholder="Ex: IL N'EST PAS SEUL"
                value={style.title || ''}
                onChange={(e) => updateField('title', e.target.value)}
              />

              <div style={{ ...styles.infoBox, background: '#1a2a1a', border: '1px solid #2a4a2a' }}>
                <strong style={{ color: '#00ff88' }}>Le titre n'agit que si le JSON contient un titre</strong><br />
                (champ <code>title</code> ou overlay <code>role: "title"</code>).<br />
                S'il y a un fond, le glow et les autres effets sont annulés — simple bande derrière le titre.
              </div>

              <label style={styles.label}>Police</label>
              <select style={styles.select} value={style.title_defaults.font} onChange={(e) => updateField('title_defaults.font', e.target.value)}>
                <option value="Anton, Arial Black, sans-serif">Anton</option>
                <option value="Impact, Arial Black, sans-serif">Impact</option>
                <option value="Bebas Neue, Impact, sans-serif">Bebas Neue</option>
                <option value="Arial Black, Arial, sans-serif">Arial Black</option>
                <option value="Helvetica Neue, Helvetica, Arial, sans-serif">Helvetica</option>
              </select>

              <label style={styles.label}>Taille: {style.title_defaults.size}px</label>
              <input 
                style={styles.slider} 
                type="range" 
                min="20" 
                max="200" 
                step="1"
                value={style.title_defaults.size || 96} 
                onChange={(e) => updateField('title_defaults.size', Number(e.target.value))} 
              />

              <label style={styles.label}>Couleur texte</label>
              <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={style.title_defaults.color} onChange={(e) => updateField('title_defaults.color', e.target.value)} />

              <label style={styles.label}>
                <input type="checkbox" checked={!!style.title_defaults.color_strong && style.title_defaults.color_strong !== style.title_defaults.color} onChange={(e) => {
                  if (e.target.checked) {
                    updateField('title_defaults.color_strong', style.title_defaults.color_strong || style.title_defaults.color);
                  } else {
                    updateField('title_defaults.color_strong', style.title_defaults.color);
                  }
                }} style={{ marginRight: '8px' }} />
                Mot fort : couleur différente
              </label>
              {!!style.title_defaults.color_strong && style.title_defaults.color_strong !== style.title_defaults.color && (
                <>
                  <label style={styles.label}>Couleur mot fort</label>
                  <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={style.title_defaults.color_strong} onChange={(e) => updateField('title_defaults.color_strong', e.target.value)} />
                </>
              )}

              <label style={styles.label}>Couleur contour</label>
              <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={style.title_defaults.stroke_color} onChange={(e) => updateField('title_defaults.stroke_color', e.target.value)} />

              <label style={styles.label}>Epaisseur contour: {style.title_defaults.stroke_width}px</label>
              <input style={styles.slider} type="range" min="0" max="10" value={style.title_defaults.stroke_width} onChange={(e) => updateField('title_defaults.stroke_width', parseInt(e.target.value))} />

              <label style={styles.label}>Position</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[['top', 'TOP'], ['center', 'CENTER'], ['bottom', 'BOTTOM']].map(([pos, label]) => (
                  <button key={pos} style={style.title_defaults.position === pos ? styles.posBtnActive : styles.posBtn} onClick={() => updateField('title_defaults.position', pos)}>{label}</button>
                ))}
              </div>

              <label style={styles.label}>Glow: {style.title_defaults.glow_intensity}</label>
              <input 
                style={styles.slider} 
                type="range" 
                min="0" 
                max="100" 
                step="1"
                value={style.title_defaults.glow_intensity || 0} 
                onChange={(e) => updateField('title_defaults.glow_intensity', Number(e.target.value))} 
              />

              <label style={styles.label}>Animation</label>
              <select 
                style={styles.select} 
                value={style.title_defaults.animation || 'fade_in'} 
                onChange={(e) => updateField('title_defaults.animation', e.target.value)}
              >
                <option value="word_by_word">Mot par mot</option>
                <option value="fade_in">Fade in</option>
                <option value="fade_in_slow">Fade in lent</option>
                <option value="pop">Pop</option>
              </select>

              <div style={{ marginTop: '8px', padding: '12px', background: '#1a1a1a', borderRadius: '8px', border: '1px solid #333' }}>
                <strong style={{ color: '#00ff88', fontSize: '13px' }}>FOND (bande derrière le titre)</strong>

                <label style={{ ...styles.label, marginTop: '8px', display: 'block' }}>
                  <input type="checkbox" checked={!!style.title_defaults.background?.enabled} onChange={(e) => updateField('title_defaults.background.enabled', e.target.checked)} style={{ marginRight: '8px' }} />
                  Activer le fond
                </label>

                {style.title_defaults.background?.enabled && (
                  <>
                    <label style={styles.label}>Couleur du fond</label>
                    <input style={{ ...styles.colorPicker, width: '100%', height: '40px' }} type="color" value={normalizeColor(style.title_defaults.background.color)} onChange={(e) => updateField('title_defaults.background.color', hexToRgba(e.target.value, 0.6))} />

                    <label style={styles.label}>Arrondi des angles: {style.title_defaults.background.radius}px</label>
                    <input style={styles.slider} type="range" min="0" max="60" step="1" value={style.title_defaults.background.radius ?? 0} onChange={(e) => updateField('title_defaults.background.radius', parseInt(e.target.value))} />

                    <label style={styles.label}>Épaisseur (hauteur bande): {style.title_defaults.background.thickness}px</label>
                    <input style={styles.slider} type="range" min="0" max="60" step="1" value={style.title_defaults.background.thickness ?? 0} onChange={(e) => updateField('title_defaults.background.thickness', parseInt(e.target.value))} />

                    <div style={{ fontSize: '11px', color: '#ffcc00', marginTop: '4px' }}>
                      Fond actif → glow, depth_3d et ombre annulés (simple bande).
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Video tab */}
          {activeTab === 'video' && (
            <div style={styles.tabContent}>
              <label style={styles.label}>
                <input type="checkbox" checked={style.enhance_4k} onChange={(e) => updateField('enhance_4k', e.target.checked)} style={{ marginRight: '8px' }} />
                Enhance 4K
              </label>

              <label style={styles.label}>Sharpening: {style.sharpening}%</label>
              <input style={styles.slider} type="range" min="0" max="100" value={style.sharpening} onChange={(e) => updateField('sharpening', parseInt(e.target.value))} />

              <div style={styles.infoBox}>
                <strong style={{ color: '#00ff88' }}>Filtres recommandes:</strong><br />
                <code>unsharp=5:5:1.5</code> (nettete)<br />
                <code>hqdn3d=1.5:1.5:6</code> (debruitage)
              </div>
            </div>
          )}

          {/* Zoom tab */}
          {activeTab === 'zoom' && (
            <div style={styles.tabContent}>
              <label style={styles.label}>
                <input type="checkbox" checked={style.zoom.on_strong_word} onChange={(e) => updateField('zoom.on_strong_word', e.target.checked)} style={{ marginRight: '8px' }} />
                Zoom sur mots forts
              </label>

              <label style={styles.label}>Zoom min: x{style.zoom.min_scale}</label>
              <input style={styles.slider} type="range" min="100" max="150" value={style.zoom.min_scale * 100} onChange={(e) => updateField('zoom.min_scale', parseInt(e.target.value) / 100)} />

              <label style={styles.label}>Zoom max: x{style.zoom.max_scale}</label>
              <input style={styles.slider} type="range" min="100" max="200" value={style.zoom.max_scale * 100} onChange={(e) => updateField('zoom.max_scale', parseInt(e.target.value) / 100)} />

              <label style={styles.label}>1 zoom toutes les: {style.zoom.gap_sec}s</label>
              <input style={styles.slider} type="range" min="1" max="6" step="1" value={style.zoom.gap_sec || 3} onChange={(e) => updateField('zoom.gap_sec', parseInt(e.target.value))} />

              <div style={styles.infoBox}>
                <strong style={{ color: '#ffcc00' }}>Le zoom sera applique:</strong><br />
                - Sur mots <code>is_strong: true</code> dans timing.json<br />
                - Max 1 zoom toutes les {style.zoom.gap_sec || 3}s (le mot fort le plus porteur)<br />
                - Animation progressive
              </div>
            </div>
          )}

          {/* Export */}
          <div style={{ marginTop: '20px', padding: '16px', background: '#1a1a1a', borderRadius: '8px' }}>
            <button style={exported ? styles.exportedBtn : styles.exportBtn} onClick={exportCodexStyle}>
              {exported ? 'codex_STYLE.json telecharge!' : 'Telecharger codex_STYLE.json'}
            </button>
            <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
              Ce fichier = STYLE pour TOUS les clips de la session
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Styles */
const styles = {
  app: { background: '#0a0a0a', color: '#e0e0e0', fontFamily: 'system-ui, sans-serif', minHeight: '100vh' },
  header: { padding: '16px 24px', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  mainLayout: { display: 'flex', gap: '20px', padding: '20px' },
  panel: { width: '280px', background: '#141414', borderRadius: '12px', border: '1px solid #222', padding: '16px' },
  summaryItem: { display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #222', fontSize: '13px' },
  summaryLabel: { color: '#888' },
  summaryValue: { color: '#fff' },
  tabs: { display: 'flex', gap: '4px', marginBottom: '16px' },
  tab: { flex: 1, padding: '10px', background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', color: '#888', cursor: 'pointer', fontSize: '13px', fontWeight: 600 },
  tabActive: { flex: 1, padding: '10px', background: '#2a2a2a', border: '1px solid #00ff88', borderRadius: '8px', color: '#00ff88', cursor: 'pointer', fontSize: '13px', fontWeight: 600 },
  tabContent: { display: 'flex', flexDirection: 'column', gap: '10px' },
  label: { fontSize: '13px', color: '#aaa', fontWeight: 600 },
  select: { padding: '10px', background: '#1a1a1a', border: '1px solid #333', borderRadius: '6px', color: '#e0e0e0', fontSize: '14px', cursor: 'pointer' },
  slider: { width: '100%', accentColor: '#00ff88', cursor: 'pointer' },
  colorPicker: { border: '1px solid #333', borderRadius: '6px', cursor: 'pointer', background: '#1a1a1a' },
  posBtn: { flex: 1, padding: '8px', background: '#1a1a1a', border: '1px solid #333', borderRadius: '6px', color: '#888', cursor: 'pointer', fontSize: '12px' },
  posBtnActive: { flex: 1, padding: '8px', background: '#2a2a2a', border: '1px solid #00ff88', borderRadius: '6px', color: '#00ff88', cursor: 'pointer', fontSize: '12px' },
  codeBlock: { padding: '8px', background: '#1a1a1a', borderRadius: '6px', fontSize: '11px', color: '#666', fontFamily: 'monospace' },
  infoBox: { padding: '12px', background: '#1a1a1a', borderRadius: '8px', fontSize: '12px', color: '#888' },
  exportBtn: { width: '100%', padding: '12px', background: '#1a2a1a', border: '1px solid #2a4a2a', borderRadius: '8px', color: '#88ff88', cursor: 'pointer', fontSize: '14px', fontWeight: 700 },
  exportedBtn: { width: '100%', padding: '12px', background: '#2a4a2a', border: '1px solid #4a8a4a', borderRadius: '8px', color: '#aaffaa', cursor: 'pointer', fontSize: '14px', fontWeight: 700 },
  videoContainer: { marginTop: '20px', overflow: 'hidden', borderRadius: '8px' },
  videoWrapper: { position: 'relative', display: 'inline-block', width: '100%', overflow: 'hidden' }
};
