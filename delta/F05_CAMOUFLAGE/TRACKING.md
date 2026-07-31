# D-F05 CAMOUFLAGE - Flotte DELTA

## Role
Camouflage : re-encode H264 CRF18 + AAC 192k + loudnorm -14 LUFS + wipe metadonnees.
Herite de F04 Camouflage (CRUSADER).

## Entree
- `IN/clips_finaux/` : clips assemblés par D-F04
- `IN/assembly_manifest.json` : manifeste D-F04 (optionnel)

## Sortie
- `OUT/clips_camoufles/` : clips camouflés
- `OUT/camouflage_manifest.json` : QA + metriques

## Techno
FFmpeg (re-encode)
