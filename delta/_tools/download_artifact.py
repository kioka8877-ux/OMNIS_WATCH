import io
import json
import os
import sys
import zipfile

import requests

REPO = "kioka8877-ux/OMNIS_WATCH"
GH_API = "https://api.github.com/repos"


def main():
    token = sys.argv[1]
    workflow = sys.argv[2]
    artifact_name = sys.argv[3]
    output_dir = sys.argv[4]
    branch = sys.argv[5] if len(sys.argv) > 5 else "main"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    runs_url = f"{GH_API}/{REPO}/actions/workflows/{workflow}/runs"
    page = 1
    run_id = None
    found = False
    while page <= 10 and not found:
        params = {"per_page": 20, "status": "success", "page": page}
        if branch:
            params["branch"] = branch
        runs = requests.get(runs_url, headers=headers, params=params).json()
        if not runs.get("workflow_runs"):
            break
        for run in runs["workflow_runs"]:
            run_id = run["id"]
            arts_url = f"{GH_API}/{REPO}/actions/runs/{run_id}/artifacts"
            arts = requests.get(arts_url, headers=headers).json()
            for a in arts.get("artifacts", []):
                if a["name"] == artifact_name:
                    print(f"Run #{run_id}")
                    dl = requests.get(a["archive_download_url"], headers=headers)
                    z = zipfile.ZipFile(io.BytesIO(dl.content))
                    os.makedirs(output_dir, exist_ok=True)
                    z.extractall(output_dir)
                    print(f"Extracted {artifact_name} -> {output_dir}")
                    found = True
                    break
            if found:
                break
        page += 1

    if not found:
        print(f"Artifact {artifact_name} not found in last successful runs")
        sys.exit(1)


if __name__ == "__main__":
    main()
