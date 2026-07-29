# DELTA - Flotte Clipping (Assaut Viral)
## Vue d'ensemble

> Flotte delta : spcialise dans le clipping automatique longue-video → shorts 9:16 viraux.
> Pipeline : Ingest → Scene Detect → Viral Cut (PERTURABO) → Reframe → Assembly.
> Architecture fretes compartimentes (comme alpha/beta/gamma).

---

## Phases du pipeline

| Gate | Frgate | Action | Output |
|------|--------|--------|--------|
| G1 | D-F00 | Ingest (URL ou upload) | video_source.mp4 |
| G2 | D-F01 | Scene Detect + Transcription | scenes.json + transcript.json |
| G2 | D-F02 | Viral Cut (Oracle + PERTURABO) | cutlist.json |
| G3 | D-F03 | Reframe 9:16 intelligent | clips_reframes/ |
| G4 | D-F04 | Assembly (sous-titres + SFX + loop) | clips_finaux/ |

---

## Fretes

| Frgate | Nom | Techno | Rle |
|--------|-----|--------|-----|
| D-F00 | Ingest | yt-dlp | Porte d'entre : URL YouTube ou upload local |
| D-F01 | Scene Detect | PySceneDetect + faster-whisper | Eyes : coupe en scenes + transcrit mot par mot |
| D-F02 | Viral Cut | Gemini + PERTURABO Bridge | Cerveau : dtecte les moments viraux selon PERTURABO |
| D-F03 | Reframe | MediaPipe + YOLOv8 | Sniper : crop 9:16 dynamique qui suit le sujet |
| D-F04 | Assembly | FFmpeg + whisper subs | Monteur : sous-titres + SFX + loop hook |

---

## Plan d'implmentation (merge → main)

| Ordre | Action | Dtail |
|-------|--------|-------|
| 1 | Crer branche delta-dev | Depuis gamma-dev (he.rite des workflows corrigs) |
| 2 | Crire D-F00 Ingest | omnis_d00_ingest.py + workflow d00_ingest.yml |
| 3 | Crire D-F01 Scene Detect | omnis_d01_scenedetect.py + pyscenedetect install |
| 4 | Crire D-F01 Transcription | omnis_d01_transcribe.py + faster-whisper install |
| 5 | Crire META_D02 + CONTRAT_CLIPPING | Metaprompt Oracle avec PERTURABO Bridge obligatoire |
| 6 | Crire D-F02 Viral Cut | omnis_d02_viralcut.py (prepare + validate) |
| 7 | Crire D-F03 Reframe | omnis_d03_reframe.py + mediapipe + yolov8 |
| 8 | Crire D-F04 Assembly | omnis_d04_assembly.py + sfx + subs + loop |
| 9 | Crire OMNIS_EXECUTEUR_DELTA.py | Orchestrateur G1→G2→G3→G4 |
| 10 | Crer workflows GH Actions delta | d00_ingest.yml, d01_scenedetect.yml, d03_reframe.yml, d04_assembly.yml |
| 11 | Test T1-T6 | Tous les tests de validation |
| 12 | Merge delta-dev → main | Si T1-T6 OK |

---

## Ressources pilles d'OpenShorts

| Techno | Usage dans OpenShorts | Usage dans delta |
|--------|----------------------|-----------------|
| yt-dlp | Ingest via URL | D-F00 Ingest |
| PySceneDetect | Dtection de bornes | D-F01 Scene Detect |
| faster-whisper | Transcription word-level | D-F01 Transcription |
| Gemini | Dtection de moments viraux | D-F02 MAIS bride par PERTURABO |
| MediaPipe | Face tracking reframe | D-F03 Reframe TRACK mode |
| YOLOv8 | Object tracking reframe | D-F03 Reframe TRACK mode |
| FFmpeg cut/subs | Extraction + burn subs | D-F04 Assembly |

---

## Dpendances entre fregates

```
D-F00 (Ingest)
  └──> D-F01 (Scene Detect + Transcribe)
         └──> D-F02 (Viral Cut + PERTURABO)
                └──> D-F03 (Reframe)
                       └──> D-F04 (Assembly)
```

Aucune frgate ne dpare sans que la prcdente ait termin.
