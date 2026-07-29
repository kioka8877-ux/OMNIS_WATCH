# D-F04 ASSEMBLY - Tracking

## Statut
- **Statut :** PLANIFI
- **Version :** delta
- **Priorit :** tape 6

## Rle
Le monteur de la flotte. Prend les clips reframes, leur ajoute des sous-titres
styles (depuis le transcript), des SFX viraux (selon PERTURABO rules), et
applique le loop hook (fin reconnecte au dbut).

## Flow
```
clips_reframes/ de D-F03 + transcript.json de D-F01 + cutlist.json de D-F02
    ↓
D-F04 extrait les mots du transcript pour chaque clip
D-F04 gnre les sous-titres styles (ASS/FFmpeg)
D-F04 burn les sous-titres dans la vido
D-F04 ajoute les SFX (whoosh pop ding keyboard) selon les rgles virales
D-F04 applique le loop hook (recadrage fin→dbut)
    ↓
OUT/clips_finaux/ (clip_final_001.mp4 ... clip_final_N.mp4)
OUT/assembly_manifest.json
    ↓
L'oprateur valide les clips (fin du pipeline delta)
```

## Entres
- `IN/clips_reframes/` (de D-F03)
- `IN/transcript.json` (de D-F01)
- `IN/cutlist.json` (de D-F02)
- `SHARED/IN/sfx/` (whoosh.mp3, pop.mp3, ding.mp3, keyboard.mp3)

## Sorties
- `OUT/clips_finaux/clip_final_{idx:03d}.mp4` : clips finaux avec sous-titres + SFX
- `OUT/assembly_manifest.json` : mapping complet

## SFX selon PERTURABO
| SFX | Dclencheur | Volume | Timing |
|-----|-----------|--------|--------|
| Whoosh | Chaque dbut de zoom/transition | 80% | Frame 0-5 |
| Pop | Chaque apparition de sous-titre | 60% | Synchro avec le mot |
| Ding | Chaque mot fort / payoff | 70% | Synchro avec le mot |
| Keyboard | Chaque texte long | 40% | Continue |

## Loop hook (Rgle S4 PERTURABO)
La fin du clip doit reconnecter au dbut. Techniques :
- Callback : dernier mot = premier mot
- Match cut : dernire frame ressemble la premire
- Audio continuity : le son de la fin se fond dans le dbut

## Code
- Script : `CODEBASE/omnis_d04_assembly.py` (non cr)
- Techno : FFmpeg (subtitles filter, amix, concat)
- Runner : GitHub Actions (ubuntu-latest)

## Tests de validation (T5)
| # | Entre | Attendu | Statut |
|---|-------|---------|--------|
| T5.1 | clip_reframe + transcript + cutlist | Clip avec sous-titres burns, lisibles | EN ATTENTE CODE |
| T5.2 | Mmes entres + sfx/ | Clip avec SFX (whoosh, pop, ding) aux bons moments | EN ATTENTE CODE |
| T5.3 | Mmes entres | Loop hook prsent (fin + dbut lisible) | EN ATTENTE CODE |
