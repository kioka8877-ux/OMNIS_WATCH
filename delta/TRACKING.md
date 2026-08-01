# DELTA - Flotte Clipping (Assaut Viral)
## Vue d'ensemble

> Flotte delta : spécialise dans le clipping automatique longue-video → shorts 9:16 viraux.
> Pipeline : Ingest → Scene Detect → Viral Cut → Reframe → Timing → Preview → Render → Camouflage → Luther.
> Architecture fretes compartimentées (comme alpha/beta/gamma).
> Utilise les modules de gamma pour F05 (Preview) et F06 (Render).

---

## Phases du pipeline

| Gate | Frgate | Action | Output |
|------|--------|--------|--------|
| G1 | D-F00 | Ingest (URL ou upload) | video_source.mp4 |
| G2 | D-F01 | Scene Detect + Transcription | scenes.json + transcript.json |
| G2 | D-F02 | Viral Cut (PERTURABO) | cutlist.json |
| G3 | D-F03 | Reframe 9:16 intelligent | clips_reframes/clip_001.mp4... |
| G4 | D-F04 | Extract Timing JSON par clip | timing_001.json, timing_002.json... |
| G5 | D-F05 | Preview (codex.json manuel) | TU uploades codex.json via F02_PREVIEW |
| G6 | D-F06 | Render (Remotion + Mixer) | video_complete.mp4 (SFX ajoutés) |
| G7 | D-F07 | Camouflage (re-encode propre) | clips_camoufles/ |
| G8 | D-F08 | Luther (strip metadata) | final_001.mp4, final_002.mp4... |

---

## Fretes

| Frgate | Nom | Techno | Rôle |
|--------|-----|--------|------|
| D-F00 | Ingest | yt-dlp | Porte d'entrée : URL YouTube ou upload local |
| D-F01 | Scene Detect | PySceneDetect + faster-whisper | Eyes : coupe en scenes + transcrit mot par mot |
| D-F02 | Viral Cut | Gemini + PERTURABO Bridge | Cerveau : détecte les moments viraux selon PERTURABO |
| D-F03 | Reframe | MediaPipe + YOLOv8 | Sniper : crop 9:16 dynamique qui suit le sujet |
| D-F04 | Timing | Python | Extract timing.json par clip depuis transcript.json |
| D-F05 | Preview | React (from gamma/F02_PREVIEW) | Interface pour générer codex.json (manuel) |
| D-F06 | Render | Remotion + FFmpeg (from gamma/F03_RENDER) | Rendu avec presets + mix SFX |
| D-F07 | Camouflage | FFmpeg | Re-encode H264 propre, normalise audio |
| D-F08 | Luther | FFmpeg | Strip metadata, efface fingerprint |

---

## Flux de données

```
D-F00 (video_source.mp4)
    ↓
D-F01 (transcript.json + scenes.json)
    ↓
D-F02 (cutlist.json)
    ↓
D-F03 (clips_reframes/clip_001.mp4...)
    ↓
D-F04 (timing_001.json, timing_002.json...)
    ↓
D-F05 (codex_001.json, codex_002.json...) ← TU GÉNÈRES VIA F02_PREVIEW
    ↓
D-F06 (video_complete_001.mp4, video_complete_002.mp4...)
    ↓
D-F07 (clips_camoufles/)
    ↓
D-F08 (final_001.mp4, final_002.mp4...) ✅
```

---

## Modules importés de gamma

| Module gamma | Destination delta | Usage |
|--------------|-------------------|-------|
| gamma/F02_PREVIEW/ | delta/F05_PREVIEW/ | Preview React app → GitHub Pages |
| gamma/F03_RENDER/F03A_REMOTION/ | delta/F06_RENDER/F03A_REMOTION/ | Rendu Remotion |
| gamma/F03_RENDER/F03B_MIXER/ | delta/F06_RENDER/F03B_MIXER/ | Mixeur SFX |
| gamma/SHARED/IN/sfx/ | delta/SHARED/IN/sfx/ | Fichiers SFX (ding, pop, whoosh, keyboard) |

---

## Plan d'implémentation

| Ordre | Action | Détail | Statut |
|-------|--------|--------|--------|
| 1 | Mettre à jour TRACKING.md | Ce document | ✅ FAIT |
| 2 | Créer D-F04 TIMING | extract_timing.py + d04_timing.yml | ✅ FAIT |
| 3 | Copier gamma/F02_PREVIEW → delta/F05_PREVIEW | Preview React app | ⬜ TODO |
| 4 | Créer D-F05 PREVIEW | d05_preview.yml (deploy to GitHub Pages) | ⬜ TODO |
| 5 | Copier gamma/F03_RENDER → delta/F06_RENDER | F03A + F03B | ⬜ TODO |
| 6 | Créer D-F06 RENDER | d06_render.yml (wrapper Remotion + Mixer) | ⬜ TODO |
| 7 | Renommer D-F05 → D-F07 | Camouflage | ⬜ TODO |
| 8 | Renommer D-F06 → D-F08 | Luther | ⬜ TODO |
| 9 | Supprimer D-F04 ASSEMBLY | Obsolète | ⬜ TODO |
| 10 | Créer delta/SHARED/IN/sfx/ | Copier SFX de gamma | ⬜ TODO |
| 11 | Test G5 (boucle par clip) | 3 clips → 3 finals | ⬜ TODO |

---

## Ressources piles d'OpenShorts

| Techno | Usage dans delta |
|--------|------------------|
| yt-dlp | D-F00 Ingest |
| PySceneDetect | D-F01 Scene Detect |
| faster-whisper | D-F01 Transcription |
| Gemini | D-F02 Viral Cut |
| MediaPipe | D-F03 Reframe TRACK mode |
| YOLOv8 | D-F03 Reframe TRACK mode |
| Remotion | D-F06 Render (F03A) |
| FFmpeg | D-F06 Mixer, D-F07, D-F08 |

---

## Dépendances entre fregates

```
D-F00 (Ingest)
  └──> D-F01 (Scene Detect + Transcribe)
         └──> D-F02 (Viral Cut + PERTURABO)
                └──> D-F03 (Reframe)
                       └──> D-F04 (Timing)
                              └──> D-F05 (Preview) ← MANUEL
                                     └──> D-F06 (Render)
                                            └──> D-F07 (Camouflage)
                                                   └──> D-F08 (Luther)
```

Aucune frégate ne démarre sans que la précédente ait terminé (sauf D-F05 = manuel).
