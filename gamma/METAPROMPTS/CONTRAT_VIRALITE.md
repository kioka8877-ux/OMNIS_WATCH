# CONTRAT DE VIRALITE — OMNIS-WATCH GAMMA
## Schéma tactique pour Shorts viraux

> **Rôle :** Dit à F02B et F03 exactement quoi mettre et où pour qu'un Short soit viral.
> PERTURABO = *quoi* raconter (stratégie). Contrat de Viralité = *comment* le raconter (rythme).

---

## PHASE 1 — HOOK (0-3s) : Les 3 coups simultanés

Un Short viral doit frapper les 3 sens en moins de 3 secondes.

| Sensoriel | Élément | Règle | Timing |
|-----------|---------|-------|--------|
| **Visuel** | Zoom d'entrée agressif | 1.0x → 1.3x en 0.5s sur la première frame | Frame 0-15 |
| **Textuel** | Premier texte écran | 2-4 mots, set up le payoff (pas juste un hook génial — Règle S2 PERTURABO) | Frame 0-30 |
| **Auditif** | SFX impact | Whoosh + pop ou music hit dans les 0.5 premières secondes | Frame 0-15 |

**Contrat :** Les 3 doivent tomber en moins de 3 secondes (frame 0-90 à 30fps).

### Variantes de hook selon le mode émotionnel

| Mode | Hook visuel | Hook textuel | Hook auditif |
|------|-------------|-------------|--------------|
| WHOLESOME | Zoom doux sur le sujet | "He's only three." | Music swell doux |
| TENSION | Zoom rapide + shake | "You think you know him." | Whoosh + impact |
| SURPRISE | Pop zoom (1.0x → 1.4x instant) | "Nobody expected this." | Ding + music hit |
| TRISTE | Zoom lent sur le visage | "This is Max." | Music seule, pas de SFX |

---

## PHASE 2 — RÉTENTION (3s → avant payoff) : Le rythme viral

Le but : empêcher le swipe. Le rythme doit varier — pas constant.

### 2.1 Micro-zooms sur mots forts

| Élément | Règle | Déclencheur |
|---------|-------|-------------|
| Zoom avant | 1.1x-1.3x progressif sur le mot fort | Chaque mot fort (timing.json `is_strong: true`) |
| Retour normal | 1.0x après le mot | Fin du mot fort |
| Durée du zoom | 0.3-0.8s (rapide pour tension, lent pour émotion) | Selon mode émotionnel |

### 2.2 SFX systématiques

| SFX | Quand | Volume |
|-----|-------|--------|
| Keyboard typing | Chaque apparition de texte écran | 40% |
| Whoosh | Chaque démarrage de zoom | 80% |
| Pop | Chaque texte "pop" animation | 60% |
| Ding | Chaque mot fort (ponctuation) | 70% |

### 2.3 Cuts brutaux

| Élément | Règle |
|---------|-------|
| Transitions entre séquences | Coupe nette (pas de fondu, pas de crossfade) |
| Sauf si mode TRISTE | Fondu lent autorisé |
| Alignement | Les cuts tombent sur les beats musicaux si possible (F03C) |

### 2.4 Variations de rythme

| Pattern | Quand | Effet |
|---------|-------|-------|
| Rapide → Lent | Après un passage tendu | Release, l'audience respire |
| Lent → Rapide | Avant le payoff | Buildup, tension qui monte |
| Statique → Zoom | Sur un mot clé révélation | Accentue l'impact |

### 2.5 Foreshadow (teaser du payoff)

| Élément | Règle | Timing |
|---------|-------|--------|
| Texte tease | Un texte qui prépare le payoff sans le dévoiler | Vers 40-60% de la vidéo |
| Zoom léger | Micro-zoom sur le teaser | Même moment |

---

## PHASE 3 — PAYOFF (Climax) : Le drop

Le payoff est le point d'ancrage (Règle S1 PERTURABO). Tout le Short converge vers ça.

| Élément | Règle | Intensité |
|---------|-------|-----------|
| Zoom maximum | 1.5x+ sur le moment clé | Maximum du Short |
| Texte neon | Effet glow au climax (couleur selon mode) | Vert WHOLESOME, rouge TENSION, etc. |
| SFX impact | Whoosh puissant + ding | 100% volume |
| Musique drop | TETE segment à 110% volume (F03C) | Drop final |
| CTA / Punchline | Dernier texte = call to action ou punchline émotionnelle | 2-5 mots |

### Structure du payoff selon le mode

| Mode | Payoff | CTA |
|------|--------|-----|
| WHOLESOME | Moment de tendresse maximal | "Every dog deserves a second chance." |
| TENSION | Révélation / twist | "You were wrong about him." |
| SURPRISE | Le reveal | "And that's when it happened." |
| TRISTE | Le moment de tristesse pure | "Good boy, Max." |

---

## INTÉGRATION TECHNIQUE

### F02B lit le contrat et génère le codex

Le codex.json gamma inclut de nouveaux champs :

```json
{
  "viralite": {
    "hook_phase": {
      "frames": [0, 90],
      "zoom_in": {"start": 1.0, "end": 1.3, "duration_frames": 15},
      "first_text": "txt_01",
      "sfx_impact": {"frame": 0, "type": "whoosh_pop", "volume": 0.9}
    },
    "retention": {
      "micro_zooms": "auto_on_strong_words",
      "sfx_pattern": "keyboard_per_text + whoosh_per_zoom",
      "cut_style": "brutal",
      "rhythm_pattern": "fast_slow_fast"
    },
    "payoff": {
      "frame": 380,
      "zoom_max": 1.5,
      "neon": true,
      "neon_color": "#00FF88",
      "sfx": "whoosh_ding",
      "music_drop": true,
      "cta_text": "txt_final"
    }
  }
}
```

### F03 exécute le codex

F03A lit `viralite.hook_phase` → applique le zoom d'entrée + premier texte + SFX.
F03A lit `viralite.retention` → applique les micro-zooms + cuts.
F03A lit `viralite.payoff` → applique le zoom max + neon + SFX impact.
F03B lit `viralite.*.sfx_*` → place les SFX aux frames exactes.
F03C lit `viralite.payoff.music_drop` → aligne le TETE sur le payoff.

---

## NOTES

- Le contrat est **statique** dans OMNIS-WATCH (Option A)
- Il est affiné au fil des productions
- PERTURABO fournit la stratégie (quoi raconter), le contrat fournit la tactique (comment le monter)
- Les deux sont lus par F02B au runtime
- Les modes émotionnels peuvent être étendus (NOSTALGIE, COLERE, ESPOIR...)
