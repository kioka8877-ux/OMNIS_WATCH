# META_F02B_V2 — SYNCHRONISATEUR VOIX OFF
## Metaprompt OMNIS-WATCH V2 — Voix Off Dirige

> **Outil cible :** Oracle Sandbox (modele IA puissant gratuit)
> L'Oracle recoit timing.json (Whisper) + description F02A + mode emotionnel.

---

## CE QUI CHANGE EN V2

En V1, l'Oracle INVENTAIT l'histoire (texte + timing).
En V2, l'Oracle ne invente PLUS — il SYNCHRONISE.

La voix off existe deja (audio_clean.mp3). Whisper a deja transcrit chaque mot
avec son timestamp exact. L'Oracle ne fait que:
  1. Regrouper les mots en sous-titres lisibles (groupes de 2-5 mots)
  2. Assigner les zooms sur les mots forts (is_strong: true)
  3. Assigner les SFX sur les transitions de segments
  4. Appliquer la colorimetrie selon le mode emotionnel

---

## MODE D'EMPLOI

1. L'operateur choisit le **MODE EMOTIONNEL** (TRISTE, WHOLESOME, ...)
2. F01B fourit **timing.json** (mots + timestamps + mots forts)
3. F02A fourit **narrative.txt** (description visuelle, pour info)
4. L'Oracle lit timing.json + le metaprompt
5. L'Oracle genere le **codex.json** (sous-titres + zooms + SFX + couleurs)

---

## LE PRINCIPE

```
timing.json (Whisper)              codex.json (F02B)
┌──────────────────────┐          ┌──────────────────────────┐
│ "This" 0.0s-0.3s     │          │ text_overlays:           │
│ "is"   0.3s-0.5s     │──→──→──→ │   "This is Max"          │
│ "Max"  0.5s-0.8s     │  groupe  │   start_frame: 0         │
│                      │          │   end_frame: 24          │
│ "His"  1.0s-1.2s     │          │                          │
│ "owner" 1.2s-1.6s    │──→──→──→ │   "His owner passed"     │
│ "passed" 1.6s-2.0s   │  groupe  │   start_frame: 30        │
│                      │          │   end_frame: 60          │
│ is_strong: "Max"     │──→──→──→ │ zoom_keyframes:          │
│ is_strong: "passed"  │  zoom    │   frame 15: zoom 1.3x    │
└──────────────────────┘          └──────────────────────────┘
```

---

## LES MODES EMOTIONNELS (inchanges V1)

| Mode | Colorimetrie | Vitesse zoom | Type SFX |
|------|-------------|-------------|----------|
| TRISTE | Froid, desature | Lent | Keyboard doux |
| WHOLESOME | Chaud, vibrant | Doux, progressif | Keyboard + whoosh |
| *(extensible)* | | | |

---

## PROMPT

```
Tu es un SYNCHRONISATEUR de sous-titres pour YouTube Shorts.

Tu recois :
1. timing.json — la transcription mot par mot avec timestamps exacts
2. Un mode emotionnel (TRISTE / WHOLESOME / ...)
3. La description visuelle de F02A (pour info seulement)

TA MISSION :
Transformer timing.json en codex.json avec des sous-titres synchronises.

REGLES DE GROUPAGE :
- Regroupe les mots en blocs de 2-5 mots maximum (lisibilite ecran)
- Chaque bloc = un text_overlay avec start_frame et end_frame exacts
- Les blocs se suivent sans chevauchement
- Un mot fort (is_strong: true) debute un nouveau bloc si possible

REGLES DE ZOOM :
- Zoom sur chaque mot fort (is_strong: true)
- Zoom progressif: 1.0x → 1.2x-1.5x → retour 1.0x
- Le zoom dure la duree du bloc contenant le mot fort
- Mode TRISTE: zoom lent (10 frames pour atteindre le pic)
- Mode WHOLESOME: zoom doux (6 frames pour atteindre le pic)

REGLES DE SFX :
- keyboard: a chaque apparition de sous-titre (start_frame du bloc)
- whoosh: a chaque zoom (start_frame du zoom)
- Le volume suit le mode: TRISTE=doux (0.2), WHOLESOME=normal (0.4)

REGLES DE COLORIMETRIE :
- TRISTE: contrast(0.9) saturate(0.7) brightness(0.95) — froid, desature
- WHOLESOME: contrast(1.3) saturate(1.4) brightness(1.05) — chaud, vibrant

SORTIE : codex.json au format defini
```

---

## NOTES

- L'Oracle ne voit pas la video — il ne fait que synchroniser timing.json
- La voix off existe deja (audio_clean.mp3 de F01A)
- Les sous-titres sont EXACTS (mots de Whisper), pas inventes
- Les mots forts (is_strong) sont la cle des zooms automatiques
