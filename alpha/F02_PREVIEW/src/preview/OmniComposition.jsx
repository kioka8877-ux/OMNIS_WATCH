import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  Video,
  Sequence,
  OffthreadVideo,
} from 'remotion';

/**
 * OmniComposition — Composition principale OMNIS-WATCH
 * Lit le codex.json et orchestre tous les layers.
 *
 * Props:
 *   codex: object — le codex.json genere par F02B
 *   videoSrc: string — chemin vers video_coupee.mp4
 */
export const OmniComposition = ({ codex, videoSrc }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  // Calculer le zoom actuel base sur les keyframes
  const currentZoom = getCurrentZoom(frame, codex.zoom_keyframes || []);

  // Calculer le offset du zoom base sur le tracking
  const trackingOffset = getTrackingOffset(frame, codex);

  // CSS filter pour la colorimetrie
  const colorFilter = codex.color_css_filter || '';

  // CSS filter pour l'enhance 4K
  const enhanceFilter = codex.enhance_4k
    ? ' contrast(1.1) saturate(1.15) brightness(1.05)'
    : '';

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Layer 1: Video source avec zoom + colorimetrie */}
      <AbsoluteFill
        style={{
          transform: `scale(${currentZoom.scale}) translate(${
            -currentZoom.targetX * width + width / 2
          }px, ${-currentZoom.targetY * height + height / 2}px)`,
          transformOrigin: `${currentZoom.targetX * 100}% ${
            currentZoom.targetY * 100
          }%`,
        }}
      >
        <OffthreadVideo src={videoSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </AbsoluteFill>

      {/* Layer 2: Color grade + enhance 4K (overlay transparent) */}
      <AbsoluteFill
        style={{
          filter: colorFilter + enhanceFilter,
          pointerEvents: 'none',
        }}
      />

      {/* Layer 3: Text overlays */}
      {(codex.text_overlays || []).map((overlay, index) => (
        <TextOverlay
          key={overlay.id || index}
          overlay={overlay}
          frame={frame}
          fps={fps}
        />
      ))}
    </AbsoluteFill>
  );
};

// ── Helper: Zoom interpolation ──────────────────────────────────────────────

function getCurrentZoom(frame, keyframes) {
  if (!keyframes || keyframes.length === 0) {
    return { scale: 1.0, targetX: 0.5, targetY: 0.5 };
  }

  // Trouver les keyframes avant et apres la frame courante
  let prev = keyframes[0];
  let next = keyframes[keyframes.length - 1];

  for (let i = 0; i < keyframes.length; i++) {
    if (keyframes[i].frame <= frame) {
      prev = keyframes[i];
    }
    if (keyframes[i].frame >= frame) {
      next = keyframes[i];
      break;
    }
  }

  if (prev.frame === next.frame) {
    return {
      scale: prev.scale,
      targetX: prev.target_x || 0.5,
      targetY: prev.target_y || 0.5,
    };
  }

  // Interpolation lineaire
  const t = (frame - prev.frame) / (next.frame - prev.frame);
  const easedT = easeInOutCubic(t);

  return {
    scale: interpolate(easedT, [0, 1], [prev.scale, next.scale]),
    targetX: interpolate(easedT, [0, 1], [prev.target_x || 0.5, next.target_x || 0.5]),
    targetY: interpolate(easedT, [0, 1], [prev.target_y || 0.5, next.target_y || 0.5]),
  };
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// ── Helper: Tracking offset ────────────────────────────────────────────────

function getTrackingOffset(frame, codex) {
  // TODO: lire tracking_data.json et ajuster target_x/target_y
  // Pour l'instant, les keyframes du codex contiennent deja les positions
  return { offsetX: 0, offsetY: 0 };
}

// ── TextOverlay Component ──────────────────────────────────────────────────

const TextOverlay = ({ overlay, frame, fps }) => {
  const { start_frame, end_frame, animation, content, position } = overlay;

  // Ne rendre que si on est dans la fenetre de temps
  if (frame < start_frame || frame > end_frame) {
    return null;
  }

  const localFrame = frame - start_frame;
  const totalFrames = end_frame - start_frame;

  // Calculer l'opacite et la transformation selon l'animation
  let opacity = 1;
  let transform = '';
  let visibleChars = content.length;

  switch (animation) {
    case 'fade_in':
      opacity = interpolate(localFrame, [0, Math.min(15, totalFrames / 3)], [0, 1], {
        extrapolateRight: 'clamp',
      });
      if (localFrame > totalFrames - 15) {
        opacity = interpolate(localFrame, [totalFrames - 15, totalFrames], [1, 0], {
          extrapolateLeft: 'clamp',
        });
      }
      break;

    case 'fade_in_slow':
      opacity = interpolate(localFrame, [0, Math.min(30, totalFrames / 2)], [0, 1], {
        extrapolateRight: 'clamp',
      });
      if (localFrame > totalFrames - 20) {
        opacity = interpolate(localFrame, [totalFrames - 20, totalFrames], [1, 0], {
          extrapolateLeft: 'clamp',
        });
      }
      break;

    case 'typewriter':
      // Apparition lettre par lettre
      const charsPerFrame = Math.max(1, content.length / Math.min(totalFrames * 0.6, 60));
      visibleChars = Math.min(content.length, Math.floor(localFrame * charsPerFrame));
      opacity = localFrame < 2 ? 0 : 1;
      // Fade out a la fin
      if (localFrame > totalFrames - 10) {
        opacity = interpolate(localFrame, [totalFrames - 10, totalFrames], [1, 0], {
          extrapolateLeft: 'clamp',
        });
      }
      break;

    case 'slide_left':
      const slideProgress = interpolate(localFrame, [0, 15], [0, 1], {
        extrapolateRight: 'clamp',
      });
      transform = `translateX(${interpolate(slideProgress, [0, 1], [100, 0])}px)`;
      opacity = slideProgress;
      if (localFrame > totalFrames - 10) {
        opacity = interpolate(localFrame, [totalFrames - 10, totalFrames], [1, 0], {
          extrapolateLeft: 'clamp',
        });
      }
      break;

    case 'slide_right':
      const slideRProgress = interpolate(localFrame, [0, 15], [0, 1], {
        extrapolateRight: 'clamp',
      });
      transform = `translateX(${interpolate(slideRProgress, [0, 1], [-100, 0])}px)`;
      opacity = slideRProgress;
      if (localFrame > totalFrames - 10) {
        opacity = interpolate(localFrame, [totalFrames - 10, totalFrames], [1, 0], {
          extrapolateLeft: 'clamp',
        });
      }
      break;

    case 'pop':
      const popProgress = spring({
        frame: localFrame,
        fps,
        config: { damping: 12, stiffness: 200, mass: 0.8 },
      });
      const scale = interpolate(popProgress, [0, 1], [0.3, 1]);
      transform = `scale(${scale})`;
      opacity = popProgress;
      if (localFrame > totalFrames - 10) {
        opacity = interpolate(localFrame, [totalFrames - 10, totalFrames], [1, 0], {
          extrapolateLeft: 'clamp',
        });
      }
      break;

    default:
      opacity = 1;
  }

  // Position
  const positionStyles = getPositionStyles(position || 'center_bottom');

  // Style du texte
  const textStyle = {
    position: 'absolute',
    ...positionStyles,
    fontFamily: overlay.font || 'Arial Black, sans-serif',
    fontSize: `${overlay.size || 64}px`,
    color: overlay.color || '#FFFFFF',
    WebkitTextStroke: `${overlay.stroke_width || 3}px ${overlay.stroke_color || '#000000'}`,
    textShadow: `0 4px 12px rgba(0,0,0,0.8)`,
    opacity,
    transform,
    textAlign: 'center',
    width: '100%',
    maxWidth: '90%',
    lineHeight: 1.2,
    fontWeight: 900,
    textTransform: 'uppercase',
    letterSpacing: '0.02em',
    pointerEvents: 'none',
  };

  return (
    <div style={textStyle}>
      {animation === 'typewriter'
        ? content.substring(0, visibleChars)
        : content}
    </div>
  );
};

function getPositionStyles(position) {
  switch (position) {
    case 'center':
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    case 'top':
      return {
        top: '10%',
        left: '50%',
        transform: 'translateX(-50%)',
      };
    case 'center_bottom':
      return {
        bottom: '15%',
        left: '50%',
        transform: 'translateX(-50%)',
      };
    case 'bottom':
      return {
        bottom: '8%',
        left: '50%',
        transform: 'translateX(-50%)',
      };
    default:
      return {
        bottom: '15%',
        left: '50%',
        transform: 'translateX(-50%)',
      };
  }
}
