# agents/agent3/utils/helpers.py
# SIMPLE helper functions for Agent3

import json
import os
from pathlib import Path


def summarize_repo(repo_path: str):
    """
    Very simple repo summary:
    - Count files
    - List important folders (pages, src, api)
    - Detect language (JS, TS, Python)
    """
    repo_path = Path(repo_path)
    file_list = list(repo_path.rglob("*"))
    file_count = len([f for f in file_list if f.is_file()])

    languages = {"js": 0, "ts": 0, "py": 0}
    for f in file_list:
        if f.suffix == ".js":
            languages["js"] += 1
        elif f.suffix == ".ts":
            languages["ts"] += 1
        elif f.suffix == ".py":
            languages["py"] += 1

    return {
        "file_count": file_count,
        "languages": languages,
        "has_pages_dir": (repo_path / "pages").exists(),
        "has_src_dir": (repo_path / "src").exists(),
        "has_api_folder": (repo_path / "api").exists(),
    }


def save_json(data: dict, path: str | Path):
    """
    Saves JSON with pretty formatting.
    """
    try:
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to save json at {path}: {e}")


def load_json(path: str | Path):
    """
    Loads JSON safely.
    """
    try:
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def load_requirements(requirements_input):
    """
    Ensures requirements are list[str].
    You can pass:
       - a single string
       - list of strings
    """
    if isinstance(requirements_input, str):
        return [requirements_input]
    if isinstance(requirements_input, list):
        return requirements_input
    return []
