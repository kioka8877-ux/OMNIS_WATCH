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


def call_openrouter(prompt_text, api_key, model="openai/gpt-4o"):
    log_info("Appel OpenRouter Oracle...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/kioka8877-ux/OMNIS_WATCH",
        "X-Title": "OMNIS-Delta-Oracle"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es VIRAL CUT DETECTOR pour YouTube Shorts. Genere UNIQUEMENT du JSON valide, rien d autre."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.3,
        "max_tokens": 1024
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            log_fail(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")
            return None
        result = resp.json()
        raw = result["choices"][0]["message"]["content"]
        json_match = re.search(r'`(?:json)?\s*([\s\S]*?)\s*`', raw)
        if json_match:
            raw_json = json_match.group(1)
        else:
            raw_json = raw.strip()
        return json.loads(raw_json)
    except Exception as e:
        log_fail(f"OpenRouter call failed: {e}")
        return None

def run_oracle(input_dir, output_dir, clip_count=5, clip_max_duration=60, channel_slug=None, model="openai/gpt-4o"):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        log_fail("OPENROUTER_API_KEY non definie dans l environnement")
        sys.exit(1)
    prepare_prompt(input_dir, output_dir, channel_slug, clip_count, clip_max_duration)
    prompt_path = output_dir / PROMPT_FILENAME
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()
    cutlist = call_openrouter(prompt_text, api_key, model)
    if not cutlist:
        sys.exit(1)
    cutlist_path = output_dir / OUTPUT_FILENAME
    with open(cutlist_path, "w", encoding="utf-8") as f:
        json.dump(cutlist, f, ensure_ascii=False, indent=2)
    log_ok(f"Cutlist generee par Oracle: {cutlist_path}")
    validate_cutlist(input_dir, output_dir, OUTPUT_FILENAME)

def prepare_prompt(input_dir, output_dir, channel_slug=None, clip_count=5, clip_max_duration=60):
    """Genere le prompt pour l'Oracle (sandbox)."""
    section("D-F02 PREPARE - Generation du prompt Oracle")
    log_info(f"Parametres operateur: {clip_count} clips, max {clip_max_duration}s")

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

    log_ok(f"Scenes: {scenes_data.get('scene_count', 0)}")
    log_ok(f"Transcript: {transcript_data.get('word_count', 0)} mots")

    section("PERTURABO Bridge - Fetch regles")
    shorts_rules = fetch_perturabo(RULES_SHORTS)
    tim_rules = fetch_perturabo(RULES_TIM)
    skeleton = fetch_perturabo(SKELETON_CHECKLIST)
    channel_id = fetch_channel_identity(channel_slug) if channel_slug else "(aucune chane assignee)"

    log_ok("Regles PERTURABO recuperees")

    scenes_summary = json.dumps(scenes_data["scenes"][:12], ensure_ascii=False, indent=2)
    transcript_summary = json.dumps(
        transcript_data["words"][:300], ensure_ascii=False, indent=2
    )

    prompt = f"""# MISSION D-F02 - VIRAL CUT DETECTOR

## PERTURABO REGLES (OBLIGATOIRE - appliquer sur la cutlist)

### SHORTS RULES:
{shorts_rules[:5000]}

### TIM DANILOV RULES:
{tim_rules[:5000]}

### SKELETON CHECKLIST:
{skeleton[:3000]}

### CHANNEL IDENTITY:
{channel_id[:2000] if channel_id else "(aucune)"}

## DONNEES SOURCE

### SCENES ({scenes_data.get('scene_count', 0)} scenes):
{scenes_summary}

### TRANSCRIPT ({transcript_data.get('word_count', 0)} mots, langue={transcript_data.get('language', '?')}):
{transcript_summary}

## MISSION:
Tu es un VIRAL CUT DETECTOR pour YouTube Shorts.
Identifie les {clip_count} MEILLEURS moments de cette video qui deviendront des Shorts viraux.

CRITERES (par ordre de priorite):
1. Hook potential : la premiere frame fonctionne SANS SON (Regle S3)
2. Payoff potential : le moment a un payoff identifiable (Regle S1)
3. Emotion : le moment est emotionnellement fort
4. Rythme : Hook -> Context -> Foreshadow -> Payoff -> Loop (Regle S1)
5. Sujet : visage ou personne identifiable pour le reframe

REGLES DE SORTIE:
- EXACTEMENT {clip_count} moments (ni plus, ni moins)
- Chaque moment = 15-{clip_max_duration}s
- Ordre chronologique
- Premier moment = HOOK (capture dans les 3s)
- Dernier moment = PAYOFF ou LOOP
- Au moins 1 foreshadow entre 40-60% de la duree
- Loop hook si clip >30s (Regle S4)
- Chaque moment a un mode emotionnel (triste/wholesome/tension/surprise)

FORMAT DE SORTIE (JSON valide uniquement):
```json
{{
  "video_duration_sec": 0,
  "moment_count": 0,
  "moments": [
    {{
      "index": 0,
      "start_sec": 0,
      "end_sec": 0,
      "duration_sec": 0,
      "viral_type": "hook|context|foreshadow|payoff|loop",
      "perturabo_rule": "Regle S1/S2/S3/S4/S5/S6 ou Tim Danilov 1-6",
      "emotion_mode": "triste|wholesome|tension|surprise",
      "hook_summary": "Description courte du hook (2-10 mots)",
      "scene_source": 0
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


def validate_cutlist(input_dir, output_dir, cutlist_file):
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

    moments = cutlist.get("moments", [])
    if not moments:
        errors.append("Aucun moment dans la cutlist")
    if len(moments) < 3:
        errors.append(f"Trop peu de moments: {len(moments)} (min 3)")
    if len(moments) > 15:
        errors.append(f"Trop de moments: {len(moments)} (max 15)")

    has_hook = any(m.get("viral_type") == "hook" for m in moments)
    has_payoff = any(m.get("viral_type") == "payoff" for m in moments)
    has_foreshadow = any(m.get("viral_type") == "foreshadow" for m in moments)

    if not has_hook:
        errors.append("Pas de moment type HOOK")
    if not has_payoff:
        errors.append("Pas de moment type PAYOFF")
    if not has_foreshadow:
        errors.append("Pas de moment type FORESHADOW")

    video_dur = cutlist.get("video_duration_sec", 0)
    if video_dur > 30:
        has_loop = any(m.get("viral_type") == "loop" for m in moments)
        if not has_loop:
            errors.append("Pas de LOOP hook (Regle S4) pour video >30s")

    for i, m in enumerate(moments):
        if not m.get("perturabo_rule"):
            errors.append(f"Moment {i}: pas de regle PERTURABO justificative")
        if not m.get("emotion_mode"):
            errors.append(f"Moment {i}: pas de mode emotionnel")
        dur = m.get("duration_sec", 0)
        if dur < 10 or dur > 90:
            errors.append(f"Moment {i}: duree {dur}s hors plage (10-90s)")

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
    print(f"  Moments    : {len(moments)}")
    print(f"  Hook       : {'OK' if has_hook else 'MANQUANT'}")
    print(f"  Payoff     : {'OK' if has_payoff else 'MANQUANT'}")
    print(f"  Foreshadow : {'OK' if has_foreshadow else 'MANQUANT'}")
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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true",
                       help="Genere le prompt Oracle")
    group.add_argument("--validate", metavar="FILE",
                       help="Valide la cutlist generee par l'Oracle")
    group.add_argument("--oracle", action="store_true",
                       help="Mode complet: prepare + appelle OpenRouter + valide")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if args.prepare:
        prepare_prompt(input_dir, output_dir, args.channel, args.clip_count, args.clip_max_duration)
    elif args.validate:
        validate_cutlist(input_dir, output_dir, args.validate)
    elif args.oracle:
        run_oracle(input_dir, output_dir, args.clip_count, args.clip_max_duration, args.channel)


if __name__ == "__main__":
    main()
