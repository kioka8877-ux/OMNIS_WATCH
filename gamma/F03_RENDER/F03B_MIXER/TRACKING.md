# F03B MIXER — Tracking

## Etat
- **Statut :** CODE COMPLETE
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | omnis_f03b_mixer.py developpe | Script FFmpeg mixage SFX complet |

## Tests
| # | Date | Video entree | SFX | Sortie | Statut |
|---|------|---------------|-----|--------|--------|
| — | — | — | — | — | EN ATTENTE GH ACTIONS |

## Notes techniques
- Script : omnis_f03b_mixer.py (FONCTIONNEL)
- Runner : GitHub Actions (CPU gratuit)
- Techno : FFmpeg (adelay + amix)
- Entree : video_visuelle.mp4 + codex.json (sfx_timeline) + sfx/
- Sortie : video_complete.mp4

## Processus
1. Lit le codex.json (section sfx_timeline)
2. Pour chaque SFX: calcule timestamp (frame/fps), applique delay + volume
3. Mixe tous les SFX ensemble (amix normalize=0)
4. FFmpeg combine video (copy) + SFX audio (AAC 192k)
5. Si aucun SFX: copie la video telle quelle

## Bibliotheque SFX
| Fichier | Type | Statut |
|---------|------|--------|
| — | — | EN ATTENTE (l'operateur fournira les fichiers) |
