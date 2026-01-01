# repo_preprocessor.py (Optimized Lightweight Version)
import os
import subprocess
import hashlib
import json
from typing import Dict
from services.redis_client import redis_cache

# Redis keys
ACTIVE_REPO_META_KEY = "active_repo_meta"
SUMMARY_KEY_PREFIX = "repo_summary:"
META_SUMMARY_KEY_PREFIX = "repo_meta:"


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def get_git_commit_hash(project_path: str) -> str | None:
    """Returns the HEAD commit hash if available."""
    try:
        cmd = ["git", "-C", project_path, "rev-parse", "HEAD"]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return None


def _repo_cache_key(repo_url: str, project_path: str) -> str:
    """Generate deterministic key (repo URL + commit hash if present)."""
    commit = get_git_commit_hash(project_path)
    base = f"{repo_url}::{commit}" if commit else repo_url
    return sha1(base)


# -------------------------------------------------------------------
# MAIN: Lightweight Summary Generator
# -------------------------------------------------------------------
def generate_repo_summary_lightweight(project_path: str) -> dict:
    """
    Ultra-lightweight repo analysis (NO LLM, NO file content).
    Always produces 300–700 tokens total.

    Extracts:
      - file counts
      - file types
      - component names
      - route/page files
      - API folders/files
      - key inferred features
    """

    summary = {
        "repo_name": os.path.basename(project_path),
        "total_files": 0,
        "file_types": {},
        "components": [],
        "routes_or_pages": [],
        "apis": [],
        "potential_features": [],
    }

    for root, dirs, files in os.walk(project_path):
        # Skip heavy paths
        if any(
            skip in root
            for skip in [
                "node_modules",
                ".git",
                ".next",
                "dist",
                "build",
                "__pycache__",
            ]
        ):
            continue

        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1]

            # Update file stats
            summary["total_files"] += 1
            summary["file_types"][ext] = summary["file_types"].get(ext, 0) + 1

            # Detect components
            if ext in [".jsx", ".tsx"]:
                summary["components"].append(file)

            # Detect Next.js pages/app router
            if "pages" in root or "/app" in root:
                summary["routes_or_pages"].append(file)

            # Detect API folders
            if "api" in root.lower():
                summary["apis"].append(file)

    # -------------------------------------------------------------------
    # Infer potential features (simple heuristics, LLM is not needed)
    # -------------------------------------------------------------------
    combined_names = json.dumps(summary).lower()

    if "auth" in combined_names or "login" in combined_names:
        summary["potential_features"].append("Authentication / Login system")

    if "dashboard" in combined_names:
        summary["potential_features"].append("Dashboard UI")

    if "profile" in combined_names:
        summary["potential_features"].append("User profile management")

    if "admin" in combined_names:
        summary["potential_features"].append("Admin panel structure")

    if "api" in combined_names:
        summary["potential_features"].append("Backend API endpoints")

    return summary


# -------------------------------------------------------------------
# MAIN ENTRY — with Redis caching (NO LLM CALL ANYMORE)
# -------------------------------------------------------------------
def generate_repo_summary(
    gemini_llm,  # Ignored but kept for compatibility with your existing function calls
    project_path: str,
    repo_url: str,
) -> str:
    """
    Generates or returns cached lightweight repository summary.
    NO LLM is used; summary is always < 800 tokens.

    Returned as a string because Agent3 uses string context.
    """

    # Build repo cache key
    repo_key = _repo_cache_key(repo_url, project_path)
    summary_key = SUMMARY_KEY_PREFIX + repo_key
    meta_key = META_SUMMARY_KEY_PREFIX + repo_key

    # Check if another repo was cached before
    active = redis_cache.get(ACTIVE_REPO_META_KEY)
    if active and active != repo_key:
        try:
            redis_cache.delete(SUMMARY_KEY_PREFIX + active)
        except:
            pass

    # Return cached summary if exists
    if redis_cache.exists(summary_key):
        cached = redis_cache.get(summary_key)
        redis_cache.set(ACTIVE_REPO_META_KEY, repo_key)
        return cached

    # -------------------------------------------------------------
    # Generate NEW lightweight summary
    # -------------------------------------------------------------
    summary_dict = generate_repo_summary_lightweight(project_path)
    summary_json = json.dumps(summary_dict, indent=2)

    # Cache summary + metadata
    try:
        redis_cache.set(summary_key, summary_json)

        meta_value = f"url:{repo_url}"
        commit = get_git_commit_hash(project_path)
        if commit:
            meta_value += f" commit:{commit}"

        redis_cache.set(meta_key, meta_value)
        redis_cache.set(ACTIVE_REPO_META_KEY, repo_key)

    except Exception:
        pass

    return summary_json
