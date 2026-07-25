"""
OMNIS_EXECUTEUR.py — Orchestrateur OMNIS-WATCH (GitHub Actions Edition)
======================================================================
Sandbox = telecommande + Oracle.
Toutes les fregates tournent sur GitHub Actions.
L'operateur intervient aux 4 gates.

Usage:
  python OMNIS_EXECUTEUR.py --start --title "Mon sujet"
  python OMNIS_EXECUTEUR.py --gate G2    # Telecharge F01, lance F02A/F02B, preview
  python OMNIS_EXECUTEUR.py --gate G3    # Trigger F03A + F03B sur GH Actions
  python OMNIS_EXECUTEUR.py --gate G4    # Telecharge F03, trigger F04 sur GH
  python OMNIS_EXECUTEUR.py --close      # Telecharge artefact final F04
  python OMNIS_EXECUTEUR.py --resume     # Reprendre depuis ledger

Variables d'environnement requises:
  GH_TOKEN — token GitHub (scope: repo)
  OPENROUTER_API_KEY — cle API OpenRouter (pour F02A vision)
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

# ── Dependance requests (auto-install si absente) ──────────────────────────
try:
    import requests
except ImportError:
    print("[SETUP] Installation de requests...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "requests",
        "--quiet", "--break-system-packages"
    ])
    import requests

# ── Chemins ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
LEDGER_PATH = SCRIPT_DIR / "omnis_ledger.json"
REPO_NAME = "kioka8877-ux/OMNIS_WATCH"
MODE = "alpha"
GH_API = "https://api.github.com/repos"

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Ledger ──────────────────────────────────────────────────────────────────

def load_ledger():
    """Charge le ledger depuis le fichier JSON."""
    if not LEDGER_PATH.exists():
        log_fail(f"Ledger introuvable: {LEDGER_PATH}")
        sys.exit(1)
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ledger(ledger):
    """Sauvegarde le ledger."""
    ledger["derniere_mise_a_jour"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    log_ok(f"Ledger sauvegarde: gate={ledger['gate_actuelle']}")

# ── GitHub Actions ──────────────────────────────────────────────────────────

def gh_headers(token):
    """Headers pour l'API GitHub."""
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

def trigger_workflow(token, workflow_filename, ref="main", inputs=None):
    """Declenche un workflow GitHub Actions."""
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
    """Recupere les derniers runs d'un workflow."""
    url = f"{GH_API}/{REPO_NAME}/actions/workflows/{workflow_filename}/runs"
    params = {"per_page": limit}
    resp = requests.get(url, headers=gh_headers(token), params=params)
    if resp.status_code != 200:
        log_fail(f"Erreur recuperation runs: {resp.status_code}")
        return []
    return resp.json().get("workflow_runs", [])

def wait_for_run(token, run_id, timeout=600, interval=15):
    """Attend qu'un run GitHub Actions se termine."""
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
    """Telecharge un artifact d'un run GitHub Actions."""
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

    # Telecharger l'artifact
    download_url = target["archive_download_url"]
    resp = requests.get(download_url, headers=gh_headers(token))
    if resp.status_code != 200:
        log_fail(f"Erreur download artifact: {resp.status_code}")
        return None

    # Extraire le zip
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(output_dir)

    log_ok(f"Artifact telecharge: {artifact_name} -> {output_dir}")
    return output_dir

def get_latest_run_id(token, workflow_filename):
    """Recupere l'ID du dernier run d'un workflow."""
    runs = get_workflow_runs(token, workflow_filename, limit=1)
    if not runs:
        return None
    return runs[0]["id"]

# ── Commandes ───────────────────────────────────────────────────────────────

def cmd_start(title, token, ledger):
    """Gate G1 — Initialise une production."""
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

    # L'operateur doit placer video_raw.mp4 dans SHARED/IN/
    video_path = SCRIPT_DIR / "SHARED" / "IN" / "video_raw.mp4"
    if not video_path.exists():
        log_warn("video_raw.mp4 non trouve dans SHARED/IN/")
        log_info("Placez votre video dans alpha/SHARED/IN/video_raw.mp4")
        log_info("Puis relancez: python OMNIS_EXECUTEUR.py --start --title \"...\"")
        save_ledger(ledger)
        return

    log_ok(f"Video source: {video_path}")

    # Copier vers F01 IN/
    f01_in = SCRIPT_DIR / "F01_ACQUISITION" / "IN"
    f01_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(video_path, f01_in / "video_raw.mp4")
    log_ok("Video copiee vers F01_ACQUISITION/IN/")

    # Custos check-out F01
    section("CUSTOS — Validation F01 check-out")
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", "F01", "--mode", "check-out",
        "--base", str(SCRIPT_DIR)
    ])
    if result.returncode != 0:
        log_fail("CUSTOS F01 check-out a echoue — production bloquee")
        save_ledger(ledger)
        return

    # Trigger F01 sur GitHub Actions
    section("Trigger F01 sur GitHub Actions")
    inputs = {
        "mode": MODE,
        "in_timestamp": "00:00",
        "out_timestamp": "00:15",
        "format": "9:16",
        "blur_pad": "true",
        "speed": "1.0",
        "volume": "1.0",
    }

    # Permettre a l'operateur de customiser les parametres
    print()
    log_info("Parametres F01 par defaut:")
    for k, v in inputs.items():
        print(f"  {k} = {v}")
    print()
    log_info("Pour customiser, modifiez le ledger ou utilisez les inputs du workflow GH Actions")

    if trigger_workflow(token, "f01_acquisition.yml", inputs=inputs):
        log_info("En attente du run F01...")
        time.sleep(5)  # Laisser le temps au workflow de demarrer
        run_id_gh = get_latest_run_id(token, "f01_acquisition.yml")
        if run_id_gh:
            ledger["gh_runs"]["f01"] = run_id_gh
            log_ok(f"Run F01 GitHub Actions: #{run_id_gh}")
            save_ledger(ledger)
            print()
            print(f"{'═' * 52}")
            print(f" GATE G1 — F01 lance sur GitHub Actions")
            print(f" Run: #{run_id_gh}")
            print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
            print(f" Quand F01 est termine, lancez: --gate G2")
            print(f"{'═' * 52}")
    else:
        log_fail("Echec du trigger F01")
        save_ledger(ledger)

def cmd_gate_g2(token, ledger):
    """Gate G2 — Telecharge F01, lance F02A (tracking GH) + F02B (Oracle sandbox)."""
    section("GATE G2 — Analyse et generation")

    # 1. Telecharger l'artifact F01
    f01_run_id = ledger.get("gh_runs", {}).get("f01")
    if not f01_run_id:
        log_fail("Aucun run F01 dans le ledger")
        return

    section("Telechargement artifact F01")
    f01_out = SCRIPT_DIR / "F01_ACQUISITION" / "OUT"
    f01_out.mkdir(parents=True, exist_ok=True)

    # Verifier si F01 est termine
    success, run_data = wait_for_run(token, f01_run_id, timeout=30, interval=5)
    if not success:
        log_fail(f"Run F01 #{f01_run_id} non termine ou echoue")
        log_info(f"Verifiez: https://github.com/{REPO_NAME}/actions/runs/{f01_run_id}")
        return

    # Telecharger l'artifact
    artifact_dir = download_artifact(token, f01_run_id, "f01-output", str(f01_out))
    if not artifact_dir:
        log_fail("Impossible de telecharger l'artifact F01")
        return

    # Custos check-in F01
    section("CUSTOS — Validation F01 check-in")
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", "F01", "--mode", "check-in",
        "--base", str(SCRIPT_DIR)
    ])
    if result.returncode != 0:
        log_fail("CUSTOS F01 check-in a echoue")
        return

    # Mettre a jour le ledger
    ledger["etapes_completees"].append("F01")
    ledger["artefacts"]["video_coupee"] = "F01_ACQUISITION/OUT/video_coupee.mp4"
    ledger["artefacts"]["f01_manifest"] = "F01_ACQUISITION/OUT/f01_manifest.json"

    # Lire le manifest pour les metadonnees
    manifest_path = f01_out / "f01_manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        ledger["f01_meta"] = manifest["meta"]
        log_ok(f"F01 meta: {manifest['meta']['duration_seconds']}s, "
               f"{manifest['meta']['total_frames']} frames")

    # 2. Copier vers F02A IN/
    section("Preparation F02A")
    f02a_in = SCRIPT_DIR / "F02_ANALYSIS" / "F02A_VISION" / "IN"
    f02a_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f01_out / "video_coupee.mp4", f02a_in / "video_coupee.mp4")
    shutil.copy2(f01_out / "f01_manifest.json", f02a_in / "f01_manifest.json")
    log_ok("Fichiers copies vers F02A_VISION/IN/")

    # 3. Custos check-out F02A
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", "F02A", "--mode", "check-out",
        "--base", str(SCRIPT_DIR)
    ])
    if result.returncode != 0:
        log_fail("CUSTOS F02A check-out a echoue")
        save_ledger(ledger)
        return

    # 4. Trigger F02A tracking sur GitHub Actions
    section("Trigger F02A Tracking sur GitHub Actions")
    if trigger_workflow(token, "f02a_tracking.yml", inputs={
        "mode": MODE,
        "target_type": "face",
    }):
        time.sleep(5)
        f02a_run_id = get_latest_run_id(token, "f02a_tracking.yml")
        if f02a_run_id:
            ledger["gh_runs"]["f02a_tracking"] = f02a_run_id
            log_ok(f"Run F02A tracking: #{f02a_run_id}")

    # 5. F02A Vision — description OpenRouter (se fait dans le sandbox)
    section("F02A Vision — Description OpenRouter")
    log_info("La description OpenRouter se fait dans le sandbox (Oracle)")
    log_info("Lancez manuellement:")
    log_info(f"  python F02_ANALYSIS/F02A_VISION/CODEBASE/omnis_f02a_vision.py \\")
    log_info(f"    --input F02_ANALYSIS/F02A_VISION/IN/ \\")
    log_info(f"    --output F02_ANALYSIS/F02A_VISION/OUT/ \\")
    log_info(f"    --api-key $OPENROUTER_API_KEY")

    # 6. F02B Oracle — generation du codex (se fait dans le sandbox)
    section("F02B Oracle — Generation du codex")
    log_info("L'Oracle (sandbox AI) genere le codex.json")
    log_info("1. Preparez le prompt:")
    log_info(f"  python F02_ANALYSIS/F02B_ORACLE/CODEBASE/omnis_f02b_oracle.py \\")
    log_info(f"    --input F02_ANALYSIS/F02B_ORACLE/IN/ \\")
    log_info(f"    --output F02_ANALYSIS/F02B_ORACLE/OUT/ \\")
    log_info(f"    --emotion-mode TRISTE --prepare")
    log_info("2. L'Oracle genere le codex base sur le prompt")
    log_info("3. Validez le codex:")
    log_info(f"  python F02_ANALYSIS/F02B_ORACLE/CODEBASE/omnis_f02b_oracle.py \\")
    log_info(f"    --input F02_ANALYSIS/F02B_ORACLE/IN/ \\")
    log_info(f"    --output F02_ANALYSIS/F02B_ORACLE/OUT/ \\")
    log_info(f"    --emotion-mode TRISTE --validate <codex_genere.json>")

    # 7. F02 Preview
    section("F02 Preview")
    log_info("Une fois le codex.json valide:")
    log_info("1. Copiez codex.json + video_coupee.mp4 vers F02_PREVIEW/public/")
    log_info("2. Build: cd F02_PREVIEW && npm install && npm run build")
    log_info("3. Ouvrez dist/index.html dans le navigateur")
    log_info("4. Validez le preview → passez a G3")

    ledger["gate_actuelle"] = "G2"
    save_ledger(ledger)

    print()
    print(f"{'═' * 52}")
    print(f" GATE G2 — En attente de validation operateur")
    print(f" 1. F02A tracking: GitHub Actions (surveiller)")
    print(f" 2. F02A vision: Oracle sandbox (manuel)")
    print(f" 3. F02B oracle: Oracle sandbox (manuel)")
    print(f" 4. F02 preview: build + validation visuelle")
    print(f" Quand tout est valide: --gate G3")
    print(f"{'═' * 52}")

def cmd_gate_g3(token, ledger):
    """Gate G3 — Trigger F03A + F03B sur GitHub Actions."""
    section("GATE G3 — Rendu visuel + mixage")

    # Verifier que F02B est complete
    codex_path = SCRIPT_DIR / "F02_ANALYSIS" / "F02B_ORACLE" / "OUT" / "codex.json"
    if not codex_path.exists():
        log_fail("codex.json non trouve dans F02B_ORACLE/OUT/")
        log_info("Completez F02B d'abord (Gate G2)")
        return

    # Copier codex + video vers F03A IN/
    section("Preparation F03A")
    f03a_in = SCRIPT_DIR / "F03_RENDER" / "F03A_REMOTION" / "IN"
    f03a_in.mkdir(parents=True, exist_ok=True)

    video_coupee = SCRIPT_DIR / "F01_ACQUISITION" / "OUT" / "video_coupee.mp4"
    if video_coupee.exists():
        shutil.copy2(video_coupee, f03a_in / "video_coupee.mp4")
    shutil.copy2(codex_path, f03a_in / "codex.json")
    log_ok("Fichiers copies vers F03A_REMOTION/IN/")

    # Custos check-out F03A
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", "F03A", "--mode", "check-out",
        "--base", str(SCRIPT_DIR)
    ])
    if result.returncode != 0:
        log_fail("CUSTOS F03A check-out a echoue")
        return

    # Trigger F03A sur GitHub Actions
    section("Trigger F03A sur GitHub Actions")
    if trigger_workflow(token, "f03a_render.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f03a_run_id = get_latest_run_id(token, "f03a_render.yml")
        if f03a_run_id:
            ledger["gh_runs"]["f03a"] = f03a_run_id
            log_ok(f"Run F03A: #{f03a_run_id}")

            # Attendre la fin de F03A
            log_info("En attente de F03A (peut prendre plusieurs minutes)...")
            success, _ = wait_for_run(token, f03a_run_id, timeout=1800, interval=30)
            if not success:
                log_fail("F03A a echoue ou timeout")
                save_ledger(ledger)
                return

            # Telecharger l'artifact F03A
            f03a_out = SCRIPT_DIR / "F03_RENDER" / "F03A_REMOTION" / "OUT"
            f03a_out.mkdir(parents=True, exist_ok=True)
            download_artifact(token, f03a_run_id, "f03a-output", str(f03a_out))

    # Preparer F03B
    section("Preparation F03B")
    f03b_in = SCRIPT_DIR / "F03_RENDER" / "F03B_MIXER" / "IN"
    f03b_in.mkdir(parents=True, exist_ok=True)

    f03a_out = SCRIPT_DIR / "F03_RENDER" / "F03A_REMOTION" / "OUT"
    video_visuelle = f03a_out / "video_visuelle.mp4"
    if video_visuelle.exists():
        shutil.copy2(video_visuelle, f03b_in / "video_visuelle.mp4")
    shutil.copy2(codex_path, f03b_in / "codex.json")
    log_ok("Fichiers copies vers F03B_MIXER/IN/")

    # Trigger F03B
    section("Trigger F03B sur GitHub Actions")
    if trigger_workflow(token, "f03b_mixer.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f03b_run_id = get_latest_run_id(token, "f03b_mixer.yml")
        if f03b_run_id:
            ledger["gh_runs"]["f03b"] = f03b_run_id
            log_ok(f"Run F03B: #{f03b_run_id}")

    ledger["etapes_completees"].extend(["F02A", "F02B", "F03A"])
    ledger["gate_actuelle"] = "G3"
    save_ledger(ledger)

    print()
    print(f"{'═' * 52}")
    print(f" GATE G3 — F03A + F03B lances sur GitHub Actions")
    print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
    print(f" Quand F03B est termine: --gate G4")
    print(f"{'═' * 52}")

def cmd_gate_g4(token, ledger):
    """Gate G4 — Telecharge F03B, trigger F04 sur GitHub Actions."""
    section("GATE G4 — Camouflage")

    # Telecharger F03B
    f03b_run_id = ledger.get("gh_runs", {}).get("f03b")
    if not f03b_run_id:
        log_fail("Aucun run F03B dans le ledger")
        return

    success, _ = wait_for_run(token, f03b_run_id, timeout=300, interval=15)
    if not success:
        log_fail(f"Run F03B #{f03b_run_id} non termine")
        return

    f03b_out = SCRIPT_DIR / "F03_RENDER" / "F03B_MIXER" / "OUT"
    f03b_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, f03b_run_id, "f03b-output", str(f03b_out))

    # Custos check-in F03B
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", "F03B", "--mode", "check-in",
        "--base", str(SCRIPT_DIR)
    ])
    if result.returncode != 0:
        log_fail("CUSTOS F03B check-in a echoue")
        return

    # Preparer F04
    section("Preparation F04")
    f04_in = SCRIPT_DIR / "F04_CAMOUFLAGE" / "IN"
    f04_in.mkdir(parents=True, exist_ok=True)

    video_complete = f03b_out / "video_complete.mp4"
    if video_complete.exists():
        shutil.copy2(video_complete, f04_in / "video_complete.mp4")
    log_ok("Fichiers copies vers F04_CAMOUFLAGE/IN/")

    # Trigger F04
    section("Trigger F04 sur GitHub Actions")
    if trigger_workflow(token, "f04_camouflage.yml", inputs={"mode": MODE}):
        time.sleep(5)
        f04_run_id = get_latest_run_id(token, "f04_camouflage.yml")
        if f04_run_id:
            ledger["gh_runs"]["f04"] = f04_run_id
            log_ok(f"Run F04: #{f04_run_id}")

    ledger["etapes_completees"].extend(["F03B"])
    ledger["gate_actuelle"] = "G4"
    save_ledger(ledger)

    print()
    print(f"{'═' * 52}")
    print(f" GATE G4 — F04 lance sur GitHub Actions")
    print(f" Surveillez: https://github.com/{REPO_NAME}/actions")
    print(f" Quand F04 est termine: --close")
    print(f"{'═' * 52}")

def cmd_close(token, ledger):
    """Close — Telecharge l'artifact final F04."""
    section("CLOSE — Telechargement final")

    f04_run_id = ledger.get("gh_runs", {}).get("f04")
    if not f04_run_id:
        log_fail("Aucun run F04 dans le ledger")
        return

    success, _ = wait_for_run(token, f04_run_id, timeout=300, interval=15)
    if not success:
        log_fail(f"Run F04 #{f04_run_id} non termine")
        return

    f04_out = SCRIPT_DIR / "F04_CAMOUFLAGE" / "OUT"
    f04_out.mkdir(parents=True, exist_ok=True)
    download_artifact(token, f04_run_id, "f04-output", str(f04_out))

    # Custos check-in F04
    result = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "OMNIS_CUSTOS.py"),
        "--frigate", "F04", "--mode", "check-in",
        "--base", str(SCRIPT_DIR)
    ])

    # Mettre a jour le ledger
    ledger["etapes_completees"].append("F04")
    ledger["artefacts"]["youtube_final"] = "F04_CAMOUFLAGE/OUT/youtube_final.mp4"
    ledger["gate_actuelle"] = "CLOSE"
    ledger["statut"] = "TERMINE"
    save_ledger(ledger)

    print()
    print(f"{'═' * 52}")
    print(f" VICTORIA AETERNA — Production terminee")
    print(f" Fichier final: F04_CAMOUFLAGE/OUT/youtube_final.mp4")
    print(f"{'═' * 52}")

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OMNIS_EXECUTEUR — Orchestrateur OMNIS-WATCH"
    )
    parser.add_argument("--start", action="store_true", help="Initialiser une production")
    parser.add_argument("--title", help="Titre de la production (avec --start)")
    parser.add_argument("--gate", choices=["G2", "G3", "G4"], help="Passer a une gate")
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

    elif args.close:
        cmd_close(token, ledger)

    elif args.resume:
        gate = ledger.get("gate_actuelle", "G1")
        print(f"[RESUME] Reprise a gate {gate}")
        if gate == "G1":
            log_info("Placez video_raw.mp4 dans SHARED/IN/ et relancez --start")
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
