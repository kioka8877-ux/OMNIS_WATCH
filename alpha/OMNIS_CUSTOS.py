"""
OMNIS_CUSTOS.py — Gardien de Flotte OMNIS-WATCH
================================================
Valide les fichiers IN/ et OUT/ de chaque fregate avant et apres tout transfert.
Stdlib uniquement — aucune dependance externe.

Usage:
  python OMNIS_CUSTOS.py --frigate F01 --mode check-out [--base /path/to/alpha]
  python OMNIS_CUSTOS.py --frigate F01 --mode check-in [--base /path/to/alpha]

Exit codes:
  0 = VALIDATION OK
  1 = VALIDATION FAIL
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Configuration ───────────────────────────────────────────────────────────

DEFAULT_BASE = "."

# Manifeste de validation par fregate et par mode
# check-out : verifie que les fichiers d'ENTREE sont presents avant de lancer la fregate
# check-in  : verifie que les fichiers de SORTIE sont presents et valides apres la fregate
MANIFEST = {
    "F01": {
        "check-out": {
            "files": [
                {"path": "F01_ACQUISITION/IN/video_raw.mp4", "type": "file", "min_size": 10000},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F01_ACQUISITION/OUT/video_coupee.mp4", "type": "file", "min_size": 5000},
                {"path": "F01_ACQUISITION/OUT/f01_manifest.json", "type": "json",
                 "required_keys": ["meta", "input", "output"]},
            ],
        },
    },
    "F02A": {
        "check-out": {
            "files": [
                {"path": "F02_ANALYSIS/F02A_VISION/IN/video_coupee.mp4", "type": "file", "min_size": 5000},
                {"path": "F02_ANALYSIS/F02A_VISION/IN/f01_manifest.json", "type": "json",
                 "required_keys": ["meta"]},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F02_ANALYSIS/F02A_VISION/OUT/narrative.txt", "type": "file", "min_size": 50},
                {"path": "F02_ANALYSIS/F02A_VISION/OUT/tracking_data.json", "type": "json",
                 "required_keys": ["target_type", "fps", "tracks"]},
            ],
        },
    },
    "F02B": {
        "check-out": {
            "files": [
                {"path": "F02_ANALYSIS/F02B_ORACLE/IN/narrative.txt", "type": "file", "min_size": 50},
                {"path": "F02_ANALYSIS/F02B_ORACLE/IN/f01_manifest.json", "type": "json",
                 "required_keys": ["meta"]},
            ],
            "optional": [
                {"path": "F02_ANALYSIS/F02B_ORACLE/IN/tracking_data.json", "type": "json",
                 "required_keys": ["tracks"]},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F02_ANALYSIS/F02B_ORACLE/OUT/codex.json", "type": "json",
                 "required_keys": ["version", "emotion_mode", "video", "text_overlays",
                                   "zoom_keyframes", "sfx_timeline"]},
            ],
        },
    },
    "F03A": {
        "check-out": {
            "files": [
                {"path": "F03_RENDER/F03A_REMOTION/IN/codex.json", "type": "json",
                 "required_keys": ["video", "text_overlays"]},
                {"path": "F03_RENDER/F03A_REMOTION/IN/video_coupee.mp4", "type": "file", "min_size": 5000},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F03_RENDER/F03A_REMOTION/OUT/video_visuelle.mp4", "type": "file", "min_size": 5000},
            ],
        },
    },
    "F03B": {
        "check-out": {
            "files": [
                {"path": "F03_RENDER/F03B_MIXER/IN/video_visuelle.mp4", "type": "file", "min_size": 5000},
                {"path": "F03_RENDER/F03B_MIXER/IN/codex.json", "type": "json",
                 "required_keys": ["sfx_timeline"]},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F03_RENDER/F03B_MIXER/OUT/video_complete.mp4", "type": "file", "min_size": 5000},
            ],
        },
    },
    "F04": {
        "check-out": {
            "files": [
                {"path": "F04_CAMOUFLAGE/IN/video_complete.mp4", "type": "file", "min_size": 5000},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F04_CAMOUFLAGE/OUT/youtube_final.mp4", "type": "file", "min_size": 5000},
                {"path": "F04_CAMOUFLAGE/OUT/rapport_f04.html", "type": "file", "min_size": 100},
            ],
        },
    },
    "F05": {
        "check-out": {
            "files": [
                {"path": "F05_LUTHER/IN/youtube_final.mp4", "type": "file", "min_size": 5000},
            ],
        },
        "check-in": {
            "files": [
                {"path": "F05_LUTHER/OUT/clean_final.mp4", "type": "file", "min_size": 5000},
            ],
        },
    },
}

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

# ── Validation ──────────────────────────────────────────────────────────────

def validate_file(path, spec, base):
    """Valide un fichier selon sa spec."""
    full_path = os.path.join(base, spec["path"])
    errors = 0

    if not os.path.exists(full_path):
        log_fail(f"Manquant: {spec['path']}")
        return 1

    if spec.get("type") == "file":
        size = os.path.getsize(full_path)
        min_size = spec.get("min_size", 0)
        if size < min_size:
            log_fail(f"Trop petit: {spec['path']} ({size} bytes < {min_size})")
            errors += 1
        else:
            log_ok(f"OK: {spec['path']} ({size / 1024:.1f} KB)")

    elif spec.get("type") == "json":
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            log_ok(f"JSON valide: {spec['path']}")

            # Verifier les cles requises
            required_keys = spec.get("required_keys", [])
            for key in required_keys:
                if key not in data:
                    log_fail(f"Cle manquante dans {spec['path']}: '{key}'")
                    errors += 1
                else:
                    log_ok(f"  cle '{key}' presente")

        except json.JSONDecodeError as e:
            log_fail(f"JSON invalide: {spec['path']} — {e}")
            errors += 1
        except Exception as e:
            log_fail(f"Erreur lecture: {spec['path']} — {e}")
            errors += 1

    return errors

def validate_frigate(frigate, mode, base):
    """Valide une fregate dans un mode donne."""
    if frigate not in MANIFEST:
        log_fail(f"Fregate inconnue: {frigate}")
        log_info(f"Fregates valides: {', '.join(MANIFEST.keys())}")
        return 1

    if mode not in MANIFEST[frigate]:
        log_fail(f"Mode inconnu pour {frigate}: {mode}")
        return 1

    spec = MANIFEST[frigate][mode]
    errors = 0

    print()
    print(f"{'═' * 52}")
    print(f" CUSTOS — Validation {frigate} {mode}")
    print(f" Base: {base}")
    print(f"{'═' * 52}")
    print()

    # Fichiers obligatoires
    for file_spec in spec.get("files", []):
        errors += validate_file(file_spec, file_spec, base)

    # Fichiers optionnels (warning seulement si manquants)
    for opt_spec in spec.get("optional", []):
        full_path = os.path.join(base, opt_spec["path"])
        if os.path.exists(full_path):
            errors += validate_file(opt_spec, opt_spec, base)
        else:
            log_warn(f"Optionnel manquant: {opt_spec['path']}")

    # Resultat
    print()
    if errors == 0:
        print(f" {'═' * 48}")
        print(f" VALIDATION OK — {frigate} {mode} : Aucune erreur.")
        print(f" {'═' * 48}")
        return 0
    else:
        print(f" {'═' * 48}")
        print(f" VALIDATION FAIL — {errors} erreur(s) detectee(s). Transit interdit.")
        print(f" {'═' * 48}")
        return 1

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OMNIS_CUSTOS — Gardien de Flotte"
    )
    parser.add_argument("--frigate", required=True,
                        choices=list(MANIFEST.keys()),
                        help="Fregate a valider (F01, F02A, F02B, F03A, F03B, F04, F05)")
    parser.add_argument("--mode", required=True,
                        choices=["check-out", "check-in"],
                        help="Mode de validation (check-out = avant, check-in = apres)")
    parser.add_argument("--base", default=DEFAULT_BASE,
                        help=f"Dossier de base (defaut: {DEFAULT_BASE})")

    args = parser.parse_args()

    exit_code = validate_frigate(args.frigate, args.mode, args.base)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
