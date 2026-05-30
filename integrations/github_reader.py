"""Fetch experiment result files from the Brain-LLM-Fine-Tuning GitHub repo."""

import base64
import httpx
from config.settings import GITHUB_TOKEN, BRAIN_LLM_REPO


HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
BASE = "https://api.github.com"


def list_experiment_files() -> list[dict]:
    """Return metadata for all EXPERIMENT*.md files in the repo root."""
    url = f"{BASE}/repos/{BRAIN_LLM_REPO}/contents/"
    r = httpx.get(url, headers=HEADERS)
    r.raise_for_status()
    return [
        f for f in r.json()
        if f["type"] == "file" and f["name"].startswith("EXPERIMENT") and f["name"].endswith(".md")
    ]


def fetch_file(path: str) -> str:
    """Return the decoded text content of a file in the repo."""
    url = f"{BASE}/repos/{BRAIN_LLM_REPO}/contents/{path}"
    r = httpx.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    return base64.b64decode(data["content"]).decode("utf-8")


def fetch_latest_experiment() -> tuple[str, str]:
    """Return (filename, content) for the most-recently updated EXPERIMENT*.md."""
    files = list_experiment_files()
    if not files:
        raise RuntimeError(f"No EXPERIMENT*.md files found in {BRAIN_LLM_REPO}")
    # Sort by name descending (EXPERIMENT3 > EXPERIMENT2 > EXPERIMENT1)
    files.sort(key=lambda f: f["name"], reverse=True)
    latest = files[0]
    content = fetch_file(latest["path"])
    return latest["name"], content


def fetch_all_experiments() -> list[tuple[str, str]]:
    """Return [(filename, content)] for all experiment files, oldest first."""
    files = sorted(list_experiment_files(), key=lambda f: f["name"])
    return [(f["name"], fetch_file(f["path"])) for f in files]
