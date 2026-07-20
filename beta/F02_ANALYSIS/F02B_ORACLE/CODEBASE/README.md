# F02B — ORACLE
## Le Createur d'Emotion

## Role
Transforme la description factuelle de F02A en recit emotionnel. Genere le codex.json qui dirige toute la video.

## Entree
- `narrative.txt` (description factuelle de F02A)
- `tracking_data.json` (coordonnees de la cible de F02A)
- `f01_manifest.json` (duree, fps, frames)
- `emotion_mode` (choisi par l'operateur : TRISTE, WHOLESOME, ...)

## Action
1. Lit la description factuelle (la "brouillie" de F02A)
2. Lit le mode emotionnel choisi par l'operateur
3. **Invente** une histoire emotionnelle qui transforme la video brute
4. Genere les textes d'ecran (2-6 mots, 4-6 textes max)
5. Assigne le timing (start_frame / end_frame) — le texte dirige le rythme
6. Assigne les zooms (lents = tristesse, rapides = tension) — suivent les textes
7. Assigne les SFX (keyboard a chaque texte, whoosh sur les zooms) — suivent les textes
8. Assigne la colorimetrie (froid = triste, chaud = wholesome) — suit le mode
9. Assigne les animations de texte (fade lent = triste, typewriter = tension)

## Sortie
- `codex.json` — Le scenario complet qui dirige F03A et F03B

## Le principe
Le texte a l'ecran **dirige la video**. Le timing des textes dicte le rythme.
Les zooms, SFX et couleurs suivent les textes, pas l'inverse.

## Ce que F02B NE fait PAS
- ❌ Voit la video (ca c'est F02A / OpenRouter Vision)
- ❌ Rend la video (ca c'est F03A / Remotion)
- ❌ Mixe le son (ca c'est F03B / Mixer)

## Techno
- Oracle Sandbox (modele IA puissant gratuit du sandbox)
- Metaprompt : `METAPROMPTS/META_F02B_EMOTION.md`

## Runner
Sandbox (l'Oracle est le modele IA du sandbox)

## Heritage
Inspire des metaprompts CRUSADER (META_01_SCRIPT, META_02_VISUELS) mais fondamentalement different :
- CRUSADER : genere un script pour voix off
- OMNIS-WATCH : transforme une video en recit emotionnel via texte a l'ecran
