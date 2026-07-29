# D-F02 VIRAL CUT - Tracking

## Statut
- **Statut :** PLANIFI
- **Version :** delta
- **Priorit :** tape 4

## Rle
Le cerveau de la flotte. L'Oracle (sandbox IA) lit les scenes + transcript + PERTURABO rules
et identifie 3-15 moments viraux. Chaque moment est justifi par une rgle PERTURABO.

## Flow
```
scenes.json + transcript.json de D-F01
PERTURABO rules (fetch depuis GitHub raw)
    ↓
D-F02 --prepare: gnre le prompt Oracle
Oracle gnre cutlist.json selon PERTURABO
D-F02 --validate: vrifie la cutlist
    ↓
OUT/cutlist.json (3-15 moments viraux)
    ↓
D-F03 prend le relais
```

## Entres
- `IN/scenes.json`
- `IN/transcript.json`
- PERTURABO rules (fetch runtime depuis GitHub)

## PERTURABO Bridge (OBLIGATOIRE)
Avant de gnrer la cutlist, l'Oracle DOIT fetch :
1. `shorts_rules.md` — Rgles S1-S18 (Hook→Explain Payoff→Foreshadow→Reveal)
2. `tim_danilov_rules.md` — Rgles 1-6 (Niche bending, squelette avant script)
3. `channel_identity.json` — Si chane assigne, identit de la chane
4. `skeleton_checklist_short.json` — Les 7 lments du squelette viral

Les rgles sont appliques sur la cutlist :
- **Rgle S1** : Hook → Explain Payoff → Foreshadow Payoff → Reveal Payoff (structure)
- **Rgle S3** : Le hook visuel doit fonctionner sans son
- **Rgle S4** : Loop hook obligatoire (fin reconnecte au dbut)
- **Rgle 4 Tim Danilov** : Squelette avant script — la cutlist respecte le moule viral

## Sorties
- `OUT/cutlist.json` : tableau de 3-15 moments, chaque avec :
  - `scene_index` : index dans scenes.json
  - `start_sec` : timestamp IN
  - `end_sec` : timestamp OUT
  - `viral_type` : hook / context / foreshadow / payoff / loop
  - `perturabo_rule` : rgles PERTURABO qui justifient ce moment
  - `emotion_mode` : triste / wholesome / tension / surprise
  - `hook_summary` : texte court qui raconte le hook

## Code
- Script : `CODEBASE/omnis_d02_viralcut.py` (non cr) — modes prepare + validate
- Metaprompt : `METAPROMPTS/META_D02_VIRALCUT.md` (non cr)
- Contrat : `METAPROMPTS/CONTRAT_CLIPPING.md`
- Runner : Sandbox (Oracle = modle IA du sandbox)

## Tests de validation (T3)
| # | Entre | Attendu | Statut |
|---|-------|---------|--------|
| T3.1 | scenes.json + transcript + PERTURABO | cutlist.json avec 3-10 moments | EN ATTENTE CODE |
| T3.2 | Chaque moment justifi par une rgle PERTURABO | Tous les champs viral_type et perturabo_rule remplis | EN ATTENTE CODE |
| T3.3 | Loop hook prsent si vido >30s | Un moment de type "loop" en fin de cutlist | EN ATTENTE CODE |
