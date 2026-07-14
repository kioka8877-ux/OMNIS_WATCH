# F02B ORACLE — Tracking

## Etat
- **Statut :** CODE COMPLETE
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | omnis_f02b_oracle.py developpe | Script prepare/validate complet |

## Tests
| # | Date | Mode | Entree | Sortie | Statut |
|---|------|------|--------|--------|--------|
| — | — | — | — | — | EN ATTENTE |

## Notes techniques
- Script : omnis_f02b_oracle.py (FONCTIONNEL)
- Runner : Sandbox (Oracle = modele IA du sandbox)
- Metaprompt : METAPROMPTS/META_F02B_EMOTION.md
- Entree : narrative.txt + tracking_data.json + f01_manifest.json
- Sortie : codex.json

## Processus F02B
1. `--prepare` : lit les entrees, genere le prompt Oracle, l'affiche
2. L'Oracle (sandbox AI) genere le codex.json base sur le prompt
3. `--validate` : valide le schema du codex, l'ecrit dans OUT/

## Modes emotionnels supportes
| Mode | Colorimetrie | Statut |
|------|-------------|--------|
| TRISTE | cold_desaturated | CODE COMPLETE |
| WHOLESOME | warm_vibrant | CODE COMPLETE |
| TENSION | high_contrast | CODE COMPLETE |
| SURPRISE | punchy | CODE COMPLETE |
| NOSTALGIA | sepia_soft | CODE COMPLETE |

## Validation du codex
- Champs obligatoires verifies
- Timing des textes valide (start < end, end <= total_frames)
- Animations valides (fade_in, fade_in_slow, typewriter, slide_left, slide_right, pop)
- Zooms dans range [1.0, 3.0]
- SFX types valides (whoosh, keyboard, impact, heartbeat)
- Max 8 text_overlays
