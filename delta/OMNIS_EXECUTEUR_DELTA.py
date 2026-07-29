"""
OMNIS_EXECUTEUR_DELTA.py - Orchestrateur OMNIS-WATCH DELTA (GitHub Actions)
===========================================================================
Sandbox = telecommande + Oracle.
Toutes les fregates delta tournent sur GitHub Actions.
L'operateur intervient aux 3 gates (G1, G2=G3, G4).

Usage:
  python OMNIS_EXECUTEUR_DELTA.py --start --title "Mon sujet" --url "https://..."
  python OMNIS_EXECUTEUR_DELTA.py --gate G2    # Telecharge D-F00, lance D-F01 + D-F02 (Oracle)
  python OMNIS_EXECUTEUR_DELTA.py --gate G3    # Trigger D-F03 (reframe)
  python OMNIS_EXECUTEUR_DELTA.py --gate G4    # Telecharge D-F03, trigger D-F04 (assembly)
  python OMNIS_EXECUTEUR_DELTA.py --close      # Telecharger clips finaux
  python OMNIS_EXECUTEUR_DELTA.py --resume     # Reprendre depuis ledger

Variables d'environnement requises:
  GH_TOKEN - token GitHub (scope: repo)
  OPENROUTER_API_KEY - cle API OpenRouter (pour D-F02 Oracle)
"""

import argparse
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

try:
    import requests
except ImportError:
    print("[SETUP] Installation de requests...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "requests",
        "--quiet", "--break-system-packages"
    ])
    import requests

SCRIPT_DIR = Path(__file__).parent.resolve()
LEDGER_PATH = SCRIPT_DIR / "omnis_ledger.json"
REPO_NAME = "kioka8877-ux/OMNIS_WATCH"
MODE = "delta"
BRANCH = "delta-dev"
GH_API = "https://api.github.com/repos"


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def load_ledger():
    if not LEDGER_PATH.exists():
        log_fail(f"Ledger introuvable: {LEDGER_PATH}")
        sys.exit(1)
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ledger(ledger):
    ledger["derniere_mise_a_jour"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    log_ok(f"Ledger sauvegarde: gate={ledger['gate_actuelle']}")


def gh_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def trigger_workflow(token, workflow_filename, ref=BRANCH, inputs=None):
    url = f"{GH_API}/{REPO_NAME}/actions/workflows/{workflow_filename}/dispatches"
    payload = {"ref": ref}
    if inputs:
        payload["inputs"] = inputs
    resp = requests.post(url, headers=gh_headers(token), json=payload)
    if resp.status_code == 204:
        log_ok(f"Workflow declenche: {workflow_filename}")
        return True
    else:
        log_fail(f"Erreur trigger {workflow_filename}: {resp.status_code} {resp.text}")
        return False


def get_workflow_runs(token, workflow_filename, limit=5):
    url = f"{GH_API}/{REPO_NAME}/actions/workflows/{workflow_filename}/runs"
    params = {"per_page": limit, "branch": BRANCH}
    resp = requests.get(url, headers=gh_headers(token), params=params)
    if resp.status_code != 200:
        log_fail(f"Erreur recuperation runs: {resp.status_code}")
        return []
    return resp.json().get("workflow_runs", [])


def wait_for_run(token, run_id, timeout=600, interval=15):
    url = f"{GH_API}/{REPO_NAME}/actions/runs/{run_id}"
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(url, headers=gh_headers(token))
        if resp.status_code != 200:
            log_info(f"Erreur status run {run_id}: {resp.status_code}")
            time.sleep(interval)
            continue
        data = resp.json()
        status = data["status"]
        conclusion = data.get("conclusion")
        if status == "completed":
            if conclusion == "success":
                log_ok(f"Run {run_id} termine: SUCCESS")
                return True, data
            else:
                log_fail(f"Run {run_id} termine: {conclusion}")
                return False, data
        elapsed = int(time.time() - start)
        log_info(f"Run {run_id}: {status} ({elapsed}s ecoules)")
        time.sleep(interval)
    log_fail(f"Timeout apres {timeout}s pour run {run_id}")
    return False, None


def download_artifact(token, run_id, artifact_name, output_dir):
    url = f"{GH_API}/{REPO_NAME}/actions/runs/{run_id}/artifacts"
    resp = requests.get(url, headers=gh_headers(token))
    if resp.status_code != 200:
        log_fail(f"Erreur recuperation artifacts: {resp.status_code}")
        return None
    artifacts = resp.json().get("artifacts", [])
    target = None
    for art in artifacts:
        if art["name"] == artifact_name:
            target = art
            break
    if not target:
        log_fail(f"Artifact non trouve: {artifact_name}")
        log_info(f"Artifacts disponibles: {[a['name'] for a in artifacts]}")
        return None
    download_url = target["archive_download_url"]
    resp = requests.get(download_url, headers=gh_headers(token))
    if resp.status_code != 200:
        log_fail(f"Erreur download artifact: {resp.status_code}")
        return None
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(output_dir)
    log_ok(f"Artifact telecharge: {artifact_name} -> {output_dir}")
    return output_dir


def get_latest_run_id(token, workflow_filename):
    runs = get_workflow_runs(token, workflow_filename, limit=1)
    if not runs:
        return None
    return runs[0]["id"]


def cmd_start(title, url, token, ledger):
    section("GATE G1 - Initialisation")

    run_id = f"DELTA_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
    ledger["run_id"] = run_id
    ledger["production_title"] = title
    ledger["gate_actuelle"] = "G1"
    ledger["statut"] = "EN_COURS"
    ledger["etapes_completees"] = []
    ledger["artefacts"] = {}
    ledger["gh_runs"] = {}

    log_ok(f"Production: {title}")
    log_ok(f"Run ID: {run_id}")

    if url:
        log_ok(f"URL source: {url}")
        inputs = {"mode": MODE, "url": url}
    else:
        log_info("Pas d'URL - upload manuel requis")
        log_info("Placez video_source.mp4 dans delta/F00_INGEST/IN/")
        save_ledger(ledger)
        return

    section("Trigger D-F00 Ingest sur GitHub Actions")
    if trigger_workflow(token, "d00_ingest.yml", inputs=inputs):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d00_ingest.yml")
        if run_id_gh:
            ledger["gh_runs"]["d00"] = run_id_gh
            log_ok(f"Run D-F00 GitHub Actions: #{run_id_gh}")
            save_ledger(ledger)
            print()
            print("=" * 52)
            print(" GATE G1 - D-F00 lance sur GitHub Actions")
            print(f" Run: #{run_id_gh}")
            print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
            print(f" Quand D-F00 est termine, lancez: --gate G2")
            print("=" * 52)
    else:
        log_fail("Echec du trigger D-F00")
        save_ledger(ledger)


def cmd_gate_g2(token, ledger):
    section("GATE G2 - Scene Detect + Viral Cut")

    d00_run_id = ledger.get("gh_runs", {}).get("d00")
    if not d00_run_id:
        log_fail("Aucun run D-F00 dans le ledger")
        return

    section("Telechargement artifact D-F00")
    d00_out = SCRIPT_DIR / "F00_INGEST" / "OUT"
    d00_out.mkdir(parents=True, exist_ok=True)

    success, _ = wait_for_run(token, d00_run_id, timeout=30, interval=5)
    if not success:
        log_fail(f"Run D-F00 #{d00_run_id} non termine ou echoue")
        return

    download_artifact(token, d00_run_id, "d00-output", str(d00_out))

    f01_in = SCRIPT_DIR / "F01_SCENE_DETECT" / "IN"
    f01_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(d00_out / "video_source.mp4", f01_in / "video_source.mp4")
    shutil.copy2(d00_out / "d00_manifest.json", f01_in / "d00_manifest.json")

    ledger["etapes_completees"].append("D-F00")

    section("Trigger D-F01 Scene Detect sur GitHub Actions")
    if trigger_workflow(token, "d01_scenedetect.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d01_scenedetect.yml")
        if run_id_gh:
            ledger["gh_runs"]["d01_scenedetect"] = run_id_gh
            log_ok(f"Run D-F01 scenes: #{run_id_gh}")

    if trigger_workflow(token, "d01_transcribe.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d01_transcribe.yml")
        if run_id_gh:
            ledger["gh_runs"]["d01_transcribe"] = run_id_gh
            log_ok(f"Run D-F01 transcription: #{run_id_gh}")

    section("D-F02 Viral Cut - Oracle + PERTURABO")
    log_info("L'Oracle (sandbox) genere la cutlist base sur PERTURABO")
    log_info("1. Preparez le prompt:")
    log_info(f"  python F02_VIRAL_CUT/CODEBASE/omnis_d02_viralcut.py \\")
    log_info(f"    --input F02_VIRAL_CUT/IN/ --output F02_VIRAL_CUT/OUT/ --prepare")
    log_info("2. L'Oracle genere cutlist.json base sur le prompt")
    log_info("3. Validez la cutlist:")
    log_info(f"  python F02_VIRAL_CUT/CODEBASE/omnis_d02_viralcut.py \\")
    log_info(f"    --input F02_VIRAL_CUT/IN/ --output F02_VIRAL_CUT/OUT/ --validate cutlist.json")

    ledger["gate_actuelle"] = "G2"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G2 - En attente de validation")
    print(" 1. D-F01: GitHub Actions (scenes + transcription)")
    print(" 2. D-F02: Oracle sandbox (PERTURABO cutlist)")
    print(" Quand tout est valide: --gate G3")
    print("=" * 52)


def cmd_gate_g3(token, ledger):
    section("GATE G3 - Reframe")

    cutlist_path = SCRIPT_DIR / "F02_VIRAL_CUT" / "OUT" / "cutlist.json"
    if not cutlist_path.exists():
        log_fail("cutlist.json non trouve dans F02_VIRAL_CUT/OUT/")
        return

    f03_in = SCRIPT_DIR / "F03_REFRAME" / "IN"
    f03_in.mkdir(parents=True, exist_ok=True)

    video_source = SCRIPT_DIR / "F00_INGEST" / "OUT" / "video_source.mp4"
    if video_source.exists():
        shutil.copy2(video_source, f03_in / "video_source.mp4")
    shutil.copy2(cutlist_path, f03_in / "cutlist.json")

    section("Trigger D-F03 Reframe sur GitHub Actions")
    if trigger_workflow(token, "d03_reframe.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d03_reframe.yml")
        if run_id_gh:
            ledger["gh_runs"]["d03"] = run_id_gh
            log_ok(f"Run D-F03: #{run_id_gh}")

            log_info("En attente de D-F03 (peut prendre plusieurs minutes)...")
            success, _ = wait_for_run(token, run_id_gh, timeout=1800, interval=30)
            if not success:
                log_fail("D-F03 a echoue ou timeout")
                save_ledger(ledger)
                return

            f03_out = SCRIPT_DIR / "F03_REFRAME" / "OUT"
            f03_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, run_id_gh, "d03-output", str(f03_out))

    ledger["etapes_completees"].extend(["D-F01", "D-F02", "D-F03"])
    ledger["gate_actuelle"] = "G3"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G3 - D-F03 termine")
    print(" Quand pret: --gate G4")
    print("=" * 52)


def cmd_gate_g4(token, ledger):
    section("GATE G4 - Assembly")

    f04_in = SCRIPT_DIR / "F04_ASSEMBLY" / "IN"
    f04_in.mkdir(parents=True, exist_ok=True)

    clips_dir = SCRIPT_DIR / "F03_REFRAME" / "OUT" / "clips_reframes"
    transcript = SCRIPT_DIR / "F01_SCENE_DETECT" / "OUT" / "transcript.json"
    cutlist = SCRIPT_DIR / "F02_VIRAL_CUT" / "OUT" / "cutlist.json"

    if clips_dir.exists():
        for f in clips_dir.iterdir():
            shutil.copy2(f, f04_in / f.name)
    if transcript.exists():
        shutil.copy2(transcript, f04_in / "transcript.json")
    if cutlist.exists():
        shutil.copy2(cutlist, f04_in / "cutlist.json")

    section("Trigger D-F04 Assembly sur GitHub Actions")
    if trigger_workflow(token, "d04_assembly.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d04_assembly.yml")
        if run_id_gh:
            ledger["gh_runs"]["d04"] = run_id_gh
            log_ok(f"Run D-F04: #{run_id_gh}")

    ledger["etapes_completees"].append("D-F04")
    ledger["gate_actuelle"] = "G4"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G4 - D-F04 lance sur GitHub Actions")
    print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
    print(f" Quand D-F04 est termine: --close")
    print("=" * 52)


def cmd_close(token, ledger):
    section("CLOSE - Telechargement final")

    d04_run_id = ledger.get("gh_runs", {}).get("d04")
    if not d04_run_id:
        log_fail("Aucun run D-F04 dans le ledger")
        return

    success, _ = wait_for_run(token, d04_run_id, timeout=300, interval=15)
    if not success:
        log_fail(f"Run D-F04 #{d04_run_id} non termine")
        return

    f04_out = SCRIPT_DIR / "F04_ASSEMBLY" / "OUT"
    f04_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, d04_run_id, "d04-output", str(f04_out))

    ledger["artefacts"]["clips_finaux"] = "F04_ASSEMBLY/OUT/clips_finaux"
    ledger["gate_actuelle"] = "CLOSE"
    ledger["statut"] = "TERMINE"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" VICTORIA AETERNA - Production terminee")
    print(" Clips finaux: F04_ASSEMBLY/OUT/clips_finaux/")
    print("=" * 52)


def main():
    parser = argparse.ArgumentParser(
        description="OMNIS_EXECUTEUR_DELTA - Orchestrateur flotte delta"
    )
    parser.add_argument("--start", action="store_true", help="Initialiser une production")
    parser.add_argument("--title", help="Titre de la production")
    parser.add_argument("--url", help="URL YouTube source")
    parser.add_argument("--gate", choices=["G2", "G3", "G4"], help="Passer a une gate")
    parser.add_argument("--close", action="store_true", help="Terminer et telecharger")
    parser.add_argument("--resume", action="store_true", help="Reprendre depuis ledger")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        log_fail("GH_TOKEN non defini")
        print("  export GH_TOKEN=<votre_token>")
        sys.exit(1)

    ledger = load_ledger()

    if args.start:
        if not args.title:
            log_fail("--title requis avec --start")
            sys.exit(1)
        cmd_start(args.title, args.url, token, ledger)
    elif args.gate == "G2":
        cmd_gate_g2(token, ledger)
    elif args.gate == "G3":
        cmd_gate_g3(token, ledger)
    elif args.gate == "G4":
        cmd_gate_g4(token, ledger)
    elif args.close:
        cmd_close(token, ledger)
    elif args.resume:
        gate = ledger.get("gate_actuelle", "G1")
        print(f"[RESUME] Reprise a gate {gate}")
        if gate == "G1":
            log_info("Placez video_source.mp4 ou donnez --url et relancez --start")
        elif gate == "G2":
            cmd_gate_g2(token, ledger)
        elif gate == "G3":
            cmd_gate_g3(token, ledger)
        elif gate == "G4":
            cmd_gate_g4(token, ledger)
        elif gate == "CLOSE":
            cmd_close(token, ledger)
        else:
            log_info(f"Production deja terminee ({gate})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
