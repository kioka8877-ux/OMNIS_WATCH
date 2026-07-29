# CONTRAT DE CLIPPING - OMNIS-WATCH DELTA
## Schma tactique pour le clipping viral

> Rle : Dit D-F02 exactement quels moments couper et pourquoi.
> PERTURABO = *quoi* raconter (stratgie). Contrat de Clipping = *comment* couper (tactique).

---

## Phase 1 - ANALYSE DE SOURCE

D-F01 fournit :
- `scenes.json` : bornes temporelles de chaque scne
- `transcript.json` : mots + timestamps + confidence

L'Oracle D-F02 lit :
- PERTURABO `shorts_rules.md` + `tim_danilov_rules.md`
- PERTURABO `channel_identity.json` (si chane assigne)
- PERTURABO `skeleton_checklist_short.json`

---

## Phase 2 - DETECTION DE MOMENTS VIRAUX (D-F02)

### Rgle C1 : 3-15 moments max
Ne pas surcharger. Pour une vido de 8min, viser 5-8 moments forts.
Chaque moment = 15-60s.

### Rgle C2 : Hook absolu dans les 3 premires secondes
Le premier moment DIT choisir une scne dont la premire frame :
- Fonctionne SANS SON (Rgle S3 PERTURABO)
- A un mouvement ou une motion forte
- Set UP le payoff (Rgle S2 PERTURABO)

### Rgle C3 : Structure en arche
Les moments doivent suivre une progression :
```
Hook → Contexte → Foreshadow → Escalade → Payoff → Loop
```
Pas de moments jetes au hasard. Chaque moment a un ROLE dans l'arche.

### Rgle C4 : Foreshadow obligatoire
Au moins un moment de type "foreshadow" entre 40-60% de la dure totale.
Ce moment tease le payoff SANS le dvoiler.

### Rgle C5 : Payoff en fin de cutlist
Le dernier moment (ou avant-dernier) doit tre le payoff.
C'est le point d'ancrage de tout le clip. Sans payoff, pas de viralit.

### Rgle C6 : Loop hook si clip >30s
Si un clip fait plus de 30s, un moment "loop" doit reconnecter la fin au dbut.
Callback textuel ou match cut visuel.

---

## Phase 3 - MODE EMOTIONNEL

Chaque moment reoit un mode motionnel qui influence le reframe (D-F03) :

| Mode | Rfrence PERTURABO | Reframe | Timing de coupe |
|------|-------------------|---------|-----------------|
| TRISTE | Cold desaturated | Zoom lent sur visage | Cuts lents, fondus |
| WHOLESOME | Warm vibrant | Zoom doux, couleur chaude | Cuts naturels |
| TENSION | High contrast | Zoom rapide, shake | Cuts brutaux |
| SURPRISE | Punchy | Pop zoom, vif | Cuts instantans |

---

## Phase 4 - EXCLUSIONS

### Moments NE JAMAIS couper :
- Silences prolongs (>3s sans parole ni action)
- Transitions de montage (fondus, cuts noirs)
- Plans sans sous-titre potentiel
- Scnes sans sujet identifiable (ni visage, ni personne, ni objet)

---

## Phase 5 - VALIDATION DE LA CUTLIST

L'Oracle D-F02 vrifie automatiquement :
1. 3-15 moments dans la cutlist ✓
2. Au moins 1 hook dans les 3 premires secondes ✓
3. Structure en arche (Hook→...→Payoff) ✓
4. Au moins 1 foreshadow ✓
5. Payoff en fin de cutlist ✓
6. Loop hook si clip >30s ✓
7. Chaque moment a un mode motionnel ✓
8. Aucune exclusion viole ✓
