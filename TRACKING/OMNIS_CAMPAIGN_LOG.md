# OMNIS-WATCH — CAMPAIGN LOG
## Carnet de Bord de la Flotte

> *"Eternal vigilance is the price of freedom."*

---

## Statut de la Flotte

| Fregate | Nom | Role | Statut | Date de Scellement |
|---------|-----|------|--------|--------------------|
| F01 | ACQUISITION | FFmpeg coupe + format + vitesse + volume | CODE COMPLETE | 2026-07-14 |
| F02A | VISION | OpenRouter Vision (description) + MediaPipe (tracking) | CODE COMPLETE | 2026-07-14 |
| F02B | ORACLE | Metaprompt emotionnel → codex.json | TEST SIMULATION OK | 2026-07-14 |
| F02 | PREVIEW | Apercu temps reel @remotion/player | CODE COMPLETE | 2026-07-14 |
| F03A | REMOTION | Rendu visuel (texte, zoom, tracking, couleurs) | CODE COMPLETE | 2026-07-14 |
| F03B | MIXER | Mixage SFX | CODE COMPLETE | 2026-07-14 |
| F04 | CAMOUFLAGE | Wipe metadonnees + Loudnorm | CODE COMPLETE | 2026-07-14 |
| F05 | LUTHER | Effacement empreinte numerique | HORS SCOPE V1 (heritage CRUSADER) | — |
| META | METAPROMPTS | Guide operateur (emotion) | TEST SIMULATION OK | 2026-07-14 |
| EXEC | OMNIS_EXECUTEUR | Orchestrateur (telecommande) | CODE COMPLETE | 2026-07-14 |
| CUST | OMNIS_CUSTOS | Gardien de flotte (validation) | CODE COMPLETE | 2026-07-14 |

**Compteur de Guerre :**
[███████░░░] 7/8 fregates code complete (F05 hors scope V1)
[█] 1/1 metaprompts — TEST SIMULATION OK
[░░░░] 0/4 gates operateur (tests production en attente)
[██] 2/2 outils orchestration complets (Executeur + Custos)

---

## CAMP_01 — EN COURS — OMNIS-WATCH ALPHA

**2026-07-14 → Initialisation du projet**

### Objectif
Construire le pipeline OMNIS-WATCH de bout en bout :
1. F01 — Decoupe video (FFmpeg) ✅ CODE COMPLETE
2. F02A — Analyse visuelle (OpenRouter + MediaPipe) ✅ CODE COMPLETE
3. F02B — Generation emotionnelle (Oracle sandbox) ✅ CODE COMPLETE
4. F02 PREVIEW — Validation temps reel ✅ CODE COMPLETE
5. F03A — Rendu Remotion ✅ CODE COMPLETE
6. F03B — Mixage SFX ✅ CODE COMPLETE
7. F04 — Camouflage (heritage CRUSADER) ✅ CODE COMPLETE
8. F05 — Luther (plus tard) ⏸️ HORS SCOPE V1

### Heritage CRUSADER
- F04 CAMOUFLAGE : adapte de F04_HELBRECHT (CRUSADER)
- F05 LUTHER : adapte de F05_LUTHER (CRUSADER)
- Structure de repo : inspiree de CRUSADER (mode alpha/beta/gamma)
- Ledger, Executeur, Custos : adaptes de CRUSADER

### Outils d'orchestration
- OMNIS_EXECUTEUR.py : orchestrateur complet (--start, --gate G2/G3/G4, --close, --resume)
- OMNIS_CUSTOS.py : gardien de flotte (validation IN/OUT pour 7 fregates)
- Workflows GitHub Actions : 5 workflows fonctionnels (F01, F02A, F03A, F03B, F04)

---

## F01 — ACQUISITION
- **Status :** CODE COMPLETE
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** video_raw.mp4 + JSON (IN, OUT, format, blur_pad, vitesse, volume)
- **Sortie :** video_coupee.mp4 + f01_manifest.json
- **Role :** Coupe, redimensionne, applique vitesse + volume. Point.
- **Script :** omnis_f01.py (filter_complex blur-pad, setpts+atempo, volume, CRF18)
- **Tests :** EN ATTENTE GitHub Actions (FFmpeg non disponible sandbox)

## F02A — VISION
- **Status :** CODE COMPLETE
- **Techno :** OpenRouter Vision (description) + MediaPipe (tracking)
- **Entree :** video_coupee.mp4 (de F01)
- **Sortie :** narrative.txt (description factuelle) + tracking_data.json (coordonnees cible)
- **Role :** Les yeux. Decrit ce qu'il se passe. Track le visage/main/chien. Ne raconte pas d'histoire.
- **Scripts :** omnis_f02a_vision.py (OpenRouter) + omnis_f02a_track.py (MediaPipe)
- **Tests :** EN ATTENTE (cle OpenRouter + GitHub Actions pour MediaPipe)

## F02B — ORACLE
- **Status :** CODE COMPLETE
- **Techno :** Oracle Sandbox (metaprompt emotionnel)
- **Entree :** narrative.txt + tracking_data.json + emotion_mode (TRISTE/WHOLESOME/...)
- **Sortie :** codex.json (texte + timing + zooms + SFX + couleurs)
- **Role :** Le cerveau. Transforme la realite en recit emotionnel. Le texte dirige la video.
- **Script :** omnis_f02b_oracle.py (--prepare + --validate)
- **Tests :** SIMULATION OK — mode TRISTE, 5 textes, 5 zooms, 9 SFX, codex valide

## F02 PREVIEW
- **Status :** CODE COMPLETE
- **Techno :** @remotion/player (Vite + React)
- **Entree :** codex.json + video_coupee.mp4 + SFX
- **Sortie :** Apercu temps reel dans le navigateur
- **Role :** Filet de securite. L'operateur voit le resultat avant de declencher le rendu.
- **Scripts :** App.jsx (chargement dynamique) + main.jsx + preview/OmniComposition.jsx
- **Tests :** EN ATTENTE (npm install + build)

## F03A — REMOTION
- **Status :** CODE COMPLETE
- **Techno :** Remotion React/Node.js (Docker custom, GitHub Actions)
- **Entree :** codex.json + video_coupee.mp4
- **Sortie :** video_visuelle.mp4 (sans son)
- **Role :** L'usine a effets. Lit le codex, dessine l'image frame par frame.
- **Scripts :** OmniComposition.jsx + Root.jsx + index.jsx + remotion.config.js + Dockerfile
- **Tests :** EN ATTENTE GitHub Actions (npm install + remotion render)

## F03B — MIXER
- **Status :** CODE COMPLETE
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** video_visuelle.mp4 + codex.json (sfx_timeline)
- **Sortie :** video_complete.mp4
- **Role :** Le mixeur son. Injecte les SFX aux bonnes frames.
- **Script :** omnis_f03b_mixer.py (adelay + amix + video copy + AAC)
- **Tests :** EN ATTENTE GitHub Actions (SFX non fournis)

## F04 — CAMOUFLAGE
- **Status :** CODE COMPLETE
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** video_complete.mp4
- **Sortie :** youtube_final.mp4 + rapport_f04.html
- **Role :** Nettoyage de surface. Wipe metadonnees, loudnorm -14 LUFS.
- **Script :** omnis_f04.py (adapte de crs_f04_helbrecht.py CRUSADER)
- **Tests :** EN ATTENTE GitHub Actions

## F05 — LUTHER
- **Status :** HORS SCOPE V1 (heritage CRUSADER)
- **Techno :** FFmpeg (GitHub Actions)
- **Entree :** youtube_final.mp4
- **Sortie :** clean_final.mp4
- **Role :** Effacement profond de l'empreinte numerique. Re-encode agressif.

---

## METAPROMPTS
- META_F02B_EMOTION.md — Createur d'emotion (TRISTE / WHOLESOME / TENSION / SURPRISE / NOSTALGIA)
- Statut: CODE COMPLETE

---

## Prochaine etape : TEST DE PRODUCTION
1. Fournir une video de test (SHARED/IN/video_raw.mp4)
2. Configurer cle OpenRouter (secret GitHub OPENROUTER_API_KEY)
3. Fournir fichiers SFX (SHARED/IN/sfx/whoosh.mp3, keyboard.mp3)
4. Lancer: python OMNIS_EXECUTEUR.py --start --title "Test production"
