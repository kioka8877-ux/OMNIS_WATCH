import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
} from 'remotion';
import { codex as codexData } from '../codexData';
import { loadFont } from '@remotion/google-fonts/Anton';

const { fontFamily: antonFont } = loadFont();

/* ────────────────────────────────────────────────────────────────────────────
 * OmniComposition — Composition principale OMNIS-WATCH
 * Lit le codex.json et orchestre tous les layers.
 *
 * Props:
 *   codex: object — le codex.json généré par F02B
 *   videoSrc: string — chemin vers video_coupee.mp4
 * ──────────────────────────────────────────────────────────────────────────── */

export const OmniComposition = ({ codex: codexProp }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  // Utiliser le codex importé directement (plus fiable que les props)
  const codex = codexProp || codexData;

  // Video source hardcodé — staticFile résoud le chemin vers public/
  const videoSrc = staticFile('video_coupee.mp4');

  // Guard: si le codex n'est pas chargé, afficher un message d'erreur visible
  if (!codex) {
    return (
      <AbsoluteFill style={{ backgroundColor: '#ff4400', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: 64, fontWeight: 'bold' }}>CODEX MANQUANT</div>
      </AbsoluteFill>
    );
  }

  // Calculer le zoom actuel basé sur les keyframes
  const currentZoom = getCurrentZoom(frame, codex.zoom_keyframes || []);

  // CSS filter pour la colorimétrie
  const colorFilter = codex.color_css_filter || '';
  const enhanceFilter = codex.enhance_4k
    ? ' contrast(1.15) saturate(1.2) brightness(1.08)'
    : '';

  // Sharpening (simulé via CSS drop-shadow + contrast)
  const sharpening = codex.sharpening || 0;
  const denoising = codex.denoising || 0;
  let sharpFilter = '';
  if (sharpening > 0) {
    const s = sharpening / 100;
    sharpFilter = ` contrast(${1 + s * 0.15}) drop-shadow(0 0 ${s * 0.5}px rgba(255,255,255,${s * 0.15}))`;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LE FILTRE COMPLET — c'est cette variable qui était calculée mais JAMAIS appliquée
  // ═══════════════════════════════════════════════════════════════════════════
  const fullFilter = (colorFilter + enhanceFilter + sharpFilter).trim();

  // Vignette
  const vignetteOpacity = codex.vignette || 0;

  // Grain
  const grainIntensity = codex.grain_intensity || 0;

  // Slow motion
  const slowmoStart = codex.slowmo_start_frame || 0;
  const slowmoSpeed = codex.slowmo_speed || 1.0;
  const cutFlashFrames = codex.cut_flash_frames || 0;
  const isSlowmo = frame >= slowmoStart && slowmoSpeed < 1.0;
  const playbackRate = isSlowmo ? slowmoSpeed : 1.0;

  // Camera shake au moment du cut — purement vertical, fluide
  const shakePower = codex.shake_power || 50; // 0-100%
  const shakeFrame = slowmoStart;
  const shakeDuration = 20; // frames de shake
  const isShaking = shakePower > 0 && frame >= shakeFrame && frame < shakeFrame + shakeDuration;
  let shakeX = 0, shakeY = 0;
  if (isShaking) {
    const shakeProgress = (frame - shakeFrame) / shakeDuration;
    // Amplitude décroissante smooth (ease-out)
    const decay = Math.pow(1 - shakeProgress, 2);
    const amp = (shakePower / 100) * decay * 20; // max 20px à 100%
    // Onde sinusoïdale pure verticale — fluide, pas saccadé
    shakeY = Math.sin((frame - shakeFrame) * 0.8) * amp;
    shakeX = 0; // pas de mouvement horizontal
  }

  // Pas de flash blanc — juste le shake

  // Calcul du transform pour le zoom + shake
  const zoomTransform = `scale(${currentZoom.scale}) translate(${
    (0.5 - currentZoom.target_x) * 100
  }%, ${(0.5 - currentZoom.target_y) * 100}%)`;

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Layer 1: Vidéo source avec zoom + colorimétrie + slow motion + shake */}
      <AbsoluteFill
        style={{
          // ═══════════════════════════════════════════════════════════════════
          // FIX: fullFilter est maintenant APPLIQUÉ ici
          // ═══════════════════════════════════════════════════════════════════
          filter: fullFilter || undefined,
        }}
      >
        <OffthreadVideo
          src={videoSrc}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `${zoomTransform} translate(${shakeX}px, ${shakeY}px)`,
          }}
          playbackRate={playbackRate}
        />
      </AbsoluteFill>

      {/* Layer 2: Badge SLOW MOTION */}
      {isSlowmo && (
        <AbsoluteFill style={{ justifyContent: 'flex-start', alignItems: 'flex-end', padding: 40 }}>
          <div style={{
            backgroundColor: 'rgba(0,0,0,0.7)',
            color: '#FF4444',
            fontSize: 32,
            fontWeight: 'bold',
            padding: '8px 20px',
            borderRadius: 8,
            fontFamily: antonFont,
            letterSpacing: '0.1em',
          }}>
            SLOW MOTION
          </div>
        </AbsoluteFill>
      )}

      {/* Layer 3: Vignette */}
      {vignetteOpacity > 0 && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,${vignetteOpacity}) 100%)`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Layer 4: Grain cinématique (SVG feTurbulence — style CRUSADER) */}
      {grainIntensity > 0 && (
        <AbsoluteFill style={{ opacity: grainIntensity, pointerEvents: 'none' }}>
          <svg
            width="100%"
            height="100%"
            style={{ position: 'absolute', top: 0, left: 0 }}
          >
            <filter id="grainFilter">
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.9"
                numOctaves="2"
                stitchTiles="stitch"
              />
              <feColorMatrix
                type="matrix"
                values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.5 0"
              />
            </filter>
            <rect width="100%" height="100%" filter="url(#grainFilter)" />
          </svg>
        </AbsoluteFill>
      )}

      {/* Layer 5: Text overlays */}
      {(codex.text_overlays || []).map((overlay, index) => {
        const startFrame = overlay.start_frame || 0;
        const endFrame = overlay.end_frame || durationInFrames;

        if (frame < startFrame || frame > endFrame) return null;

        return (
          <Sequence
            key={overlay.id || index}
            from={startFrame}
            durationInFrames={endFrame - startFrame + 1}
          >
            <TextOverlay overlay={overlay} frame={frame - startFrame} fps={fps} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

/* ────────────────────────────────────────────────────────────────────────────
 * TextOverlay — Affiche un texte avec animation mot par mot
 * Style concurrent 140M vues :
 * - Mot par mot (chaque mot = span avec fade + scale)
 * - Glow néon multi-couches si glow_intensity > 0
 * - Contour noir (WebkitTextStroke)
 * - Positions variées (center, top, center_bottom, center_left)
 * ──────────────────────────────────────────────────────────────────────────── */

const TextOverlay = ({ overlay, frame, fps }) => {
  const {
    content,
    animation = 'word_by_word',
    font = antonFont,
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

  const localFrame = frame;
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
      <div style={positionStyle}>
        <div
          style={{
            ...baseTextStyle,
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
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
                  opacity: wordOpacity,
                  transform: `scale(${wordScale})`,
                  display: 'inline-block',
                  transition: 'none',
                }}
              >
                {word}
                {i < words.length - 1 ? '\u00A0' : ''}
              </span>
            );
          })}
        </div>
      </div>
    );
  }

  // Animations bloc entier (pop, fade_in, fade_in_slow)
  return (
    <div style={positionStyle}>
      <div
        style={{
          ...baseTextStyle,
          opacity: blockOpacity,
          transform: `scale(${blockScale})`,
        }}
      >
        {/* Couches 3D depth (si depth_3d > 0) */}
        {depthLayers.map((d) => (
          <div
            key={d}
            style={{
              ...baseTextStyle,
              position: 'absolute',
              top: `${d}px`,
              left: `${d}px`,
              color: 'rgba(0,0,0,0.3)',
              WebkitTextStroke: '0px transparent',
              textShadow: 'none',
            }}
          >
            {content}
          </div>
        ))}
        {content}
      </div>
    </div>
  );
};

/* ────────────────────────────────────────────────────────────────────────────
 * Helper: Position styles
 * ──────────────────────────────────────────────────────────────────────────── */

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

/* ────────────────────────────────────────────────────────────────────────────
 * Helper: Zoom interpolation
 * ──────────────────────────────────────────────────────────────────────────── */

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
