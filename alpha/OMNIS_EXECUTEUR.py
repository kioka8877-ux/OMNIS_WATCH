"""
OMNIS_EXECUTEUR.py — Orchestrateur OMNIS-WATCH (GitHub Actions Edition)
======================================================================
Sandbox = telecommande + Oracle.
Toutes les fregates tournent sur GitHub Actions.
L'operateur intervient aux 4 gates.

Usage:
  python OMNIS_EXECUTEUR.py --start --title "Mon sujet"
  python OMNIS_EXECUTEUR.py --gate G2    # Telecharge F01, lance F02A/F02B, preview
  python OMNIS_EXECUTEUR.py --gate G3    # Trigger F03A + F03B sur GH Actions
  python OMNIS_EXECUTEUR.py --gate G4    # Telecharge F03, trigger F04 sur GH
  python OMNIS_EXECUTEUR.py --close      # Telecharge artefact final F04
  python OMNIS_EXECUTEUR.py --resume     # Reprendre depuis ledger

Variables d'environnement requises:
  GH_TOKEN — token GitHub (scope: repo)
"""
# A DEVELOPPER — adapte de CRS_EXECUTEUR.py (CRUSADER)
