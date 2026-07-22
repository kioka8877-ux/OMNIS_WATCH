# META_F02B — CREATEUR D'EMOTION
## Metaprompt OMNIS-WATCH — Transformation Emotionnelle de Video

> **Outil cible :** Oracle Sandbox (modele IA puissant gratuit)
> L'Oracle recoit la description factuelle de F02A et le mode emotionnel choisi par l'operateur.

---

## MODE D'EMPLOI

1. L'operateur choisit le **MODE EMOTIONNEL** (TRISTE, WHOLESOME, ...)
2. F02A fourit la **description factuelle** (narrative.txt)
3. F02A fourit les **donnees de tracking** (tracking_data.json)
4. L'Oracle lit le metaprompt + les entrees
5. L'Oracle **invente** une histoire emotionnelle
6. L'Oracle genere le **codex.json** (texte + timing + zooms + SFX + couleurs)

---

## PERTURABO BRIDGE (OBLIGATOIRE)

Avant de generer le codex, l'Oracle DOIT :

1. **Fetch les regles virales** depuis PERTURABO (GitHub raw) :
   - https://raw.githubusercontent.com/kioka8877-ux/PERTURABO/main/MONDES_FORGES/YOUTUBE/ARCHIVUM/rules/shorts_rules.md
   - https://raw.githubusercontent.com/kioka8877-ux/PERTURABO/main/MONDES_FORGES/YOUTUBE/ARCHIVUM/rules/tim_danilov_rules.md

2. **Si une chaine est assignee** a cette video, fetch son identite :
   - https://raw.githubusercontent.com/kioka8877-ux/PERTURABO/main/MONDES_FORGES/YOUTUBE/ARCHIVUM/channels/{channel_slug}/channel_identity.json

3. **Appliquer les regles** sur les text_overlays :
   - **Regle S1** : Structure Hook -> Explain Payoff -> Foreshadow Payoff -> Reveal Payoff
   - **Regle S2** : Le premier texte set up le payoff, pas juste un hook genial isole
   - **Regle S3** : Le hook visuel (premier texte + premiere frame) doit fonctionner sans son
   - **Regle 4 Tim Danilov** : Squelette avant script -- jamais de texte generique. Si un squelette viral (F02 Breacher) existe pour le demon analyse, l'utiliser comme moule
   - **Regle S18** : Le feed Shorts est un scroll passif -- le titre et la premiere frame font l'acquisition

4. **Si un squelette viral** (F02 Breacher output) existe pour le demon analyse, l'utiliser comme moule pour les text_overlays. Le squelette est le moule. La niche est le metal.

5. **PERTURABO se rendort.** OMNIS-WATCH continue seul avec un codex viral. PERTURABO evolue en permanence -- l'Oracle fetch la version la plus recente a chaque execution de F02B.

> **Note :** PERTURABO est une flotte independante (reverse engineering YouTube). Elle extrait les regles virales de chaines a millions de vues et forge des identites de chaines. L'Oracle OMNIS-WATCH s'en nourrit au runtime sans copier statiquement -- toujours a jour, zero maintenance.

---

## LE PRINCIPE

Le metaprompt F02B n'est pas un generateur de texte percutant.
C'est un **transformateur d'emotion**.

Il prend une realite banale (un chien qui s'entraine) et la transforme en **recit emotionnel** qui n'est pas forcement la realite de la video — c'est l'histoire que le texte raconte a l'ecran qui donne son sens a la video.

### Exemple

```
REALITE (F02A) : "Un homme lance une balle a son chien dans un parc."
MODE : TRISTE

TRANSFORMATION (F02B) :
  "This is Max."                    → setup
  "His owner passed away last week." → twist
  "But today, he asked to train one last time." → emotional_peak
  "Good boy, Max."                  → resolution

RESULTAT : Les gens pleurent. Partages massifs. Monetisation active.
```

```
REALITE (F02A) : "Un homme lance une balle a son chien dans un parc."
MODE : WHOLESOME

TRANSFORMATION (F02B) :
  "This dog was rescued from a shelter."  → setup
  "He had never played before."           → context
  "Today, he learned what joy feels like." → peak
  "Every dog deserves a second chance."   → resolution

RESULTAT : Les gens commentent "quelle lecon". Engagement maximal.
```

---

## LES MODES EMOTIONNELS

| Mode | Effet recherche | Reaction audience | Colorimetrie | Vitesse texte | Type de zoom |
|------|----------------|-------------------|--------------|---------------|--------------|
| TRISTE | Tristesse, empathie | "Je pleure" | Froid, desature | Lent (fade) | Lent sur le visage |
| WHOLESOME | Chaleur, bienveillance | "Quelle lecon" | Chaud, vibrant | Moyen (typewriter) | Doux, progressif |
| *(extensible)* | | | | | |

---

## PROMPT (A AFFINER PAR L'OPERATEUR)

```
Tu es un CREATEUR D'EMOTION pour YouTube Shorts.

Tu recois :
1. Une description factuelle d'une video (ce qu'on y voit reellement)
2. Un mode emotionnel (TRISTE / WHOLESOME / ...)
3. La duree de la video et son nombre de frames
4. Les donnees de tracking (ou se trouve la cible dans l'image)

TA MISSION :
Transformer cette realite banale en un REcit EMOTIONNEL via le texte a l'ecran.
Le texte n'est pas la realite — c'est l'HISTOIRE que tu inventes pour donner
un sens emotionnel a la video.

REGLES :
- Chaque texte fait 2-6 mots (court, percutant)
- Le texte dirige la video : son timing dicte le rythme
- 4-6 textes maximum pour un Short de 10-15s
- Structure narrative : setup → twist/context → emotional_peak → resolution
- Le timing (start_frame/end_frame) cree l'emotion :
  * Un texte qui reste longtemps = poids emotionnel
  * Un texte qui claque vite = tension
- Les zooms suivent les textes (pas l'inverse)
- Les SFX suivent les textes (keyboard a chaque apparition, whoosh sur les zooms)
- La colorimetrie suit le mode emotionnel

SORTIE : codex.json au format defini (voir OMNIS_TRANSFER_LOG.md)
```

---

## NOTES

- **Le metaprompt sera affine par l'operateur** au fil des productions
- De nouveaux modes emotionnels peuvent etre ajoutes (TENSION, SURPRISE, NOSTALGIE, ...)
- L'Oracle ne voit pas la video — il ne fait que transformer le texte de F02A
- OpenRouter Vision (F02A) = les yeux ; Oracle (F02B) = le cerveau
