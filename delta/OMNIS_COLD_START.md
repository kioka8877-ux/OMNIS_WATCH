# OMNIS-WATCH DELTA - COLD START
## Reprendre apres crash sandbox

---

## Procedure

1. **Cloner le repo**
```bash
git clone https://github.com/kioka8877-ux/OMNIS_WATCH.git
cd OMNIS_WATCH
git checkout delta-dev
```

2. **Configurer le token**
```bash
export GH_TOKEN=<votre_token_github>
```

3. **Verifier le ledger**
```bash
cat delta/omnis_ledger.json | python3 -m json.tool
```
Le champ `gate_actuelle` indique ou reprendre.

4. **Reprendre la production**
```bash
cd delta
python OMNIS_EXECUTEUR_DELTA.py --resume
```

---

## Etats possibles du ledger

| gate_actuelle | Action a faire |
|---------------|----------------|
| G1 | Upload URL ou fichier video, configurer D-F00, trigger GitHub Actions |
| G2 | D-F00 termine. Lancer D-F01 (scenes + transcription), puis D-F02 (Oracle + PERTURABO) |
| G3 | D-F02 valide. Trigger D-F03 (reframe) sur GitHub Actions |
| G4 | D-F03 termine. Trigger D-F04 (assembly) sur GitHub Actions |
| CLOSE | Production terminee. Telecharger clips_finaux/ |

---

## En cas de crash

- Le ledger (`omnis_ledger.json`) est la source de verite
- Les artefacts sont dans les dossiers OUT/ de chaque fregate
- Les logs de campagne sont dans `TRACKING/`

**Regle :** Toujours consulter le ledger avant de reprendre. Ne jamais supposer l'etat.
