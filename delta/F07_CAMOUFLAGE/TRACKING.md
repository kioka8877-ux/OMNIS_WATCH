# D-F07 CAMOUFLAGE - Tracking

## Statut
- **Statut :** EXISTANT (renommé depuis F05)
- **Version :** delta
- **Priorité :** Étape 7

## Rôle
Re-encode la vidéo en H264 propre avec audio AAC normalisé.
Supprime les métadonnées suspectes.

## Flow
```
D-F06 (video_complete_001.mp4, video_complete_002.mp4...)
    ↓
D-F07 lit tous les clips dans IN/
D-F07 re-encode en H264 CRF18 + AAC 192k
D-F07 normalise audio (loudnorm -14 LUFS)
D-F07 supprime métadonnées suspectes
    ↓
OUT/clips_camoufles/
OUT/camouflage_manifest.json
    ↓
D-F08 LUTHER prend le relais
```

## Entrées
- `IN/` : video_complete_*.mp4 de D-F06
- `IN/camouflage_manifest.json` (optionnel)

## Sorties
- `OUT/clips_camoufles/video_camoufle_001.mp4`
- `OUT/clips_camoufles/video_camoufle_002.mp4`
- `OUT/camouflage_manifest.json`

## Code
- Script : `CODEBASE/omnis_d07_camouflage.py`
- Techno : FFmpeg
- Runner : GitHub Actions

## Todo
- [x] Structure créée (copie depuis F05_CAMOUFLAGE)
- [ ] Renommer omnis_d05_camouflage.py → omnis_d07_camouflage.py
- [ ] Mettre à jour références dans le script
- [ ] Renommer workflow d05_camouflage.yml → d07_camouflage.yml
- [ ] Tester avec 3 clips
