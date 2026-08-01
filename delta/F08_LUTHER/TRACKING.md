# D-F08 LUTHER - Tracking

## Statut
- **Statut :** EXISTANT (renommé depuis F06)
- **Version :** delta
- **Priorité :** Étape 8

## Rôle
Efface complètement les traces numériques de la vidéo.
Strip toutes les métadonnées, normalise les timestamps.

## Flow
```
D-F07 (clips_camoufles/)
    ↓
D-F08 lit tous les clips dans IN/
D-F08 stream copy (copie propre)
D-F08 strip TOUTES les métadonnées
D-F08 normalise timestamps
    ↓
OUT/clips_finaux/final_001.mp4
OUT/clips_finaux/final_002.mp4
OUT/clips_finaux/final_003.mp4
OUT/luther_manifest.json
    ↓
✅ PIPELINE TERMINÉ
```

## Entrées
- `IN/` : clips_camoufles/ de D-F07
- `IN/luther_manifest.json` (optionnel)

## Sorties
- `OUT/clips_finaux/final_001.mp4` ← FINAL OUTPUT
- `OUT/clips_finaux/final_002.mp4` ← FINAL OUTPUT
- `OUT/clips_finaux/final_003.mp4` ← FINAL OUTPUT
- `OUT/luther_manifest.json`

## Code
- Script : `CODEBASE/omnis_d08_luther.py`
- Techno : FFmpeg
- Runner : GitHub Actions

## Todo
- [x] Structure créée (copie depuis F06_LUTHER)
- [ ] Renommer omnis_d06_luther.py → omnis_d08_luther.py
- [ ] Mettre à jour références dans le script
- [ ] Renommer workflow d06_luther.yml → d08_luther.yml
- [ ] Tester avec 3 clips
