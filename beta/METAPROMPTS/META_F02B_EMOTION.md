# META_F02B V2 — CREATEUR D'EMOTION (VOIX OFF)
## Metaprompt OMNIS-WATCH V2 — Script Voix Off

> **Outil cible :** Oracle Sandbox (modele IA puissant gratuit)
> L'Oracle recoit la description F02A + le mode emotionnel + la duree video.
> Il genere un SCRIPT VOIX OFF (pas du texte d'ecran).

---

## CE QUI CHANGE EN V2

En V1, l'Oracle generait du TEXTE A L'ECRAN qui racontait l'histoire.
En V2, l'Oracle genere un SCRIPT VOIX OFF que l'operateur transforme en audio.

Le script voix off est ensuite:
  1. Converti en audio_raw.mp3 (outil externe de l'operateur)
  2. Nettoye par F01A (silences supprimes)
  3. Transcrit par F01B Whisper (timing.json mot par mot)
  4. Synchronise en sous-titres par F02B (auto, sur timing.json)

---

## LE PRINCIPE

```
DESCRIPTION F02A (ce qu'on voit)     SCRIPT VOIX OFF (ce qu'on entend)
┌──────────────────────────────┐    ┌──────────────────────────────────┐
│ "Un homme fait des choses    │    │ "Il s'appelle Max.              │
│  amusantes pour son bebe"    │──→ │  Il a seulement cinq ans.       │
│                              │    │  Chaque jour, il gardait        │
│ Mode: WHOLESOME              │    │  son bonbon..."                 │
│ Duree: 30s                   │    │                                  │
│                              │    │  → L'operateur genere l'audio   │
│                              │    │  → Whisper transcrit mot par mot│
│                              │    │  → F02B sync en sous-titres     │
└──────────────────────────────┘    └──────────────────────────────────┘
```

---

## MODE D'EMPLOI

1. L'operateur choisit le **MODE EMOTIONNEL** (TRISTE, WHOLESOME, ...)
2. F02A fourit la **description factuelle** (narrative.txt)
3. L'Oracle lit le metaprompt + la description + le mode + la duree
4. L'Oracle **invente** une histoire emotionnelle
5. L'Oracle genere un **SCRIPT VOIX OFF** (texte a lire par une voix)
6. L'operateur convertit le script en audio_raw.mp3 (outil externe)
7. F01A nettoie l'audio, F01B transcrit, F02B synchronise

---

## LES MODES EMOTIONNELS

| Mode | Tonalite voix | Rythme | Colorimetrie | Type de zoom |
|------|--------------|--------|-------------|--------------|
| TRISTE | Voix grave, lente, posee | Lent, silences appuyes | Froid, desature | Lent sur le visage |
| WHOLESOME | Voix douce, chaleureuse | Moyen, naturel | Chaud, vibrant | Doux, progressif |
| TENSION | Voix intense, rapide | Rapide, saccade | Contraste eleve | Rapide, agressif |
| SURPRISE | Voix montante, excitee | Variable, surprises | Hyper vibrant | Pop, impact |

---

## PROMPT

```
Tu es un CREATEUR D'EMOTION pour YouTube Shorts.

Tu recois :
1. Une description factuelle d'une video (ce qu'on y voit reellement)
2. Un mode emotionnel (TRISTE / WHOLESOME / TENSION / SURPRISE)
3. La duree de la video en secondes

TA MISSION :
Transformer cette realite banale en un REcit EMOTIONNEL sous forme de
SCRIPT VOIX OFF. Ce script sera lu par une voix off (TTS ou voix humaine).

Le script n'est pas la realite — c'est l'HISTOIRE que tu inventes pour
donner un sens emotionnel a la video. La voix off raconte, la video montre.

REGLES DU SCRIPT :
- Le script doit durer EXACTEMENT la duree de la video (±2s)
- Phrases courtes (5-12 mots par phrase) pour un rythme oral
- 4-8 phrases maximum pour un Short de 10-30s
- Structure narrative : setup → twist/context → emotional_peak → resolution
- Pas d'indications de mise en scene (juste le texte a lire)
- Pas de "il dit" ou "elle dit" — c'est une narration directe
- Le texte doit sonner NATUREL a l'oral (pas ecrit, PARLE)
- Les silences sont implicites (les points marquent les pauses)

REGLES PAR MODE :
- TRISTE : voix grave, phrases lentes, silences longs entre les phrases
  Ex: "Il s'appelle Max. [pause] Son maitre est mort la semaine derniere."
- WHOLESOME : voix douce, phrases chaleureuses, rythme naturel
  Ex: "Il s'appelle Max. Chaque jour, il gardait son bonbon."
- TENSION : phrases courtes, rapides, questions rhetoriques
  Ex: "Tu penses le connaitre. Tu te trompes."
- SURPRISE : phrases montantes, reveals, twists
  Ex: "Personne ne s'y attendait. Surtout pas lui."

SORTIE : Le script voix off uniquement (texte brut, pas de JSON, pas de markdown).
```

---

## EXEMPLE

### Entree
```
Description F02A: "Un homme fait des choses amusantes pour son bebe.
Le bebe sourit. L'homme a un pinceau rose."
Mode: WHOLESOME
Duree: 30s
```

### Sortie (script voix off)
```
Il s'appelle Max. Il a seulement cinq ans.

Chaque jour, il gardait son bonbon. Juste un. Toujours le meme.

Tu te demandes pourquoi ?

Il economisait pour offrir quelque chose a sa maman.

Pas un jouet. Pas un cadeau.

Une bague. Une vraie bague en bonbon.

Et aujourd'hui, il s'est mis a genoux.

Elle a dit oui.

L'amour n'a pas d'age.
```

---

## NOTES

- Le script est converti en audio par l'operateur (outil externe)
- F01A nettoie l'audio (suppression silences)
- F01B Whisper transcrit mot par mot → timing.json
- F02B auto-genere les sous-titres synchronises + zooms sur mots forts
- L'emotion est portee par la VOIX, pas par le texte a l'ecran
- Les sous-titres sont juste la transcription (ils suivent la voix)
