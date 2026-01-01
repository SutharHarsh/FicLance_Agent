# agents/agent3/extractors/api_extractor.py
# This extracts backend API shapes WITHOUT LLM.
# 2 brain cell version:
# 1. Look for Express/FastAPI/Next API folders
# 2. Extract endpoints (routes)
# 3. Try runtime probing (if server can start)
# 4. Infer JSON response structure

import os
import json
import re
from pathlib import Path

# Regex for common backend route patterns
ROUTE_PATTERNS = [
    r"app\.get\(['\"](.*?)['\"]",  # Express GET
    r"app\.post\(['\"](.*?)['\"]",  # Express POST
    r"router\.get\(['\"](.*?)['\"]",  # Express Router GET
    r"router\.post\(['\"](.*?)['\"]",  # Express Router POST
    r"@app.get\(['\"](.*?)['\"]",  # FastAPI GET
    r"@app.post\(['\"](.*?)['\"]",  # FastAPI POST
]


def find_backend_files(repo_path):
    """Return all .js, .ts, .py files in backend folders."""
    repo_path = Path(repo_path)

    candidates = []
    backend_dirs = ["api", "backend", "server", "routes", "src", "pages/api"]

    for d in backend_dirs:
        full = repo_path / d
        if full.exists():
            candidates.extend(list(full.rglob("*.js")))
            candidates.extend(list(full.rglob("*.ts")))
            candidates.extend(list(full.rglob("*.py")))

    # fallback: search whole repo if nothing found
    if not candidates:
        candidates = (
            list(repo_path.rglob("*.js"))
            + list(repo_path.rglob("*.ts"))
            + list(repo_path.rglob("*.py"))
        )

    return candidates


def extract_routes_from_file(path):
    """Return list of route strings found in file."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except:
        return []

    found = []
    for pattern in ROUTE_PATTERNS:
        matches = re.findall(pattern, text)
        found.extend(matches)

    # remove duplicates
    return list(set(found))


def infer_json_shape(obj):
    """Very simple shape inference."""
    if isinstance(obj, dict):
        return {k: infer_json_shape(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if len(obj) == 0:
            return "array"
        return ["array", infer_json_shape(obj[0])]
    else:
        return type(obj).__name__


def extract_api_shapes(repo_path: str):
    """
    MAIN FUNCTION — Agent3 calls this.

    Returns:
    {
       "/api/products": {
           "method": "GET",
           "shape": {"id":"int","name":"str"}
       }
    }
    """

    repo_path = Path(repo_path)
    backend_files = find_backend_files(repo_path)

    all_routes = []

    # 1. STATIC ROUTE EXTRACTION
    for f in backend_files:
        routes = extract_routes_from_file(f)
        for r in routes:
            all_routes.append(r)

    all_routes = list(set(all_routes))

    # 2. TRY RUNTIME PROBING (best effort, safe)
    runtime_results = {}
    base_url = "http://localhost:3000"  # You can adjust based on package.json

    try:
        import requests
    except:
        requests = None

    if requests:
        for route in all_routes:
            url = f"{base_url}{route}"
            try:
                r = requests.get(url, timeout=1)
                if r.headers.get("content-type", "").startswith("application/json"):
                    try:
                        json_data = r.json()
                        shape = infer_json_shape(json_data)
                        runtime_results[route] = {
                            "method": "GET",
                            "shape": shape,
                            "status": r.status_code,
                        }
                    except:
                        runtime_results[route] = {"method": "GET", "shape": "non-json"}
                else:
                    runtime_results[route] = {"method": "GET", "shape": "non-json"}
            except:
                runtime_results[route] = {"error": "unreachable"}
    else:
        runtime_results = {
            route: {"error": "requests_not_installed"} for route in all_routes
        }

    # 3. FINAL STRUCTURE
    final = {"discovered_routes": all_routes, "runtime_shapes": runtime_results}

    return final
