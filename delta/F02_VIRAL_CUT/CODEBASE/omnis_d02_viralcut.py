"""
omnis_d02_viralcut.py - D-F02 VIRAL CUT
=======================================
L'Oracle identifie les moments viraux selon PERTURABO.
Modes: --prepare (genere le prompt Oracle) + --validate (valide la cutlist)

Usage:
  python omnis_d02_viralcut.py --input /path/IN/ --output /path/OUT/ --prepare
  python omnis_d02_viralcut.py --input /path/IN/ --output /path/OUT/ --validate cutlist_genere.json

Entree: scenes.json + transcript.json (de D-F01)
Sortie: cutlist.json (3-15 moments viraux justifies par PERTURABO)
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests


PERTURABO_BASE = "https://raw.githubusercontent.com/kioka8877-ux/PERTURABO/main/MONDES_FORGES/YOUTUBE/ARCHIVUM"
RULES_SHORTS = f"{PERTURABO_BASE}/rules/shorts_rules.md"
RULES_TIM = f"{PERTURABO_BASE}/rules/tim_danilov_rules.md"
SKELETON_CHECKLIST = "https://raw.githubusercontent.com/kioka8877-ux/PERTURABO/main/MONDES_FORGES/YOUTUBE/CONTRACTS/skeleton_checklist_short.json"

SCENES_FILENAME = "scenes.json"
TRANSCRIPT_FILENAME = "transcript.json"
OUTPUT_FILENAME = "cutlist.json"
PROMPT_FILENAME = "oracle_prompt.txt"


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def fetch_perturabo(url):
    """Fetch un fichier depuis PERTURABO (GitHub raw)."""
    try:
        resp = requests.get(url, headers={"User-Agent": "OMNIS-Delta"}, timeout=30)
        if resp.status_code == 200:
            return resp.text
        log_fail(f"Erreur fetch PERTURABO: {url} - {resp.status_code}")
        return ""
    except Exception as e:
        log_fail(f"Erreur fetch PERTURABO: {url} - {e}")
        return ""


def fetch_channel_identity(channel_slug):
    """Fetch l'identite de chane si assignee."""
    if not channel_slug:
        return ""
    url = f"{PERTURABO_BASE}/channels/{channel_slug}/channel_identity.json"
    return fetch_perturabo(url)


def call_oracle(prompt_text, api_key, model="openai/gpt-4o", base_url="https://openrouter.ai/api/v1"):
    log_info(f"Appel Oracle ({base_url} / {model})...")
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es VIRAL CUT DETECTOR pour YouTube Shorts. Genere UNIQUEMENT du JSON valide, rien d autre."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.3,
        "max_tokens": int(os.environ.get("ORACLE_MAX_TOKENS", "4096")),
        "response_format": {"type": "json_object"}
    }
    try:
        last_err = ""
        for attempt in range(3):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=120)
                if resp.status_code != 200:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                else:
                    result = resp.json()
                    raw = result["choices"][0]["message"]["content"]
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
                    if json_match:
                        raw_json = json_match.group(1)
                    else:
                        raw_json = raw.strip()
                    return json.loads(raw_json)
            except Exception as e:
                last_err = str(e)
            log_fail(f"Oracle tentative {attempt + 1}/3 echouee: {last_err} - retry dans 10s")
            time.sleep(10)
        log_fail(f"Oracle call failed apres 3 tentatives: {last_err}")
        return None
    except Exception as e:
        log_fail(f"Oracle call failed: {e}")
        return None

def run_oracle(input_dir, output_dir, clip_count=5, clip_max_duration=60, channel_slug=None, model=None, window_sec=360):
    api_key = os.environ.get("ORACLE_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        log_fail("ORACLE_API_KEY (ou OPENROUTER_API_KEY) non definie dans l environnement")
        sys.exit(1)
    base_url = os.environ.get("ORACLE_BASE_URL", "https://openrouter.ai/api/v1")
    if not model:
        model = os.environ.get("ORACLE_MODEL", "openai/gpt-4o")
    prepare_prompt(input_dir, output_dir, channel_slug, clip_count, clip_max_duration, window_sec)
    prompt_path = output_dir / PROMPT_FILENAME
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()
    cutlist = None
    for attempt in range(3):
        cutlist = call_oracle(prompt_text, api_key, model, base_url)
        if not cutlist:
            continue
        cutlist_path = output_dir / OUTPUT_FILENAME
        with open(cutlist_path, "w", encoding="utf-8") as f:
            json.dump(cutlist, f, ensure_ascii=False, indent=2)
        log_ok(f"Cutlist generee par Oracle: {cutlist_path}")
        try:
            validate_cutlist(input_dir, output_dir, OUTPUT_FILENAME, clip_max_duration)
            break
        except SystemExit:
            log_fail(f"Cutlist invalide (tentative {attempt + 1}/3) - nouvel appel Oracle dans 10s")
            time.sleep(10)
    else:
        sys.exit(1)

def prepare_prompt(input_dir, output_dir, channel_slug=None, clip_count=5, clip_max_duration=60, window_sec=360):
    """Genere le prompt pour l'Oracle (sandbox)."""
    section("D-F02 PREPARE - Generation du prompt Oracle")
    log_info(f"Parametres operateur: {clip_count} clips, max {clip_max_duration}s, fenetre {window_sec}s")

    scenes_path = input_dir / SCENES_FILENAME
    transcript_path = input_dir / TRANSCRIPT_FILENAME

    if not scenes_path.exists():
        log_fail(f"scenes.json introuvable: {scenes_path}")
        sys.exit(1)
    if not transcript_path.exists():
        log_fail(f"transcript.json introuvable: {transcript_path}")
        sys.exit(1)

    with open(scenes_path, "r", encoding="utf-8") as f:
        scenes_data = json.load(f)
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)

    scenes_all = scenes_data.get("scenes", [])
    words_all = transcript_data.get("words", [])

    scenes_in_window = [s for s in scenes_all if s["start_sec"] <= window_sec]
    words_in_window = [w for w in words_all if w["start"] <= window_sec]

    max_prompt_words = int(os.environ.get("ORACLE_MAX_PROMPT_WORDS", "800"))
    if len(words_in_window) > max_prompt_words:
        step = len(words_in_window) / max_prompt_words
        words_in_window = [words_in_window[int(i * step)] for i in range(max_prompt_words)]
        log_info(f"Transcript sous-echantillonne a {max_prompt_words} mots (fenetre {window_sec}s)")

    log_ok(f"Scenes: {len(scenes_in_window)}/{len(scenes_all)} dans la fenetre {window_sec}s")
    log_ok(f"Transcript: {len(words_in_window)}/{len(words_all)} mots dans la fenetre {window_sec}s")

    section("PERTURABO Bridge - Fetch regles")
    shorts_rules = fetch_perturabo(RULES_SHORTS)
    tim_rules = fetch_perturabo(RULES_TIM)
    skeleton = fetch_perturabo(SKELETON_CHECKLIST)
    channel_id = fetch_channel_identity(channel_slug) if channel_slug else "(aucune chane assignee)"

    log_ok("Regles PERTURABO recuperees")

    scenes_summary = json.dumps(scenes_in_window, ensure_ascii=False, indent=2)
    transcript_compact = " ".join(
        f"{w['start']}:{w['word']}" for w in words_in_window
    )

    prompt = f"""# MISSION D-F02 - VIRAL CUT DETECTOR

## PERTURABO REGLES (OBLIGATOIRE - appliquer sur la cutlist)

### SHORTS RULES:
{shorts_rules[:3000]}

### TIM DANILOV RULES:
{tim_rules[:3000]}

### SKELETON CHECKLIST:
{skeleton[:2000]}

### CHANNEL IDENTITY:
{channel_id[:1000] if channel_id else "(aucune)"}

## DONNEES SOURCE

### SCENES ({len(scenes_in_window)}/{len(scenes_all)} scenes, fenetre {window_sec}s):
{scenes_summary}

### TRANSCRIPT ({len(words_in_window)}/{len(words_all)} mots, langue={transcript_data.get('language', '?')}, format start_sec:mot):
{transcript_compact}

## MISSION:
Tu es un VIRAL CUT DETECTOR pour YouTube Shorts.
Identifie les {clip_count} MEILLEURS fenetres de cette video qui deviendront des Shorts viraux COMPLETS.
CHAQUE clip est un Short autonome qui doit respecter LA FORMULE S1: Hook -> Explain Payoff -> Foreshadow Payoff -> Reveal Payoff (+ Loop).

CRITERES DE SELECTION D'UNE FENETRE (par ordre de priorite):
1. La fenetre contient un payoff identifiable et satisfaisant (Regle S1)
2. La fenetre commence par un hook visuel fort fonctionnant SANS SON (Regle S3)
3. Le hook cree un vide cognitif ET prepare le payoff (Regle S2)
4. Emotion : le moment est emotionnellement fort
5. Sujet : visage ou personne identifiable pour le reframe

REGLES DE SORTIE:
- EXACTEMENT {clip_count} clips (ni plus, ni moins), ordre chronologique
- Chaque clip = 10-{clip_max_duration}s
- CHAQUE clip contient SA PROPRE structure interne (la formule S1 complete) :
  - visual_hook_frame : premiere frame 0-0.5s, stoppe le scroll SANS SON (S3)
  - verbal_text_hook : 0-3s, phrase qui cree un vide cognitif ET set up le payoff (S2)
  - context : 3-10s, contexte rapide, pas de temps mort
  - foreshadow : integre au hook ou juste apres, le viewer sait ce qu'il va gagner
  - escalade_rythme : milieu, chaque seconde = info nouvelle, pas de sag
  - payoff : 3-5s avant la fin, repond au hook, satisfaction maximale
  - loop_hook : derniere seconde, reconnecte au debut (S4), 2+ techniques combinees
- Les sous-moments sont des fenetres RELATIVES au debut du clip (relative_start_sec/relative_end_sec)
- **IMPORTANT - ADAPTATION A LA DUREE DU CLIP : les fenetres relatives doivent etre ADAPTEES a la duree reelle du clip (duration_sec), PAS au modele 30s. Regle stricte : payoff.relative_end_sec doit etre >= duration_sec - 5, loop_hook.relative_start_sec doit etre >= duration_sec - 3, et loop_hook.relative_end_sec = duration_sec. Si le clip dure 41s, le payoff finit vers 36-40s et le loop vers 39-41s, jamais vers 29s.**
- Chaque sous-moment a une description courte (MAX 15 mots) et un mode emotionnel (triste/wholesome/tension/surprise)
- phrase_exacte = MAX 12 mots, vide_cognitif = MAX 10 mots, setup_du_payoff = MAX 10 mots

FORMAT DE SORTIE (JSON valide uniquement):
```json
{{
  "video_duration_sec": 0,
  "clip_count": 0,
  "clips": [
    {{
      "index": 0,
      "start_sec": 0,
      "end_sec": 0,
      "duration_sec": 0,
      "scene_source": 0,
      "emotion_mode": "triste|wholesome|tension|surprise",
      "viral_angle": "Description de l'angle viral (2-10 mots)",
      "structure": {{
        "visual_hook_frame": {{"relative_start_sec": 0, "relative_end_sec": 0.5, "description": "...", "emotion_mode": "..."}},
        "verbal_text_hook": {{"relative_start_sec": 0, "relative_end_sec": 3, "phrase_exacte": "...", "vide_cognitif": "...", "setup_du_payoff": "..."}},
        "context": {{"relative_start_sec": 3, "relative_end_sec": 10, "description": "..."}},
        "foreshadow": {{"relative_start_sec": 0, "relative_end_sec": 5, "description": "...", "force": "faible|moyen|eleve"}},
        "escalade_rythme": {{"relative_start_sec": 10, "relative_end_sec": 25, "description": "..."}},
        "payoff": {{"relative_start_sec": 25, "relative_end_sec": 29, "phrase_exacte": "...", "satisfaction_cible": "...", "reponse_au_hook": "..."}},
        "loop_hook": {{"relative_start_sec": 29, "relative_end_sec": 30, "techniques": ["callback_hook|visual_match_cut|audio_continuity|cliffhanger_reversal|open_question_close"], "description": "..."}}
      }}
    }}
  ]
}}
```
Aucun texte avant ou apres le JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / PROMPT_FILENAME
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    log_ok(f"Prompt Oracle genere: {prompt_path}")
    print()
    print("L'Oracle (sandbox) genere maintenant cutlist.json base sur ce prompt.")
    print(f"Enregistrez le resultat dans: {output_dir / OUTPUT_FILENAME}")
    print(f"Puis validez: python omnis_d02_viralcut.py --input {input_dir} --output {output_dir} --validate cutlist.json")


def validate_cutlist(input_dir, output_dir, cutlist_file, clip_max_duration=60):
    """Valide le schema de la cutlistgeneree par l'Oracle."""
    section("D-F02 VALIDATE - Verification cutlist")

    cutlist_path = output_dir / cutlist_file
    if not cutlist_path.exists():
        cutlist_path = input_dir / cutlist_file
    if not cutlist_path.exists():
        log_fail(f"Cutlist introuvable: {cutlist_file}")
        sys.exit(1)

    with open(cutlist_path, "r", encoding="utf-8") as f:
        cutlist = json.load(f)

    errors = []

    clips = cutlist.get("clips", [])
    if not clips:
        errors.append("Aucun clip dans la cutlist")
    if len(clips) < 1:
        errors.append(f"Trop peu de clips: {len(clips)} (min 1)")
    if len(clips) > 10:
        errors.append(f"Trop de clips: {len(clips)} (max 10)")

    STRUCTURE_KEYS = ["visual_hook_frame", "verbal_text_hook", "context", "foreshadow", "escalade_rythme", "payoff", "loop_hook"]

    for i, c in enumerate(clips):
        dur = c.get("duration_sec", 0)
        if dur < 10 or dur > clip_max_duration:
            errors.append(f"Clip {i}: duree {dur}s hors plage (10-{clip_max_duration}s)")
        if not c.get("emotion_mode"):
            errors.append(f"Clip {i}: pas de mode emotionnel")
        if not c.get("viral_angle"):
            errors.append(f"Clip {i}: pas d'angle viral")
        start, end = c.get("start_sec", 0), c.get("end_sec", 0)
        if end <= start:
            errors.append(f"Clip {i}: fenetre invalide ({start}-{end}s)")

        structure = c.get("structure", {})
        for key in STRUCTURE_KEYS:
            if key not in structure:
                errors.append(f"Clip {i}: element de structure manquant: {key}")
        if structure:
            vhf = structure.get("visual_hook_frame", {})
            if vhf.get("relative_start_sec", -1) != 0:
                errors.append(f"Clip {i}: visual_hook_frame doit commencer a 0s")
            vth = structure.get("verbal_text_hook", {})
            if vth.get("relative_start_sec", 99) > 1:
                errors.append(f"Clip {i}: verbal_text_hook doit demarrer dans la 1ere seconde")
            ctx = structure.get("context", {})
            if ctx.get("relative_start_sec", 99) < vth.get("relative_start_sec", 0):
                errors.append(f"Clip {i}: context ne peut pas commencer avant le verbal hook")
            esc = structure.get("escalade_rythme", {})
            payoff = structure.get("payoff", {})
            if esc and payoff and esc.get("relative_start_sec", 0) > payoff.get("relative_start_sec", 999):
                errors.append(f"Clip {i}: escalade_rythme doit preceder le payoff")
            if payoff.get("relative_end_sec", 0) < dur - 8:
                errors.append(f"Clip {i}: payoff doit etre dans les 8 dernieres secondes")
            loop = structure.get("loop_hook", {})
            if loop.get("relative_start_sec", 0) < dur - 3:
                errors.append(f"Clip {i}: loop_hook doit etre dans les 3 dernieres secondes")
            for key in STRUCTURE_KEYS:
                el = structure.get(key)
                if not el:
                    continue
                rel_start = el.get("relative_start_sec", 0)
                rel_end = el.get("relative_end_sec", 0)
                if rel_end < rel_start:
                    errors.append(f"Clip {i}: {key} fenetre invalide ({rel_start}-{rel_end}s)")
                if rel_end > dur + 1:
                    errors.append(f"Clip {i}: {key} depasse la duree du clip ({rel_end}s > {dur}s)")

    if errors:
        section("ERREURS DE VALIDATION")
        for e in errors:
            log_fail(e)
        sys.exit(1)

    final_path = output_dir / OUTPUT_FILENAME
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(cutlist, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 52)
    print(" D-F02 VALIDATE - CUTLIST VALIDEE")
    print(f"  Clips      : {len(clips)}")
    for i, c in enumerate(clips):
        struct_ok = all(k in c.get("structure", {}) for k in STRUCTURE_KEYS)
        print(f"  Clip {i}    : {c.get('duration_sec', 0)}s ({c.get('start_sec', 0)}-{c.get('end_sec', 0)}s) structure {'OK' if struct_ok else 'MANQUANTE'}")
    print(f"  Fichier    : {OUTPUT_FILENAME}")
    print("=" * 52)


def main():
    parser = argparse.ArgumentParser(
        description="D-F02 VIRAL CUT - Detection de moments viraux"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--channel", default=None,
                        help="Slug de chane PERTURABO (optionnel)")
    parser.add_argument("--clip-count", type=int, default=5,
                        help="Nombre de clips a generer (defaut 5)")
    parser.add_argument("--clip-max-duration", type=int, default=60,
                        help="Duree max par clip en secondes (defaut 60)")
    parser.add_argument("--window-sec", type=int, default=360,
                        help="Fenetre temporelle analysee en secondes (defaut 360)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true",
                       help="Genere le prompt Oracle")
    group.add_argument("--validate", metavar="FILE",
                       help="Valide la cutlist generee par l'Oracle")
    group.add_argument("--oracle", action="store_true",
                       help="Mode complet: prepare + appelle l'Oracle + valide")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if args.prepare:
        prepare_prompt(input_dir, output_dir, args.channel, args.clip_count, args.clip_max_duration, args.window_sec)
    elif args.validate:
        validate_cutlist(input_dir, output_dir, args.validate, args.clip_max_duration)
    elif args.oracle:
        run_oracle(input_dir, output_dir, args.clip_count, args.clip_max_duration, args.channel, window_sec=args.window_sec)


if __name__ == "__main__":
    main()
