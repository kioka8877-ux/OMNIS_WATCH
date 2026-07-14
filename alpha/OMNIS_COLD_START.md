# OMNIS-WATCH — COLD START
## Reprendre apres crash sandbox

---

## Procedure

1. **Cloner le repo**
```bash
git clone https://github.com/kioka8877-ux/OMNIS_WATCH.git
cd OMNIS_WATCH
```

2. **Configurer le token**
```bash
export GH_TOKEN=<votre_token_github>
```

3. **Verifier le ledger**
```bash
cat alpha/omnis_ledger.json | python3 -m json.tool
```
Le champ `gate_actuelle` indique ou reprendre.

4. **Reprendre la production**
```bash
cd alpha
python OMNIS_EXECUTEUR.py --resume
```

---

## Etats possibles du ledger

| gate_actuelle | Action a faire |
|---------------|----------------|
| G1 | Upload video, configurer F01, trigger GitHub Actions |
| G2 | F01 termine. Lancer F02A (vision + tracking), puis F02B (Oracle), puis preview |
| G3 | F02B valide. Trigger F03A + F03B sur GitHub Actions |
| G4 | F03 termine. Trigger F04 sur GitHub Actions |
| CLOSE | Production terminee. Telecharger clean_final.mp4 |

---

## En cas de crash

- Le ledger (`omnis_ledger.json`) est la source de verite
- Les artefacts sont dans les dossiers OUT/ de chaque fregate
- Les logs de campagne sont dans `TRACKING/OMNIS_CAMPAIGN_LOG.md`
- Les transferts sont logges dans `TRACKING/OMNIS_TRANSFER_LOG.md`

**Regle :** Toujours consulter le ledger avant de reprendre. Ne jamais supposer l'etat.
