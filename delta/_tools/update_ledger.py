import json
import os
import sys


def main():
    gate = sys.argv[1]
    ledger_path = sys.argv[2] if len(sys.argv) > 2 else "delta/omnis_ledger.json"
    
    if os.path.exists(ledger_path):
        with open(ledger_path) as f:
            ledger = json.load(f)
    else:
        ledger = {}
    
    ledger["gate_actuelle"] = gate
    ledger["derniere_mise_a_jour"] = os.popen("date -u '+%Y-%m-%dT%H:%M:%S'").read().strip()
    
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=2)
    
    print(f"Ledger updated: gate={gate}")


if __name__ == "__main__":
    main()
