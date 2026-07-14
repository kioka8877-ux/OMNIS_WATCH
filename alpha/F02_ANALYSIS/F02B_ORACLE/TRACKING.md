# F02B ORACLE — Tracking

## Etat
- **Statut :** CODE COMPLETE — TEST SIMULATION OK
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | omnis_f02b_oracle.py developpe | Script prepare/validate complet |
| 2026-07-14 | Simulation test — mode TRISTE | OK — codex valide, 5 textes, 5 zooms, 9 SFX |

## Tests
| # | Date | Mode | Entree | Sortie | Statut |
|---|------|------|--------|--------|--------|
| 1 | 2026-07-14 | TRISTE | narrative.txt (homme+chien parc) + tracking face 11pts | codex.json (5 textes, 5 zooms, 9 SFX) | OK |

## Test 1 — Detail de la simulation

### Brouillie (F02A)
> A man is sitting on a park bench with his dog, a golden retriever. 
> The dog is resting its head on the man's lap. The man is gently petting 
> the dog's head. The park is empty, with autumn leaves on the ground. 
> The man looks down at the dog with a sad expression. The dog looks 
> up at the man. The man stops petting and looks away toward the 
> empty park. The dog stays still, watching him.

### Transformation (F02B — mode TRISTE)
| Frame | Texte | Animation | Emotion | Zoom |
|-------|-------|-----------|---------|------|
| 0-90 | "This is Max." | fade_in | setup | 1.0x |
| 105-225 | "His owner is dying." | typewriter | context | 1.1x → visage |
| 240-330 | "He knows." | fade_in_slow | twist | 1.2x → visage |
| 360-480 | "So he stays." | fade_in_slow | emotional_peak | 1.35x → visage |
| 510-599 | "Until the end." | fade_in_slow | resolution | 1.5x → visage |

### Mecanique emotionnelle
- Setup : texte court, fade rapide, zoom normal → pose le contexte
- Context : typewriter (lettre par lettre = tension qui monte), zoom leger vers le visage
- Twist : "He knows." — 2 mots, fade lent, zoom vers le visage → l'emotion frappe
- Peak : "So he stays." — fade lent, zoom qui se rapproche → poids emotionnel maximum
- Resolution : "Until the end." — texte plus petit, couleur grise, zoom maximum → silence

### SFX
- keyboard a chaque apparition de texte (volume decroissant → de plus en plus silencieux = triste)
- whoosh a chaque zoom (volume qui monte puis redescend = le twist qui frappe puis s'installe)

### Colorimetrie
- cold_desaturated : contrast(0.95) saturate(0.6) brightness(0.9) hue-rotate(-5deg)

### Validation script
- `--prepare` : prompt genere (2980 chars) OK
- `--validate` : codex conforme, 0 erreur OK
- codex.json ecrit dans OUT/ OK

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
| TRISTE | cold_desaturated | TEST OK |
| WHOLESOME | warm_vibrant | CODE COMPLETE (non teste) |
| TENSION | high_contrast | CODE COMPLETE (non teste) |
| SURPRISE | punchy | CODE COMPLETE (non teste) |
| NOSTALGIA | sepia_soft | CODE COMPLETE (non teste) |
