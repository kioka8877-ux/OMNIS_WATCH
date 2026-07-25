# F03C — MIXER MUSICAL
## L'Architecte + La Machine à Micro-jets

## Role
Prend la video de F03B (SFX + voix off) et ajoute la musique de fond avec ducking.

## Architecture
- **F03C-A** : Analyse musique (Librosa) + viewer HTML + Oracle enrichit -> directives.json
- **F03C-B** : Decoupe musique (Pydub) + ducking + mix avec video_complete.mp4 -> video_with_music.mp4

## Entree
- `video_complete.mp4` (depuis F03B OUT/, avec SFX + voix off)
- `music.mp3` (fourni par l'operateur)
- `directives.json` (genere par F03C-A + Oracle)
- `script_voix_off.txt` (F02B, pour l'Oracle)
- `timing.json` (F01B, pour l'Oracle)

## Sortie
- `video_with_music.mp4` — video complete avec image + SFX + voix + musique
- `master_audio_mix.mp3` — audio mix seul (debug)
- `master_audio_mix_backbone.mp3` — musique seule sans voix (reutilisation)

## Transformations par segment
- speed (0.9-1.1) : ralentir / accelerer
- reverse (true/false) : jouer a l'envers
- volume_pct (75-115) : ajuster le volume
- loops (1-4) : repeter le segment
- fade_in_ms (0-300) : fondu d'entree
- fade_out_ms (0-600) : fondu de sortie
- crossfade_ms (15) : fondu entre segments

## Ducking
- 500ms plein volume (hook) avant que la voix commence
- Puis musique baufee de ducking_db (-14dB) sous la voix
- Voix off + SFX par-dessus la musique

## Techno
- Librosa : BPM detection + beat tracking
- Pydub : decoupe + speed + reverse + volume + fades + loops
- FFmpeg : extraction audio + mux final

## Heritage
Adapte depuis SANCTORUM F03_SERAPHIM (seraphim_a.py + seraphim_b.py)
