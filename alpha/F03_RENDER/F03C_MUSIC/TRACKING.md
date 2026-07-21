# F03C — Mixeur Musical (Canonisé ALPHA)

## Statut
✅ CANONISÉ en ALPHA sur main — Mode texte qui dirige (pas de voix off)

## Rôle
F03C prend la vidéo de F03B (SFX) et ajoute la musique de fond.
S'insère entre F03B et F04 : F03A → F03B → **F03C** → F04 → F05

## Architecture

### F03C-A — L'Architecte (Analyse + Directives)
- **Phase analyze** : Librosa détecte BPM + beats + waveform → viewer HTML
- **Phase oracle** : L'Oracle sandbox enrichit les segments → directives.json
- **Viewer** : Hébergé sur GitHub Pages (f03c/)
  - Timeline 1 : musique source avec beats, sections d'énergie, clic IN/OUT
  - Timeline 2 : rendu assemblé avec playback séquentiel
  - Sliders vitesse 0.5x-2x (preservesPitch), reverse, loops
  - Sync vidéo automatique (indicateur 🟢/🟡/🔴)
  - Reset par segment, inputs éditables, graduations

### F03C-B — La Machine (Mixage)
- Découpe la musique en QUEUE/LOOP/TETE selon directives.json
- Applique speed, reverse, volume_pct, fades, loops par segment
- Crossfade entre segments
- Stretch pour couvrir la durée vidéo
- **Mode ALPHA : volume constant, pas de ducking** (pas de voix off)
- Mux audio sur vidéo → video_with_music.mp4
- Export backbone (musique seule)

## Mode ALPHA vs BETA
| Élément | ALPHA (main) | BETA (main) |
|---------|-------------|-------------|
| Ducking | ❌ Volume constant | ✅ -14dB sous voix off |
| timing.json | ❌ Pas besoin | ✅ Source du ducking |
| Voix off | ❌ Texte qui dirige | ✅ Whisper |
| Input vidéo | video_complete.mp4 (SFX) | video_complete.mp4 (SFX + voix) |

## Fichiers
- `CODEBASE/omnis_f03c_a.py` — Architecte (Librosa + viewer + Oracle)
- `CODEBASE/omnis_f03c_b.py` — Machine (Pydub + mixage + mux)
- `CODEBASE/requirements_f03c.txt` — Dépendances
- `IN/directives.json` — Directives de mixage (générées par Oracle)
- `IN/analysis.json` — Analyse Librosa (BPM, beats)
- `IN/viewer.html` — Viewer F03C-A (aussi sur GitHub Pages)
- `OUT/` — video_with_music.mp4, master_audio_mix.mp3, backbone

## Workflow
- `.github/workflows/f03c_music.yml` — workflow_dispatch manuel
- Installe librosa + pydub + ffmpeg
- Lance F03C-B avec les chemins alpha/
- Upload artifact f03c-output

## Héritage
Adapté depuis SANCTORUM F03_SERAPHIM (seraphim_a.py + seraphim_b.py).
