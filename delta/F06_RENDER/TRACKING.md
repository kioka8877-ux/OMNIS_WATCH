# D-F06 RENDER - Tracking

## Statut
- **Statut :** À COPIER depuis gamma
- **Version :** delta (from gamma/F03_RENDER)
- **Priorité :** Étape 5-6

## Rôle
Wrapper pour les modules de rendu de gamma :
- F03A_REMOTION : Rendu avec presets et sous-titres animés
- F03B_MIXER : Ajout des SFX sur les mots forts

## Flow (par clip)
```
Pour chaque clip (boucle):
    ↓
    F03A_REMOTION
    ├─ Input: IN/video_coupee.mp4 + IN/codex.json
    ├─ Output: OUT/video_visuelle.mp4
    │
    F03B_MIXER
    ├─ Input: IN/video_visuelle.mp4 + IN/codex.json
    ├─ SFX: delta/SHARED/IN/sfx/
    └─ Output: OUT/video_complete.mp4
```

## Structure interne

```
F06_RENDER/
├── F03A_REMOTION/
│   ├── CODEBASE/         ← from gamma/F03_RENDER/F03A_REMOTION/CODEBASE
│   ├── IN/              ← input pour Remotion
│   └── OUT/             ← output de Remotion
│
└── F03B_MIXER/
    ├── CODEBASE/         ← from gamma/F03_RENDER/F03B_MIXER/CODEBASE
    ├── IN/              ← input pour mixer
    └── OUT/             ← output final du render
```

## Entrées
- `F03A_REMOTION/IN/video_coupee.mp4` (clip de D-F03)
- `F03A_REMOTION/IN/codex.json` (de D-F05, placé manuellement)
- `F03B_MIXER/IN/` (copie de F03A OUT)

## Sorties
- `F03B_MIXER/OUT/video_complete_001.mp4`
- `F03B_MIXER/OUT/video_complete_002.mp4`
- `F03B_MIXER/OUT/video_complete_003.mp4`

## Code
- Source : `gamma/F03_RENDER/F03A_REMOTION/` et `gamma/F03_RENDER/F03B_MIXER/`
- Techno : Node.js, Remotion, FFmpeg
- Runner : GitHub Actions

## Todo
- [x] Créer structure dossiers
- [ ] Copier gamma/F03_RENDER/F03A_REMOTION/CODEBASE → F06_RENDER/F03A_REMOTION/CODEBASE
- [ ] Copier gamma/F03_RENDER/F03B_MIXER/CODEBASE → F06_RENDER/F03B_MIXER/CODEBASE
- [ ] Créer `d06_render.yml` (boucle par clip)
- [ ] Tester avec 3 clips
