# agents/agent3/extractors/route_detector.py
# 2 brain cell explanation:
# We detect ROUTES (pages) using:
# - Next.js pages/ directory
# - React Router <Route path="...">
# - public/index.html
# - fallback: infer from folder names

import re
from pathlib import Path


def detect_nextjs_routes(repo_path):
    """Scan pages/ folder for Next.js routes."""
    repo_path = Path(repo_path)
    pages_dir = repo_path / "pages"

    routes = []

    if pages_dir.exists():
        for f in pages_dir.rglob("*.js"):
            rel = f.relative_to(pages_dir)

            # convert file path → route
            if rel.name == "index.js":
                routes.append("/")
            else:
                route = "/" + str(rel).replace(".js", "")
                route = route.replace("\\", "/")
                routes.append(route)

    return routes


ROUTE_REGEX = re.compile(r'path=["\']([^"\']+)["\']')


def detect_react_router_routes(repo_path):
    """Scan for <Route path="/something"> patterns."""
    repo_path = Path(repo_path)
    routes = []

    for f in repo_path.rglob("*.js"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except:
            continue

        matches = ROUTE_REGEX.findall(text)
        for m in matches:
            if m.startswith("/"):
                routes.append(m)

    return list(set(routes))


def detect_fallback_routes(repo_path):
    """If no router found, create generic fallback routes."""
    fallback = ["/", "/home", "/index"]
    return fallback


def detect_routes(repo_path: str):
    """
    MAIN FUNCTION
    Returns a list of routes the app likely has.
    """

    repo_path = Path(repo_path)

    routes = []

    # 1. Next.js pages
    next_routes = detect_nextjs_routes(repo_path)
    routes.extend(next_routes)

    # 2. React Router
    react_routes = detect_react_router_routes(repo_path)
    routes.extend(react_routes)

    # dedupe
    routes = list(set(routes))

    # 3. If we still have no routes, fallback
    if not routes:
        routes = detect_fallback_routes(repo_path)

    # Ensure "/" exists
    if "/" not in routes:
        routes.insert(0, "/")

    return routes
