# agents/agent3/extractors/jsx_text_extractor.py
import os
import re
from pathlib import Path

TEXT_PATTERN = re.compile(r">([^<>{}][^<>{}]*)<")  # text between tags


def extract_jsx_visible_text(repo_path: str):
    repo_path = Path(repo_path)
    all_text = []
    for root, _, files in os.walk(repo_path):
        if any(
            skip in root for skip in ["node_modules", ".git", ".next", "dist", "build"]
        ):
            continue
        for f in files:
            if f.endswith((".jsx", ".tsx", ".js", ".tsx", ".html")):
                p = Path(root) / f
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                except:
                    continue
                matches = TEXT_PATTERN.findall(txt)
                matches = [m.strip() for m in matches if m.strip()]
                all_text.extend(matches)
    return {"jsx_visible_text": all_text}
