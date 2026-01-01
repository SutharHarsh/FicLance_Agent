import os

def find_all_jsx_components(repo_path: str):
    components = []
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".jsx"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, repo_path)
                components.append(rel)
    return components
