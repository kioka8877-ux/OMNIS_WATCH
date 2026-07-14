# F03B — MIXER
## Le Chef d'Orchestre Sonore

## Role
Prend la video muette de F03A et lui greffe les SFX aux bonnes frames.

## Entree
- `video_visuelle.mp4` (depuis F03A OUT/, sans son)
- `codex.json` (section sfx_timeline definie par F02B)
- `sfx/` (bibliotheque de fichiers SFX depuis SHARED/IN/sfx/)

## Action
1. Lit le codex.json (section `sfx_timeline`)
2. Pour chaque entree SFX :
   - Calcule le timestamp exact (frame / fps)
   - Recupere le fichier audio correspondant (ex: whoosh.mp3, keyboard.mp3)
   - Applique le volume defini
3. FFmpeg mixe tous les SFX sur la piste audio de la video
4. Sortie : video complete avec image + son

## Sortie
- `video_complete.mp4` — video complete avec image de F03A et SFX mixes

## Ce que F03B NE fait PAS
- ❌ Genere les SFX (ils sont fournis par l'operateur dans SHARED/IN/sfx/)
- ❌ Decide du timing des SFX (ca c'est F02B qui decide dans le codex)
- ❌ Normalise le volume pour YouTube (→ F04 Camouflage)
- ❌ Nettoie les metadonnees (→ F04 Camouflage)

## Techno
- FFmpeg (GitHub Actions)
- Mapping frame → timestamp → fichier audio

## Runner
GitHub Actions (CPU gratuit)

## Format du mapping SFX
```json
"sfx_timeline": [
  {"frame": 45, "type": "whoosh", "volume": 0.8},
  {"frame": 0, "type": "keyboard", "volume": 0.3}
]
```

Le `type` correspond au nom du fichier dans `SHARED/IN/sfx/` (ex: `whoosh.mp3`, `keyboard.mp3`).
