# D-F06 LUTHER - Flotte DELTA

## Role
Effacement complet de l'empreinte numerique : stream copy, strip metadonnees, normalisation timestamp.
Herite de F05 Luther (CRUSADER).

## Entree
- `IN/clips_camoufles/` : clips issus de D-F05
- `IN/camouflage_manifest.json` : manifeste D-F05 (optionnel)

## Sortie
- `OUT/clips_finaux/` : clips finaux nettoyés
- `OUT/luther_manifest.json` : QA + metriques

## Techno
FFmpeg (stream copy)
