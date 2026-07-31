"""
OMNIS_EXECUTEUR_DELTA.py - Orchestrateur OMNIS-WATCH DELTA (GitHub Actions)
===========================================================================
Sandbox = telecommande + Oracle.
Toutes les fregates delta tournent sur GitHub Actions.
L'operateur valide aux 5 gates (G1 a G5). F05 + F06 automatiques.

Usage:
  python OMNIS_EXECUTEUR_DELTA.py --start --title "Mon sujet" --url "https://..."
  python OMNIS_EXECUTEUR_DELTA.py --gate G2    # Telecharge F00, lance F01
  python OMNIS_EXECUTEUR_DELTA.py --gate G3    # Lance F02 Oracle (interaction operateur)
  python OMNIS_EXECUTEUR_DELTA.py --gate G4    # Lance F03 reframe
  python OMNIS_EXECUTEUR_DELTA.py --gate G5    # Lance F04 assembly + auto F05 + F06
  python OMNIS_EXECUTEUR_DELTA.py --close      # Telecharger clips finaux (F06)
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


def cmd_gate_g1(title, url, token, ledger):
    section("GATE G1 - Initialisation / Ingest")

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
        section("Trigger D-F00 Ingest sur GitHub Actions")
        if trigger_workflow(token, "d00_ingest.yml", inputs=inputs):
            time.sleep(5)
            run_id_gh = get_latest_run_id(token, "d00_ingest.yml")
            if run_id_gh:
                ledger["gh_runs"]["d00"] = run_id_gh
                log_ok(f"Run D-F00 GitHub Actions: #{run_id_gh}")
    else:
        log_info("Pas d'URL - upload manuel requis")
        log_info("Placez video_source.mp4 dans delta/F00_INGEST/IN/")
        log_info("Puis lancez le workflow d00_ingest.yml manuellement ou --gate G2 si deja fait")

    save_ledger(ledger)
    print()
    print("=" * 52)
    print(" GATE G1 - D-F00 lance (ou upload manuel)")
    print(f" Quand F00 est termine et valide:")
    print(f"   python OMNIS_EXECUTEUR_DELTA.py --gate G2")
    print("=" * 52)


def cmd_gate_g2(token, ledger):
    section("GATE G2 - Scene Detect")

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
    ledger["etapes_completees"].append("D-F00")

    f01_in = SCRIPT_DIR / "F01_SCENE_DETECT" / "IN"
    f01_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(d00_out / "video_source.mp4", f01_in / "video_source.mp4")
    shutil.copy2(d00_out / "d00_manifest.json", f01_in / "d00_manifest.json")

    section("Trigger D-F01 Scene Detect + Transcribe sur GitHub Actions")
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

    log_info("Attente D-F01 scenes + transcription...")
    d01s_id = ledger.get("gh_runs", {}).get("d01_scenedetect")
    d01t_id = ledger.get("gh_runs", {}).get("d01_transcribe")

    for rid, name in [(d01s_id, "D-F01 scenes"), (d01t_id, "D-F01 transcription")]:
        if rid:
            log_info(f"Attente {name} #{rid}...")
            success, _ = wait_for_run(token, rid, timeout=600, interval=15)
            if not success:
                log_fail(f"{name} #{rid} a echoue")
                return

    section("Telechargement artifacts D-F01")
    f01_out = SCRIPT_DIR / "F01_SCENE_DETECT" / "OUT"
    f01_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, d01s_id, "d01-scenes-output", str(f01_out))
    download_artifact(token, d01t_id, "d01-transcript-output", str(f01_out))

    ledger["etapes_completees"].extend(["D-F00", "D-F01"])

    ledger["gate_actuelle"] = "G2"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G2 - D-F01 termine")
    print(" Scenes et transcription telechargees")
    print(" Validez les scenes, puis:")
    print("   python OMNIS_EXECUTEUR_DELTA.py --gate G3")
    print("=" * 52)


def cmd_gate_g3(token, ledger):
    section("GATE G3 - Viral Cut (Oracle + Operateur)")

    f01_out = SCRIPT_DIR / "F01_SCENE_DETECT" / "OUT"

    f02_in = SCRIPT_DIR / "F02_VIRAL_CUT" / "IN"
    f02_in.mkdir(parents=True, exist_ok=True)
    for f in f01_out.iterdir():
        shutil.copy2(f, f02_in / f.name)

    print()
    print("-- Interaction operateur pour D-F02 Viral Cut --")
    print()

    clip_count = input("  Nombre de clips a generer (1-15, defaut 5): ").strip()
    if not clip_count:
        clip_count = "5"
    elif not clip_count.isdigit() or int(clip_count) < 1 or int(clip_count) > 15:
        log_fail("Nombre invalide, utilisation de 5")
        clip_count = "5"

    clip_duration = input("  Duree max par clip en secondes (15-90, defaut 60): ").strip()
    if not clip_duration:
        clip_duration = "60"
    elif not clip_duration.isdigit() or int(clip_duration) < 15 or int(clip_duration) > 90:
        log_fail("Duree invalide, utilisation de 60s")
        clip_duration = "60"

    log_ok(f"{clip_count} clips, max {clip_duration}s chacun")

    inputs = {"mode": MODE, "clip_count": clip_count, "clip_max_duration": clip_duration}

    section("Trigger D-F02 Oracle sur GitHub Actions")
    if trigger_workflow(token, "d02_viralcut.yml", inputs=inputs):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d02_viralcut.yml")
        if run_id_gh:
            ledger["gh_runs"]["d02_oracle"] = run_id_gh
            log_ok(f"Run D-F02 Oracle: #{run_id_gh}")

            log_info("Attente D-F02 Oracle (generation cutlist OpenRouter)...")
            success, _ = wait_for_run(token, run_id_gh, timeout=300, interval=15)
            if not success:
                log_fail("D-F02 Oracle a echoue")
                save_ledger(ledger)
                return

            f02_out = SCRIPT_DIR / "F02_VIRAL_CUT" / "OUT"
            f02_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, run_id_gh, "d02-cutlist-output", str(f02_out))
            log_ok("Cutlist generee et telechargee !")
            ledger["etapes_completees"].extend(["D-F01", "D-F02"])

    ledger["gate_actuelle"] = "G3"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G3 - D-F02 termine")
    print(" Cutlist Oracle generee avec vos parametres")
    print(" Validez la cutlist, puis:")
    print("   python OMNIS_EXECUTEUR_DELTA.py --gate G4")
    print("=" * 52)


def cmd_gate_g4(token, ledger):
    section("GATE G4 - Reframe")

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

    ledger["gate_actuelle"] = "G4"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G4 - D-F03 termine")
    print(" Clips reframes telecharges")
    print(" Validez le reframe, puis:")
    print("   python OMNIS_EXECUTEUR_DELTA.py --gate G5")
    print("=" * 52)


def cmd_gate_g5(token, ledger):
    section("GATE G5 - Assembly + Camouflage + Luther")

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
            log_info("Attente D-F04 Assembly...")
            success, _ = wait_for_run(token, run_id_gh, timeout=600, interval=15)
            if not success:
                log_fail("D-F04 a echoue")
                save_ledger(ledger)
                return

            f04_out = SCRIPT_DIR / "F04_ASSEMBLY" / "OUT"
            f04_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, run_id_gh, "d04-output", str(f04_out))
            log_ok("Assembly termine !")

            ledger["etapes_completees"].append("D-F04")

    section("Auto: D-F05 Camouflage")
    f05_in = SCRIPT_DIR / "F05_CAMOUFLAGE" / "IN"
    f05_in.mkdir(parents=True, exist_ok=True)

    f04_clips = f04_out / "clips_finaux"
    if f04_clips.exists():
        for f in f04_clips.iterdir():
            shutil.copy2(f, f05_in / f.name)

    if trigger_workflow(token, "d05_camouflage.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d05_camouflage.yml")
        if run_id_gh:
            ledger["gh_runs"]["d05"] = run_id_gh
            log_ok(f"Run D-F05: #{run_id_gh}")
            log_info("Attente D-F05 Camouflage...")
            success, _ = wait_for_run(token, run_id_gh, timeout=600, interval=15)
            if not success:
                log_fail("D-F05 a echoue")
                save_ledger(ledger)
                return

            f05_out = SCRIPT_DIR / "F05_CAMOUFLAGE" / "OUT"
            f05_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, run_id_gh, "d05-output", str(f05_out))
            log_ok("Camouflage termine !")
            ledger["etapes_completees"].append("D-F05")

    section("Auto: D-F06 Luther")
    f06_in = SCRIPT_DIR / "F06_LUTHER" / "IN"
    f06_in.mkdir(parents=True, exist_ok=True)

    f05_clips = f05_out / "clips_camoufles"
    if f05_clips.exists():
        for f in f05_clips.iterdir():
            shutil.copy2(f, f06_in / f.name)

    if trigger_workflow(token, "d06_luther.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "d06_luther.yml")
        if run_id_gh:
            ledger["gh_runs"]["d06"] = run_id_gh
            log_ok(f"Run D-F06: #{run_id_gh}")
            log_info("Attente D-F06 Luther...")
            success, _ = wait_for_run(token, run_id_gh, timeout=600, interval=15)
            if not success:
                log_fail("D-F06 a echoue")
                save_ledger(ledger)
                return

            f06_out = SCRIPT_DIR / "F06_LUTHER" / "OUT"
            f06_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, run_id_gh, "d06-output", str(f06_out))
            log_ok("Luther termine !")
            ledger["etapes_completees"].append("D-F06")

    ledger["gate_actuelle"] = "G5"
    ledger["statut"] = "TERMINE"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G5 - PRODUCTION TERMINEE")
    print(" F04 assembly + F05 camouflage + F06 luther OK")
    print(" Clips finaux: delta/F06_LUTHER/OUT/clips_finaux/")
    print(" Pour telecharger les artefacts:")
    print("   python OMNIS_EXECUTEUR_DELTA.py --close")
    print("=" * 52)


def cmd_close(token, ledger):
    section("CLOSE - Telechargement final")

    f06_run_id = ledger.get("gh_runs", {}).get("d06")
    if not f06_run_id:
        f05_out = SCRIPT_DIR / "F05_CAMOUFLAGE" / "OUT"
        if f05_out.exists():
            log_info("F06 deja telecharge ou absent - utilisation F05")
            f06_out = SCRIPT_DIR / "F06_LUTHER" / "OUT"
            if f06_out.exists():
                log_ok(f"Clips finaux prets: {f06_out}")
            return
        log_fail("Aucun run D-F06 dans le ledger")
        return

    success, _ = wait_for_run(token, f06_run_id, timeout=300, interval=15)
    if not success:
        log_fail(f"Run D-F06 #{f06_run_id} non termine")
        return

    f06_path = SCRIPT_DIR / "F06_LUTHER" / "OUT"
    f06_path.mkdir(parents=True, exist_ok=True)
    download_artifact(token, f06_run_id, "d06-output", str(f06_path))

    ledger["artefacts"]["clips_finaux"] = "F06_LUTHER/OUT/clips_finaux"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" VICTORIA AETERNA - Production terminee")
    print(f" Clips finaux: {f06_path / 'clips_finaux'}")
    print("=" * 52)


def main():
    parser = argparse.ArgumentParser(
        description="OMNIS_EXECUTEUR_DELTA - Orchestrateur flotte delta"
    )
    parser.add_argument("--start", action="store_true", help="Initialiser une production (G1)")
    parser.add_argument("--title", help="Titre de la production")
    parser.add_argument("--url", help="URL YouTube source")
    parser.add_argument("--gate", choices=["G2", "G3", "G4", "G5"], help="Passer a une gate")
    parser.add_argument("--close", action="store_true", help="Telecharger clips finaux")
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
        cmd_gate_g1(args.title, args.url, token, ledger)
    elif args.gate == "G2":
        cmd_gate_g2(token, ledger)
    elif args.gate == "G3":
        cmd_gate_g3(token, ledger)
    elif args.gate == "G4":
        cmd_gate_g4(token, ledger)
    elif args.gate == "G5":
        cmd_gate_g5(token, ledger)
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
        elif gate == "G5":
            cmd_gate_g5(token, ledger)
        elif gate == "CLOSE":
            cmd_close(token, ledger)
        else:
            log_info(f"Production deja terminee ({gate})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
