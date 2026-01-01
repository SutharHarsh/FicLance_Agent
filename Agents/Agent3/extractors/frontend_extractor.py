# agents/agent3/extractors/frontend_extractor.py
# 2 brain cell explanation:
# - Find frontend source files
# - Detect API calls: fetch(), axios.get(), axios.post()
# - Detect data usage: x.name, x.price, product.title etc.
# - Map route -> fields used by UI

import re
from pathlib import Path

# REGEX for detecting fetch/axios API calls
FETCH_REGEX = re.compile(r"fetch\(['\"]([^'\"]+)['\"]")
AXIOS_GET_REGEX = re.compile(r"axios\.get\(['\"]([^'\"]+)['\"]")
AXIOS_POST_REGEX = re.compile(r"axios\.post\(['\"]([^'\"]+)['\"]")

# REGEX for detecting data usage (like product.title, item.price)
DOT_ACCESS_REGEX = re.compile(r"[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+")


def find_frontend_files(repo_path):
    """Return all .js, .jsx, .ts, .tsx files inside src/, pages/, components/."""
    repo_path = Path(repo_path)
    folders = ["src", "pages", "components"]

    files = []
    for f in folders:
        full = repo_path / f
        if full.exists():
            files.extend(list(full.rglob("*.js")))
            files.extend(list(full.rglob("*.jsx")))
            files.extend(list(full.rglob("*.ts")))
            files.extend(list(full.rglob("*.tsx")))

    if not files:
        # fallback: search entire repo
        files = list(repo_path.rglob("*.js")) + list(repo_path.rglob("*.jsx"))

    return files


def extract_api_calls(text):
    """Return list of API endpoints used by fetch or axios."""
    calls = []

    calls.extend(FETCH_REGEX.findall(text))
    calls.extend(AXIOS_GET_REGEX.findall(text))
    calls.extend(AXIOS_POST_REGEX.findall(text))

    # Remove external URLs (only keep local API calls)
    local_calls = [c for c in calls if c.startswith("/") and not c.startswith("http")]

    return list(set(local_calls))


def extract_used_fields(text):
    """Detect patterns like product.name, item.price, user.email."""
    matches = DOT_ACCESS_REGEX.findall(text)

    fields = []
    for m in matches:
        if "." in m:
            parent, field = m.split(".", 1)
            fields.append(field.strip())

    # remove duplicates
    return list(set(fields))


def extract_frontend_usage(repo_path: str):
    """
    MAIN FUNCTION — returns:
    {
        "api_calls": {
            "/api/products": ["title", "price", "image"],
            "/api/cart": ["items"]
        }
    }
    """

    files = find_frontend_files(repo_path)
    route_to_fields = {}

    for f in files:
        try:
            text = Path(f).read_text(encoding="utf-8", errors="ignore")
        except:
            continue

        api_calls = extract_api_calls(text)
        fields = extract_used_fields(text)

        for route in api_calls:
            if route not in route_to_fields:
                route_to_fields[route] = []

            route_to_fields[route].extend(fields)

    # dedupe
    final = {route: list(set(fields)) for route, fields in route_to_fields.items()}

    return {"frontend_api_usage": final}
