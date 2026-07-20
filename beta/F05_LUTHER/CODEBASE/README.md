# F05 — LUTHER
## Effacement de l'Empreinte Numerique

## Role
Effacement complet et profond de l'empreinte numerique du fichier video.

## Entree
- `youtube_final.mp4` (depuis F04 OUT/)

## Action
1. Strip TOTAL des metadonnees container (title, date, encoder, tout)
2. Stream copy uniquement (`-c copy -map_metadata -1`) — zero re-encode, zero degradation
3. Normalisation du timestamp fichier → date de production
4. Verification post-strip : aucun tag residuel autorise

## Sortie
- `clean_final.mp4` — artefact livrable, empreinte zero

## Techno
- FFmpeg (GitHub Actions)

## Runner
GitHub Actions (CPU gratuit)

## Heritage
**Adapte directement de F05_LUTHER (CRUSADER).**
Le script `crs_f05_luther.py` de CRUSADER est la base de `omnis_f05_luther.py`.
Fonctionnalites reprises :
- Stream copy `-c copy -map_metadata -1`
- Verification des tags suspects (remotion, ffmpeg, lavc, libav, python, claude)
- Normalisation du timestamp fichier

## Statut V1
**HORS SCOPE** — Le dossier est pret mais le code ne sera developpe que dans une phase ulterieure.
F04 (Camouflage) suffit pour la V1.
