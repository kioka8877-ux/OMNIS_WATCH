# F01B — WHISPER
## Transcription Audio → timing.json

## Rôle
Transcrit l'audio clean mot par mot via faster-whisper.
Produit `timing.json` — le document maître temporel pour tout le pipeline.

## Entrée
- `audio_clean.mp3` — Audio sans silences (de F01A)

## Action
1. faster-whisper transcrit avec `word_timestamps=True`
2. Détection automatique de la langue
3. Calcul des frames (start_frame, end_frame) pour chaque mot
4. Détection des "mots forts" (is_strong: true)

## Sortie
- `timing.json` — Mots + timestamps + frames + mots forts

## Mots forts (is_strong)
Un mot est "fort" si :
1. Balisé `[mot]` par l'opérateur
2. En MAJUSCULES dans la transcription
3. Durée > 1.8x la moyenne
4. >= 7 caractères ET pas un stopword

Ces mots déclencheront automatiquement des zooms dans F02B.

## Modèles
| Modèle | Vitesse CPU GH Actions | Précision |
|--------|----------------------|-----------|
| tiny | ~5s | Faible |
| **base** (défaut) | ~15s | Moyenne |
| small | ~30s | Bonne |
| medium | ~60s | Excellente |

## Workflow GitHub Actions
```yaml
f01b_whisper.yml — workflow_dispatch (manuel)
```

## Adapté de
CRUSADER `crs_f01_grimaldus.py` — modèle par défaut: base (CPU)
