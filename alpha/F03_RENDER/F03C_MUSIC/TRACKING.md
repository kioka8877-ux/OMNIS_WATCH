# F03C — Journal de Mission

> Fregate F03C — L'Architecte (F03C-A) + La Machine a Micro-jets (F03C-B)
> Pipeline : music.mp3 -> directives.json -> video_with_music.mp4

| Champ | Valeur |
|-------|--------|
| Fregate A | F03C-A — L'Architecte |
| Fregate B | F03C-B — La Machine a Micro-jets |
| Moteur analyse | Librosa (BPM + structure) |
| Moteur decoupe | Pydub (speed, reverse, volume, fades, loops) |
| Ducking | Pydub (hook 500ms + ducking -14dB) |
| Heritage | SANCTORUM F03_SERAPHIM |

## Workflow

1. **F03C-A analyze** : Analyser la musique -> BPM + waveform -> viewer HTML
2. **GATE** : Operateur choisit QUEUE/LOOP/TETE dans le viewer
3. **F03C-A prepare** : Oracle enrichit les segments -> directives.json
4. **GATE** : Operateur valide les directives
5. **F03C-B** : Decoupe + ducking + mix -> video_with_music.mp4
6. **GATE** : Operateur valide le resultat

## Phase : CONSTRUCTION

### [2026-07-20] CONSTRUCTION F03C
- F03C-A : adapte de seraphim_a.py (Librosa + viewer HTML + Oracle sandbox)
- F03C-B : adapte de seraphim_b.py (Pydub + ducking + mux video)
- Workflow GitHub Actions : f03c_music.yml
