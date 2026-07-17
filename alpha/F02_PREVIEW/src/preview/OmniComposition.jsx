import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  OffthreadVideo,
  Sequence,
} from 'remotion';

/* ──────────────────────────────────────────────────────────────
 * OmniComposition — Composition principale OMNIS-WATCH
 * Lit le codex.json et orchestre tous les layers.
 *
 * Props:
 *   codex: object — le codex.json généré par F02B
 *   videoSrc: string — chemin vers video_coupee.mp4
 * ────────────────────────────────────────────────────────────── */

export const OmniComposition = ({ codex, videoSrc }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  // Calculer le zoom actuel basé sur les keyframes
  const currentZoom = getCurrentZoom(frame, codex.zoom_keyframes || []);

  // CSS filter pour la colorimétrie
  const colorFilter = codex.color_css_filter || '';
  const enhanceFilter = codex.enhance_4k
    ? ' contrast(1.15) saturate(1.2) brightness(1.08)'
    : '';
  const fullFilter = (colorFilter + enhanceFilter).trim();

  // Vignette
  const vignetteOpacity = codex.vignette || 0;

  // Grain
  const grainIntensity = codex.grain_intensity || 0;

  return (
    <AbsoluteFill style={{ background: '#000', overflow: 'hidden' }}>
      {/* Layer 1: Vidéo source avec zoom + colorimétrie */}
      <AbsoluteFill
        style={{
          transform: `scale(${currentZoom.scale}) translate(${
            (0.5 - currentZoom.target_x) * -100
          }%, ${(0.5 - currentZoom.target_y) * -100}%)`,
          filter: fullFilter || undefined,
        }}
      >
        <OffthreadVideo src={videoSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </AbsoluteFill>

      {/* Layer 2: Vignette */}
      {vignetteOpacity > 0 && (
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,' +
              vignetteOpacity +
              ') 100%)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Layer 3: Grain cinématique (SVG feTurbulence — style CRUSADER) */}
      {grainIntensity > 0 && (
        <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'overlay' }}>
          <svg width="100%" height="100%" style={{ opacity: grainIntensity * 0.15 }}>
            <filter id="grain">
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.9"
                numOctaves="2"
                seed={frame % 100}
                stitchTiles="stitch"
              />
              <feColorMatrix type="saturate" values="0" />
            </filter>
            <rect width="100%" height="100%" filter="url(#grain)" />
          </svg>
        </AbsoluteFill>
      )}

      {/* Layer 4: Text overlays */}
      {(codex.text_overlays || []).map((overlay, index) => {
        const startFrame = overlay.start_frame || 0;
        const endFrame = overlay.end_frame || durationInFrames;

        if (frame < startFrame || frame > endFrame) return null;

        return (
          <TextOverlay key={overlay.id || index} overlay={overlay} frame={frame} fps={fps} />
        );
      })}
    </AbsoluteFill>
  );
};

/* ──────────────────────────────────────────────────────────────
 * TextOverlay — Affiche un texte avec animation mot par mot
 * Style concurrent 140M vues :
 *   - Mot par mot (chaque mot = span avec fade + scale)
 *   - Glow néon multi-couches si glow_intensity > 0
 *   - Contour noir (WebkitTextStroke)
 *   - Positions variées (center, top, center_bottom, center_left)
 * ────────────────────────────────────────────────────────────── */

const TextOverlay = ({ overlay, frame, fps }) => {
  const {
    content,
    animation = 'word_by_word',
    font = 'Impact, Arial Black, sans-serif',
    size = 96,
    color = '#FFFFFF',
    stroke_color = '#000000',
    stroke_width = 4,
    shadow = '2px 4px 8px rgba(0,0,0,0.9)',
    position = 'center',
    letter_spacing = '0em',
    glow_intensity = 0,
    depth_3d = 0,
    start_frame = 0,
  } = overlay;

  const localFrame = frame - start_frame;
  const words = content.split(' ');

  // Calculer le timing d'apparition des mots
  // Pour word_by_word : chaque mot apparaît à intervalle régulier
  const totalDuration = (overlay.end_frame || 300) - start_frame;
  const wordFadeFrames = 8; // frames pour le fade-in d'un mot
  let wordsPerFrame;

  if (animation === 'word_by_word') {
    // Les mots apparaissent sur les premiers 60% de la durée, puis restent
    const revealDuration = Math.max(totalDuration * 0.6, words.length * 8);
    wordsPerFrame = revealDuration / words.length;
  } else {
    wordsPerFrame = 0; // pas utilisé pour les autres animations
  }

  // Construire le glow néon
  const glowLayers = [];
  if (glow_intensity > 0) {
    const intensity = glow_intensity / 100;
    const layers = Math.round(intensity * 4); // 0 à 4 couches
    const glowSizes = [3, 6, 12, 20];
    for (let i = 0; i < layers; i++) {
      glowLayers.push(`0 0 ${glowSizes[i]}px ${color}`);
    }
    glowLayers.push(shadow); // ombre portée noire
  } else {
    glowLayers.push(shadow);
  }
  const textShadowStr = glowLayers.join(', ');

  // Contour
  const strokeStr =
    stroke_width > 0 ? `${stroke_width}px ${stroke_color}` : '0px transparent';

  // 3D depth (couches décalées)
  const depthLayers = [];
  if (depth_3d > 0) {
    for (let d = 1; d <= depth_3d; d++) {
      depthLayers.push(d);
    }
  }

  // Style de base du texte
  const baseTextStyle = {
    fontFamily: font,
    fontSize: `${size}px`,
    color: color,
    WebkitTextStroke: strokeStr,
    textShadow: textShadowStr,
    letterSpacing: letter_spacing,
    fontWeight: 900,
    textTransform: 'uppercase',
    lineHeight: 1.1,
    textAlign: 'center',
    pointerEvents: 'none',
    display: 'inline',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
    maxWidth: '85%',
  };

  // Container de position (séparé de l'animation pour éviter les conflits de transform)
  const positionStyle = getPositionStyle(position);

  // Animation du bloc entier (pour pop, fade_in, fade_in_slow)
  let blockOpacity = 1;
  let blockScale = 1;

  if (animation === 'pop') {
    blockOpacity = interpolate(localFrame, [0, 6], [0, 1], { extrapolateRight: 'clamp' });
    blockScale = interpolate(localFrame, [0, 6], [0.8, 1], { extrapolateRight: 'clamp' });
  } else if (animation === 'fade_in') {
    blockOpacity = interpolate(localFrame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
  } else if (animation === 'fade_in_slow') {
    blockOpacity = interpolate(localFrame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  }

  // Rendu
  if (animation === 'word_by_word') {
    // Mot par mot : chaque mot est un span animé individuellement
    return (
      <div
        style={{
          ...positionStyle,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
          zIndex: 10,
        }}
      >
        <div
          style={{
            ...baseTextStyle,
            opacity: 1,
            transform: 'none',
            display: 'inline',
            whiteSpace: 'pre-wrap',
          }}
        >
          {words.map((word, i) => {
            const wordStartFrame = i * wordsPerFrame;
            const wordLocalFrame = localFrame - wordStartFrame;
            const wordOpacity = interpolate(
              wordLocalFrame,
              [0, wordFadeFrames],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            const wordScale = interpolate(
              wordLocalFrame,
              [0, wordFadeFrames],
              [0.92, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            return (
              <span
                key={i}
                style={{
                  display: 'inline-block',
                  opacity: wordOpacity,
                  transform: `scale(${wordScale})`,
                  transition: 'none',
                  marginRight: i < words.length - 1 ? '0.25em' : '0',
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      </div>
    );
  }

  // Animations bloc entier (pop, fade_in, fade_in_slow)
  return (
    <div
      style={{
        ...positionStyle,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none',
        zIndex: 10,
      }}
    >
      {/* Couches 3D depth (si depth_3d > 0) */}
      {depthLayers.map((d) => (
        <div
          key={`depth-${d}`}
          style={{
            ...baseTextStyle,
            position: 'absolute',
            transform: `translate(${d}px, ${d}px)`,
            opacity: blockOpacity * 0.3,
            color: 'rgba(0,0,0,0.5)',
            WebkitTextStroke: '0px transparent',
            textShadow: 'none',
          }}
        >
          {content}
        </div>
      ))}
      <div
        style={{
          ...baseTextStyle,
          opacity: blockOpacity,
          transform: `scale(${blockScale})`,
        }}
      >
        {content}
      </div>
    </div>
  );
};

/* ──────────────────────────────────────────────────────────────
 * Helper: Position styles
 * ────────────────────────────────────────────────────────────── */

function getPositionStyle(position) {
  switch (position) {
    case 'center':
      return {
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '90%',
      };
    case 'top':
      return {
        position: 'absolute',
        top: '10%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
      };
    case 'center_bottom':
      return {
        position: 'absolute',
        bottom: '15%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
      };
    case 'bottom':
      return {
        position: 'absolute',
        bottom: '8%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
      };
    case 'center_left':
      return {
        position: 'absolute',
        top: '45%',
        left: '10%',
        width: '80%',
      };
    default:
      return {
        position: 'absolute',
        bottom: '15%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
      };
  }
}

/* ──────────────────────────────────────────────────────────────
 * Helper: Zoom interpolation
 * ────────────────────────────────────────────────────────────── */

function getCurrentZoom(frame, keyframes) {
  if (!keyframes || keyframes.length === 0) {
    return { scale: 1.0, target_x: 0.5, target_y: 0.5 };
  }

  if (frame <= keyframes[0].frame) {
    return {
      scale: keyframes[0].scale,
      target_x: keyframes[0].target_x,
      target_y: keyframes[0].target_y,
    };
  }

  if (frame >= keyframes[keyframes.length - 1].frame) {
    const last = keyframes[keyframes.length - 1];
    return { scale: last.scale, target_x: last.target_x, target_y: last.target_y };
  }

  // Trouver les keyframes encadrants
  for (let i = 0; i < keyframes.length - 1; i++) {
    const k1 = keyframes[i];
    const k2 = keyframes[i + 1];
    if (frame >= k1.frame && frame <= k2.frame) {
      const t = (frame - k1.frame) / (k2.frame - k1.frame);
      // Interpolation ease-in-out
      const easedT = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      return {
        scale: k1.scale + (k2.scale - k1.scale) * easedT,
        target_x: k1.target_x + (k2.target_x - k1.target_x) * easedT,
        target_y: k1.target_y + (k2.target_y - k1.target_y) * easedT,
      };
    }
  }

  return { scale: 1.0, target_x: 0.5, target_y: 0.5 };
}
