# OMNIS_EXECUTEUR_DELTA - Plan d'implementation

## Structure attendue
Identique a gamma/OMNIS_EXECUTEUR.py avec MODE="delta" et ref="delta-dev".

## Commandes

| Commande | Action |
|----------|--------|
| `--start --title "X" --url "Y"` | Initialiser, lancer D-F00 Ingest |
| `--gate G2` | Telecharger D-F00, lancer D-F01 + D-F02 (Oracle PERTURABO) |
| `--gate G3` | Valider cutlist, lancer D-F03 Reframe |
| `--gate G4` | Telecharger D-F03, lancer D-F04 Assembly |
| `--close` | Telecharger clips finaux |
| `--resume` | Reprendre depuis ledger |

## Implementation
Implementer apres que D-F00, D-F01, D-F02, D-F03, D-F04 soient codes.
