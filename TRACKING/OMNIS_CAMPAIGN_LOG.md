# OMNIS-WATCH — CAMPAIGN LOG
## Carnet de Bord de la Flotte

> *"Eternal vigilance is the price of freedom."*

---

## Statut de la Flotte

| Fregate | Nom | Role | Statut | Date de Scellement |
|---------|-----|------|--------|--------------------|
| F01 | ACQUISITION | FFmpeg coupe + format + vitesse + volume | CODE COMPLETE | 2026-07-14 |
| F02A | VISION | OpenRouter Vision (description) + MediaPipe (tracking) | CODE COMPLETE | 2026-07-14 |
| F02B | ORACLE | Metaprompt emotionnel → codex.json | CODE COMPLETE | 2026-07-14 |
| F02 | PREVIEW | Apercu temps reel @remotion/player | EN DEVELOPPEMENT | — |
| F03A | REMOTION | Rendu visuel (texte, zoom, tracking, couleurs) | EN DEVELOPPEMENT | — |
| F03B | MIXER | Mixage SFX | CODE COMPLETE | 2026-07-14 |
| F04 | CAMOUFLAGE | Wipe metadonnees + Loudnorm | EN DEVELOPPEMENT (heritage CRUSADER) | — |
| F05 | LUTHER | Effacement empreinte numerique | HORS SCOPE V1 (heritage CRUSADER) | — |
| META | METAPROMPTS | Guide operateur (emotion) | EN DEVELOPPEMENT | — |

**Compteur de Guerre :**
[▓░░░░░░░░░] 1/8 (code complete, tests GH Actions) fregates scellees
[░] 0/1 metaprompts scelles
[░░░░] 0/4 gates operateur

---

## CAMP_01 — EN COURS — OMNIS-WATCH ALPHA

**2026-07-14 → Initialisation du projet**

### Objectif
Construire le pipeline OMNIS-WATCH de bout en bout :
1. F01 — Decoupe video (FFmpeg)
2. F02A — Analyse visuelle (OpenRouter + MediaPipe)
3. F02B — Generation emotionnelle (Oracle sandbox)
4. F02 PREVIEW — Validation temps reel
5. F03A — Rendu Remotion
6. F03B — Mixage SFX
7. F04 — Camouflage (heritage CRUSADER)
8. F05 — Luther (plus tard)

### Heritage CRUSADER
- F04 CAMOUFLAGE : adapte de F04_HELBRECHT (CRUSADER)
- F05 LUTHER : adapte de F05_LUTHER (CRUSADER)
- Structure de repo : inspiree de CRUSADER (mode alpha/beta/gamma)
- Ledger, Executeur, Custos : adaptes de CRUSADER

---

## F01 — ACQUISITION
- **Status :** EN DEVELOPPEMENT
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** video_raw.mp4 + JSON (IN, OUT, format, blur_pad, vitesse, volume)
- **Sortie :** video_coupee.mp4 + f01_manifest.json
- **Role :** Coupe, redimensionne, applique vitesse + volume. Point.

## F02A — VISION
- **Status :** EN DEVELOPPEMENT
- **Techno :** OpenRouter Vision (description) + MediaPipe (tracking)
- **Entree :** video_coupee.mp4 (de F01)
- **Sortie :** narrative.txt (description factuelle) + tracking_data.json (coordonnees cible)
- **Role :** Les yeux. Decrit ce qu'il se passe. Track le visage/main/chien. Ne raconte pas d'histoire.

## F02B — ORACLE
- **Status :** EN DEVELOPPEMENT
- **Techno :** Oracle Sandbox (metaprompt emotionnel)
- **Entree :** narrative.txt + tracking_data.json + emotion_mode (TRISTE/WHOLESOME/...)
- **Sortie :** codex.json (texte + timing + zooms + SFX + couleurs)
- **Role :** Le cerveau. Transforme la realite en recit emotionnel. Le texte dirige la video.

## F02 PREVIEW
- **Status :** EN DEVELOPPEMENT
- **Techno :** @remotion/player (Vite + React)
- **Entree :** codex.json + video_coupee.mp4 + SFX
- **Sortie :** Apercu temps reel dans le navigateur
- **Role :** Filet de securite. L'operateur voit le resultat avant de declencher le rendu.

## F03A — REMOTION
- **Status :** EN DEVELOPPEMENT
- **Techno :** Remotion React/Node.js (Docker custom, GitHub Actions)
- **Entree :** codex.json + video_coupee.mp4
- **Sortie :** video_visuelle.mp4 (sans son)
- **Role :** L'usine a effets. Lit le codex, dessine l'image frame par frame.

## F03B — MIXER
- **Status :** EN DEVELOPPEMENT
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** video_visuelle.mp4 + codex.json (sfx_timeline)
- **Sortie :** video_complete.mp4
- **Role :** Le mixeur son. Injecte les SFX aux bonnes frames.

## F04 — CAMOUFLAGE
- **Status :** EN DEVELOPPEMENT (heritage CRUSADER)
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** video_complete.mp4
- **Sortie :** youtube_final.mp4
- **Role :** Nettoyage de surface. Wipe metadonnees, loudnorm -14 LUFS.

## F05 — LUTHER
- **Status :** HORS SCOPE V1 (heritage CRUSADER)
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** youtube_final.mp4
- **Sortie :** clean_final.mp4
- **Role :** Effacement profond de l'empreinte numerique. Re-encode agressif.

---

## METAPROMPTS
- META_F02B_EMOTION.md — Createur d'emotion (TRISTE / WHOLESOME / ...)
- Statut: EN DEVELOPPEMENT
