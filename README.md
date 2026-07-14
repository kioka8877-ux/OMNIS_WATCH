# OMNIS-WATCH

## Pipeline Automatise de Production Video YouTube Shorts

> *"Vigilance eternal."*

---

## VICTORIA AETERNA

```
[░░░░░░░░░░░░░░░░] CAMP_01 EN COURS — OMNIS-WATCH ALPHA
```

---

## Architecture — Les Fregates

```
SHARED/IN/
 video_raw.mp4
 |
 v
[Gate G1 — operateur : upload, IN/OUT, format, blur-pad, vitesse, volume]
 |
 v
F01 ACQUISITION → video_coupee.mp4 [GitHub Actions — FFmpeg]
 |
 v
F02A VISION → narrative.txt + tracking_data.json [Sandbox Oracle (vision OpenRouter) + GH Actions (MediaPipe)]
 |
 v
F02B ORACLE → codex.json [Sandbox Oracle — Metaprompt emotionnel]
 |
 v
F02 PREVIEW → Apercu temps reel [Sandbox — @remotion/player]
 |
 v
[Gate G2 — operateur : choisit mode emotionnel, valide codex via preview]
 |
 v
F03A REMOTION → video_visuelle.mp4 (sans son) [GitHub Actions — Remotion Docker]
 |
 v
F03B MIXER → video_complete.mp4 [GitHub Actions — FFmpeg SFX]
 |
 v
F04 CAMOUFLAGE → youtube_final.mp4 [GitHub Actions — FFmpeg wipe + loudnorm]
 |
 v
F05 LUTHER → clean_final.mp4 [GitHub Actions — strip empreinte]
 |
 v
[Gate G3/4 — operateur : recupere le .mp4 indetectable, pret pour YouTube]
```

| Fregate | Nom | Role | Runner |
|---------|-----|------|--------|
| F01 | ACQUISITION | FFmpeg coupe + format + blur-pad + vitesse + volume | GitHub Actions |
| F02A | VISION | OpenRouter Vision (description) + MediaPipe (tracking) | Sandbox (vision) + GH Actions (tracking) |
| F02B | ORACLE | Metaprompt emotionnel → codex.json (texte + timing + zooms + SFX + couleurs) | Sandbox Oracle |
| F02 | PREVIEW | Apercu temps reel @remotion/player (validation avant rendu) | Sandbox |
| F03A | REMOTION | Rendu visuel (texte anime, zoom, tracking, colorimetrie) | GitHub Actions (Docker) |
| F03B | MIXER | Mixage SFX (whoosh, keyboard) | GitHub Actions |
| F04 | CAMOUFLAGE | Wipe metadonnees + Loudnorm | GitHub Actions |
| F05 | LUTHER | Effacement complet empreinte numerique | GitHub Actions |

**Doctrine :** Sandbox = telecommande + Oracle IA. GitHub Actions = usine. PC operateur = reception.

---

## Le Metaprompt F02B — Createur d'Emotion

Le coeur d'OMNIS-WATCH n'est pas le decoupage ou le rendu. C'est la **transformation emotionnelle**.

Le metaprompt F02B prend une video brute (ex: un chien qui s'entraine) et la transforme en **recit emotionnel** via le texte a l'ecran :
- Mode **TRISTE** : "Son maitre est mort. Il s'entraine une derniere fois avec lui."
- Mode **WHOLESOME** : "Ce chien a decouvert le bonheur pour la premiere fois."

Le texte a l'ecran **dirige la video**. Le timing des textes dicte le rythme. Les zooms, SFX et couleurs suivent les textes, pas l'inverse.

---

## Pile Technologique

| Composant | Technologie |
|-----------|-------------|
| Decoupe video | FFmpeg (GitHub Actions) |
| Analyse visuelle | OpenRouter Vision (modeles gratuits) |
| Tracking cible | MediaPipe (CPU, GitHub Actions) |
| Generation texte | Oracle Sandbox (metaprompt emotionnel) |
| Preview temps reel | @remotion/player (Vite + React) |
| Rendu visuel | Remotion React/Node.js — Docker custom |
| Mixage SFX | FFmpeg |
| Nettoyage | FFmpeg (CRF18, loudnorm -14 LUFS) |
| Strip metadonnees | FFmpeg `-c copy -map_metadata -1` |
| Orchestration | Python stdlib |

---

## Structure du Repo

```
OMNIS_WATCH/
├── README.md
├── .gitignore
├── TRACKING/
│   ├── OMNIS_CAMPAIGN_LOG.md
│   └── OMNIS_TRANSFER_LOG.md
├── .github/workflows/
│   ├── f01_acquisition.yml
│   ├── f02a_tracking.yml
│   ├── f03a_render.yml
│   ├── f03b_mixer.yml
│   ├── f04_camouflage.yml
│   └── docker-build.yml
└── alpha/
    ├── OMNIS_EXECUTEUR.py
    ├── OMNIS_CUSTOS.py
    ├── OMNIS_COLD_START.md
    ├── omnis_ledger.json
    ├── METAPROMPTS/
    │   └── META_F02B_EMOTION.md
    ├── SHARED/
    │   ├── IN/
    │   │   ├── video_raw.mp4
    │   │   └── sfx/
    │   └── OUT/
    ├── F01_ACQUISITION/
    │   ├── CODEBASE/
    │   ├── IN/
    │   └── OUT/
    ├── F02_ANALYSIS/
    │   ├── F02A_VISION/
    │   │   ├── CODEBASE/
    │   │   ├── IN/
    │   │   └── OUT/
    │   └── F02B_ORACLE/
    │       ├── CODEBASE/
    │       ├── IN/
    │       └── OUT/
    ├── F02_PREVIEW/
    │   ├── src/
    │   └── public/
    ├── F03_RENDER/
    │   ├── F03A_REMOTION/
    │   │   ├── CODEBASE/
    │   │   ├── IN/
    │   │   └── OUT/
    │   └── F03B_MIXER/
    │       ├── CODEBASE/
    │       ├── IN/
    │       └── OUT/
    ├── F04_CAMOUFLAGE/
    │   ├── CODEBASE/
    │   ├── IN/
    │   └── OUT/
    └── F05_LUTHER/
        ├── CODEBASE/
        ├── IN/
        └── OUT/
```

---

## Axiomes

1. **Sandbox = telecommande + Oracle** — Le modele IA du sandbox genere le texte. Zero compute local.
2. **GitHub Actions = usine** — FFmpeg, MediaPipe, Remotion tournent sur CPU gratuit.
3. **OpenRouter = yeux** — Le modele vision gratuit d'OpenRouter decrit la video. L'Oracle ne voit pas.
4. **Le texte dirige tout** — Le timing des textes dicte le rythme, les zooms, les SFX, les couleurs.
5. **Preview avant rendu** — Aucun rendu GitHub Actions sans validation visuelle prealable.
6. **Isolation des fregates** — Chaque fregate lit son IN/, ecrit son OUT/.
7. **Empreinte zero** — F04 + F05 effacent toute trace d'outil avant livraison.
8. **4 gates operateur** — Decisions humaines uniquement aux points de controle.

---

*Nomenclature inspiree du lore Warhammer 40K — Flotte OMNIS-WATCH.*
*Herite du projet CRUSADER (F04 Camouflage + F05 Luther).*
