"""
OMNIS_EXECUTEUR.py — Orchestrateur OMNIS-WATCH Gamma
====================================================
Mode GAMMA : pipeline voix off + sequences multi-clips.
Sandbox = telecommande + Oracle. GH Actions = usine.

Usage:
  python OMNIS_EXECUTEUR.py --start --title "Mon clip"
  python OMNIS_EXECUTEUR.py --gate G2    # F01 done -> trigger F00
  python OMNIS_EXECUTEUR.py --gate G3    # F00 done -> trigger F03
  python OMNIS_EXECUTEUR.py --gate G4    # F03 done -> trigger F04+F05
  python OMNIS_EXECUTEUR.py --close      # Telecharger artefact final
  python OMNIS_EXECUTEUR.py --resume     # Reprendre depuis ledger

Variables d'environnement requises:
  GH_TOKEN — token GitHub (scope: repo)
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
MODE = "gamma"
GH_API = "https://api.github.com/repos"

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "=" * max(0, 50 - len(title))
    print(f"\n--- {title} {bar}")

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

def trigger_workflow(token, workflow_filename, ref="gamma-dev", inputs=None):
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
    params = {"per_page": limit}
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
            log_warn(f"Erreur status run {run_id}: {resp.status_code}")
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
        log_info(f"Disponibles: {[a['name'] for a in artifacts]}")
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

def custos(frigate, mode):
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", frigate, "--mode", mode,
        "--base", str(SCRIPT_DIR)
    ])
    if result.returncode != 0:
        log_fail(f"CUSTOS {frigate} {mode} a echoue")
        return False
    return True

# ── GATES ─────────────────────────────────────────────────────────────────

def cmd_start(title, token, ledger):
    """GATE G1 — Initialisation : audio + whisper"""
    section("GATE G1 — Initialisation")

    run_id = f"OMNIS_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
    ledger["run_id"] = run_id
    ledger["production_title"] = title
    ledger["gate_actuelle"] = "G1"
    ledger["statut"] = "EN_COURS"
    ledger["etapes_completees"] = []
    ledger["gh_runs"] = {}

    log_ok(f"Production: {title}")
    log_ok(f"Run ID: {run_id}")

    # Verifier audio_raw.mp3 dans SHARED/IN/
    audio_raw = SCRIPT_DIR / "SHARED" / "IN" / "audio_raw.mp3"
    if not audio_raw.exists():
        log_warn("audio_raw.mp3 non trouve dans SHARED/IN/")
        log_info("Placez votre audio TTS dans gamma/SHARED/IN/audio_raw.mp3")
        log_info("Puis relancez --start")
        save_ledger(ledger)
        return
    log_ok(f"Audio source: {audio_raw}")

    # Copier vers F01A IN/
    f01a_in = SCRIPT_DIR / "F01_AUDIO" / "F01A_CASTELLAN" / "IN"
    f01a_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio_raw, f01a_in / "audio_raw.mp3")
    log_ok("Audio copie vers F01A_CASTELLAN/IN/")

    # Custos check-out F01A
    section("CUSTOS — Validation F01A check-out")
    if not custos("F01A", "check-out"):
        save_ledger(ledger)
        return

    # Trigger F01A sur GitHub Actions
    section("Trigger F01A sur GitHub Actions")
    run_id_gh = None
    if trigger_workflow(token, "f01a_audio.yml", inputs={"mode": MODE}):
        time.sleep(5)
        run_id_gh = get_latest_run_id(token, "f01a_audio.yml")
        if run_id_gh:
            ledger["gh_runs"]["f01a"] = run_id_gh
            log_ok(f"Run F01A: #{run_id_gh}")
            save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G1 - F01A lance sur GitHub Actions")
    print(" (nettoyage audio + silence detection)")
    print(f" Run: #{run_id_gh if run_id_gh else 'N/A'}")
    print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
    print(" Quand F01A et F01B sont termines: --gate G2")
    print("=" * 52)

def cmd_gate_g2(token, ledger):
    """GATE G2 — F01A -> F01B -> F00 (assetforge)"""
    section("GATE G2 — Audio -> Assetforge")

    # 1. Telecharger F01A
    f01a_run_id = ledger.get("gh_runs", {}).get("f01a")
    if not f01a_run_id:
        log_fail("Aucun run F01A dans le ledger")
        return

    section("Telechargement artifact F01A")
    f01a_out = SCRIPT_DIR / "F01_AUDIO" / "F01A_CASTELLAN" / "OUT"
    f01a_out.mkdir(parents=True, exist_ok=True)

    success, _ = wait_for_run(token, f01a_run_id, timeout=300, interval=15)
    if not success:
        log_fail(f"Run F01A #{f01a_run_id} non termine")
        return

    download_artifact(token, f01a_run_id, "f01a-output", str(f01a_out))

    if not custos("F01A", "check-in"):
        return

    ledger["etapes_completees"].append("F01A")

    # 2. Copier vers F01B IN/ et trigger
    section("Trigger F01B Whisper")
    f01b_in = SCRIPT_DIR / "F01_AUDIO" / "F01B_WHISPER" / "IN"
    f01b_in.mkdir(parents=True, exist_ok=True)

    audio_clean = f01a_out / "audio_clean.mp3"
    if audio_clean.exists():
        shutil.copy2(audio_clean, f01b_in / "audio_clean.mp3")
        log_ok("Audio clean copie vers F01B_WHISPER/IN/")

    if not custos("F01B", "check-out"):
        save_ledger(ledger)
        return

    f01b_run_id = None
    if trigger_workflow(token, "f01b_whisper.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f01b_run_id = get_latest_run_id(token, "f01b_whisper.yml")
        if f01b_run_id:
            ledger["gh_runs"]["f01b"] = f01b_run_id
            log_ok(f"Run F01B: #{f01b_run_id}")

    # 3. Attendre F01B
    section("Attente F01B Whisper")
    if not f01b_run_id:
        log_fail("Impossible de lancer F01B Whisper")
        save_ledger(ledger)
        return
    success, _ = wait_for_run(token, f01b_run_id, timeout=600, interval=15)
    if not success:
        log_fail(f"Run F01B #{f01b_run_id} non termine")
        save_ledger(ledger)
        return

    f01b_out = SCRIPT_DIR / "F01_AUDIO" / "F01B_WHISPER" / "OUT"
    f01b_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, f01b_run_id, "f01b-output", str(f01b_out))

    if not custos("F01B", "check-in"):
        return

    ledger["etapes_completees"].append("F01B")

    # Lire timing pour la duree
    voiceoff_duration = None
    timing_path = f01b_out / "timing.json"
    if timing_path.exists():
        with open(timing_path) as f:
            timing = json.load(f)
        voiceoff_duration = timing["meta"]["duration_seconds"]
        ledger["voiceoff_duration"] = voiceoff_duration
        log_ok(f"Duree voix off: {voiceoff_duration}s")
        log_info(f"Utilisez cette duree pour preparer sequences.json")
        log_info(f"  -> gamma/F00_ASSETFORGE/IN/sequences.json")

    ledger["gate_actuelle"] = "G2"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G2 - Audio pret !")
    print(f" Duree voix off: {voiceoff_duration:.1f}s" if voiceoff_duration else " Duree voix off: inconnue")
    print(" Tache operateur:")
    print(" 1. Preparez sequences.json dans F00_ASSETFORGE/IN/")
    print(" 2. Placez les clips bruts dans F00_ASSETFORGE/IN/")
    print(" 3. Lancez: --gate G3")
    print("=" * 52)

def cmd_gate_g3(token, ledger):
    """GATE G3 — F00 Assetforge"""
    section("GATE G3 — Assetforge")

    # Verifier sequences.json
    f00_in = SCRIPT_DIR / "F00_ASSETFORGE" / "IN"
    sequences_path = f00_in / "sequences.json"
    if not sequences_path.exists():
        log_fail("sequences.json non trouve dans F00_ASSETFORGE/IN/")
        log_info("Preparez d'abord sequences.json (voir gate G2)")
        return

    if not custos("F00", "check-out"):
        return

    # Trigger F00
    section("Trigger F00 Assetforge sur GitHub Actions")
    f00_run_id = None
    if trigger_workflow(token, "f00_assetforge.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f00_run_id = get_latest_run_id(token, "f00_assetforge.yml")
        if f00_run_id:
            ledger["gh_runs"]["f00"] = f00_run_id
            log_ok(f"Run F00: #{f00_run_id}")

    if not f00_run_id:
        log_fail("Impossible de lancer F00 Assetforge")
        save_ledger(ledger)
        return

    # Attendre F00
    success, _ = wait_for_run(token, f00_run_id, timeout=600, interval=15)
    if not success:
        log_fail(f"Run F00 #{f00_run_id} non termine")
        save_ledger(ledger)
        return

    f00_out = SCRIPT_DIR / "F00_ASSETFORGE" / "OUT"
    f00_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, f00_run_id, "f00-output", str(f00_out))

    if not custos("F00", "check-in"):
        return

    ledger["etapes_completees"].append("F00")
    ledger["gate_actuelle"] = "G3"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G3 — Clip unique pret !")
    print(" Tache operateur:")
    print(" 1. Lancez F02A Vision (sandbox OpenRouter)")
    print(" 2. Lancez F02B Oracle (codex emotionnel)")
    print(" 3. Validez le preview")
    print(" 4. Lancez: --gate G4")
    print("=" * 52)

def cmd_gate_g4(token, ledger):
    """GATE G4 — F03 Render (Remotion + Mixer + Music) + F04 + F05"""
    section("GATE G4 — Rendu complet")

    # Verifier codex.json
    codex_path = SCRIPT_DIR / "F02_ANALYSIS" / "F02B_ORACLE" / "OUT" / "codex.json"
    vf00_out = SCRIPT_DIR / "F00_ASSETFORGE" / "OUT"
    if not codex_path.exists():
        log_fail("codex.json non trouve dans F02B_ORACLE/OUT/")
        log_info("Completez F02A+F02B (sandbox) d'abord")
        return

    # Copier vers F03A
    section("Preparation F03A Remotion")
    f03a_in = SCRIPT_DIR / "F03_RENDER" / "F03A_REMOTION" / "IN"
    f03a_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(codex_path, f03a_in / "codex.json")
    clip_unique = vf00_out / "clip_unique.mp4"
    if clip_unique.exists():
        shutil.copy2(clip_unique, f03a_in / "video_scenes.mp4")
    log_ok("Fichiers copies vers F03A_REMOTION/IN/")

    if not custos("F03A", "check-out"):
        return

    # Trigger F03A
    section("Trigger F03A sur GitHub Actions")
    f03a_out = SCRIPT_DIR / "F03_RENDER" / "F03A_REMOTION" / "OUT"
    if trigger_workflow(token, "f03a_render.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f03a_run_id = get_latest_run_id(token, "f03a_render.yml")
        if f03a_run_id:
            ledger["gh_runs"]["f03a"] = f03a_run_id
            log_info("Attente F03A (peut prendre plusieurs minutes)...")
            success, _ = wait_for_run(token, f03a_run_id, timeout=1800, interval=30)
            if success:
                f03a_out.mkdir(parents=True, exist_ok=True)
                download_artifact(token, f03a_run_id, "f03a-output", str(f03a_out))
                log_ok("F03A termine")

    # F03B Mixer
    section("Preparation F03B Mixer")
    f03b_in = SCRIPT_DIR / "F03_RENDER" / "F03B_MIXER" / "IN"
    f03b_in.mkdir(parents=True, exist_ok=True)
    f03b_out = SCRIPT_DIR / "F03_RENDER" / "F03B_MIXER" / "OUT"
    video_visuelle = f03a_out / "video_visuelle.mp4"
    if video_visuelle.exists():
        shutil.copy2(video_visuelle, f03b_in / "video_visuelle.mp4")
    shutil.copy2(codex_path, f03b_in / "codex.json")

    if not custos("F03B", "check-out"):
        save_ledger(ledger)
        return

    section("Trigger F03B sur GitHub Actions")
    if trigger_workflow(token, "f03b_mixer.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f03b_run_id = get_latest_run_id(token, "f03b_mixer.yml")
        if f03b_run_id:
            ledger["gh_runs"]["f03b"] = f03b_run_id
            log_info("Attente F03B...")
            success, _ = wait_for_run(token, f03b_run_id, timeout=600, interval=15)
            if success:
                f03b_out.mkdir(parents=True, exist_ok=True)
                download_artifact(token, f03b_run_id, "f03b-output", str(f03b_out))
                log_ok("F03B termine")

    # F03C Music
    section("Preparation F03C Music")
    f03c_in = SCRIPT_DIR / "F03_RENDER" / "F03C_MUSIC" / "IN"
    f03c_in.mkdir(parents=True, exist_ok=True)
    f03c_out = SCRIPT_DIR / "F03_RENDER" / "F03C_MUSIC" / "OUT"
    video_complete = f03b_out / "video_complete.mp4"
    if video_complete.exists():
        shutil.copy2(video_complete, f03c_in / "video_complete.mp4")
    log_ok("Fichiers copies vers F03C_MUSIC/IN/")

    section("Trigger F03C sur GitHub Actions")
    if trigger_workflow(token, "f03c_music.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f03c_run_id = get_latest_run_id(token, "f03c_music.yml")
        if f03c_run_id:
            ledger["gh_runs"]["f03c"] = f03c_run_id

    ledger["etapes_completees"].extend(["F03A", "F03B"])
    ledger["gate_actuelle"] = "G4"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" GATE G4 - Rendu lance sur GitHub Actions")
    print(" F03A + F03B + F03C en cours")
    print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
    print(" Quand F03C est termine: --gate F04")
    print("=" * 52)

def cmd_gate_f04(token, ledger):
    """F04 Camouflage + F05 Luther"""
    section("F04 - Camouflage")

    # Attendre F03C
    f03c_out = SCRIPT_DIR / "F03_RENDER" / "F03C_MUSIC" / "OUT"
    f03b_out = SCRIPT_DIR / "F03_RENDER" / "F03B_MIXER" / "OUT"
    f03c_run_id = ledger.get("gh_runs", {}).get("f03c")
    if f03c_run_id:
        success, _ = wait_for_run(token, f03c_run_id, timeout=600, interval=15)
        if success:
            f03c_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, f03c_run_id, "f03c-output", str(f03c_out))

    # Copier vers F04
    video_final = f03c_out / "video_final.mp4"
    if not video_final.exists():
        video_final = f03b_out / "video_complete.mp4"

    f04_in = SCRIPT_DIR / "F04_CAMOUFLAGE" / "IN"
    f04_in.mkdir(parents=True, exist_ok=True)
    if video_final.exists():
        shutil.copy2(video_final, f04_in / "video_final.mp4")

    if not custos("F04", "check-out"):
        return

    section("Trigger F04 sur GitHub Actions")
    if trigger_workflow(token, "f04_camouflage.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f04_run_id = get_latest_run_id(token, "f04_camouflage.yml")
        if f04_run_id:
            ledger["gh_runs"]["f04"] = f04_run_id
            log_info("Attente F04...")
            success, _ = wait_for_run(token, f04_run_id, timeout=600, interval=15)
            if success:
                f04_out = SCRIPT_DIR / "F04_CAMOUFLAGE" / "OUT"
                f04_out.mkdir(parents=True, exist_ok=True)
                download_artifact(token, f04_run_id, "f04-output", str(f04_out))

                # Copier vers F05
                f05_in = SCRIPT_DIR / "F05_LUTHER" / "IN"
                f05_in.mkdir(parents=True, exist_ok=True)
                youtube_final = f04_out / "youtube_final.mp4"
                if youtube_final.exists():
                    shutil.copy2(youtube_final, f05_in / "youtube_final.mp4")

                if custos("F05", "check-out"):
                    section("Trigger F05 sur GitHub Actions")
                    if trigger_workflow(token, "f05_luther.yml", inputs={"mode": MODE}):
                        time.sleep(5)
                        f05_run_id = get_latest_run_id(token, "f05_luther.yml")
                        if f05_run_id:
                            ledger["gh_runs"]["f05"] = f05_run_id

    ledger["etapes_completees"].extend(["F03C", "F04"])
    ledger["gate_actuelle"] = "F05"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" F04 + F05 lances sur GitHub Actions")
    print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
    print(" Quand F05 est termine: --close")
    print("=" * 52)

def cmd_close(token, ledger):
    """Close — Telechargement final"""
    section("CLOSE — Telechargement final")

    f05_run_id = ledger.get("gh_runs", {}).get("f05")
    if not f05_run_id:
        log_fail("Aucun run F05 dans le ledger")
        log_info("Essayez --gate F04 d'abord")
        return

    success, _ = wait_for_run(token, f05_run_id, timeout=600, interval=15)
    if not success:
        log_fail(f"Run F05 #{f05_run_id} non termine")
        return

    f05_out = SCRIPT_DIR / "F05_LUTHER" / "OUT"
    f05_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, f05_run_id, "f05-output", str(f05_out))

    if not custos("F05", "check-in"):
        return

    ledger["etapes_completees"].append("F05")
    ledger["artefacts"]["clean_final"] = "F05_LUTHER/OUT/clean_final.mp4"
    ledger["gate_actuelle"] = "CLOSE"
    ledger["statut"] = "TERMINE"
    save_ledger(ledger)

    print()
    print("=" * 52)
    print(" VICTORIA AETERNA — Production terminee")
    print(f" Fichier final: F05_LUTHER/OUT/clean_final.mp4")
    print("=" * 52)

# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OMNIS_EXECUTEUR — Orchestrateur OMNIS-WATCH Gamma"
    )
    parser.add_argument("--start", action="store_true", help="Initialiser une production")
    parser.add_argument("--title", help="Titre de la production (avec --start)")
    parser.add_argument("--gate", choices=["G2", "G3", "G4", "F04"], help="Passer a une gate")
    parser.add_argument("--close", action="store_true", help="Terminer et telecharger")
    parser.add_argument("--resume", action="store_true", help="Reprendre depuis le ledger")

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
        cmd_start(args.title, token, ledger)

    elif args.gate == "G2":
        cmd_gate_g2(token, ledger)

    elif args.gate == "G3":
        cmd_gate_g3(token, ledger)

    elif args.gate == "G4":
        cmd_gate_g4(token, ledger)

    elif args.gate == "F04":
        cmd_gate_f04(token, ledger)

    elif args.close:
        cmd_close(token, ledger)

    elif args.resume:
        gate = ledger.get("gate_actuelle", "G1")
        print(f"[RESUME] Reprise a gate {gate}")
        if gate == "G1":
            log_info("Placez audio_raw.mp3 dans SHARED/IN/ et relancez --start")
        elif gate == "G2":
            cmd_gate_g2(token, ledger)
        elif gate == "G3":
            cmd_gate_g3(token, ledger)
        elif gate == "G4":
            cmd_gate_g4(token, ledger)
        elif gate == "F05":
            cmd_gate_f04(token, ledger)
        elif gate == "CLOSE":
            cmd_close(token, ledger)
        else:
            log_info(f"Production deja terminee ({gate})")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
