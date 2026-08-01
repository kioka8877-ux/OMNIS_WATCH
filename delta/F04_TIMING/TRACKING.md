# D-F04 TIMING - Tracking

## Statut
- **Statut :** À CRÉER
- **Version :** delta
- **Priorité :** Étape 2

## Rôle
Extrait le timing.json pour chaque clip depuis le transcript.json de D-F01.
Convertit les timestamps globaux en timestamps locaux par clip.

## Flow
```
D-F03 (clips_reframes/ + reframe_manifest.json)
    ↓
D-F04 lit transcript.json (timestamps globaux de la vidéo complète)
D-F04 lit cutlist.json (bornes de chaque clip)
D-F04 extrait les mots dans la plage de chaque clip
    ↓
OUT/timing_001.json
OUT/timing_002.json
OUT/timing_003.json
    ↓
D-F05 PREVIEW prend le relais (manuel)
```

## Entrées
- `IN/transcript.json` (de D-F01)
- `IN/cutlist.json` (de D-F02 via D-F03)
- `IN/reframe_manifest.json` (de D-F03, optionnel)

## Sorties
- `OUT/timing_001.json` : mots du clip 1 avec timestamps locaux
- `OUT/timing_002.json` : mots du clip 2 avec timestamps locaux
- `OUT/timing_003.json` : mots du clip 3 avec timestamps locaux
- `OUT/timing_manifest.json` : liste des fichiers générés

## Format timing.json

```json
{
  "clip_index": 1,
  "source_start_sec": 0.0,
  "source_end_sec": 10.5,
  "words": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.5,
      "is_strong": false
    },
    {
      "word": "world",
      "start": 0.5,
      "end": 1.0,
      "is_strong": true
    }
  ]
}
```

## Code
- Script : `CODEBASE/extract_timing.py`
- Techno : Python standard (json, pathlib)
- Runner : GitHub Actions

## Todo
- [x] Créer `CODEBASE/extract_timing.py`
- [x] Vérifier `IN/` avec .gitkeep
- [x] Vérifier `OUT/` avec .gitkeep
- [x] Créer `d04_timing.yml`
- [ ] Tester avec transcript.json de 3 clips
