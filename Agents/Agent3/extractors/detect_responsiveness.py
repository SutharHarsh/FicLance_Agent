# agents/agent3/extractors/detect_responsiveness.py
from pathlib import Path
import re
from typing import Dict, Any

RESPONSIVE_PATTERNS = {
    "media_queries": re.compile(r"@media\s*\((max|min)-width|@media\s+only|@media\s+screen", re.I),
    "tailwind_prefixes": re.compile(r"\b(sm:|md:|lg:|xl:|2xl:)\b"),
    "tailwind_grid_cols": re.compile(r"\b(grid-cols-(1|2|3|4|5|6))\b"),
    "flex_responsive": re.compile(r"\b(flex-col\b|flex-row\b|md:flex|sm:flex)\b"),
    "viewport_meta": re.compile(r'<meta\s+name=["\']viewport["\']', re.I),
    "percent_width": re.compile(r"(width:\s*100%|w-full\b|max-w-[\d]+|width:\s*calc\()"),
    "srcset_attr": re.compile(r"\bsrcset\b", re.I),
    "picture_tag": re.compile(r"<picture\b", re.I),
    "rem_em_units": re.compile(r"\b(rem|em)\b"),
    "grid_auto_fit": re.compile(r"(auto-fit|auto-fill|minmax\()", re.I),
}

TEXT_RESPONSIVE_KEYWORDS = [
    "mobile", "tablet", "responsive", "all devices", "small screens", "phone", "viewport"
]


def detect_responsiveness(repo_path: str) -> Dict[str, Any]:
    """
    Heuristic multi-signal responsiveness detector.
    Returns:
      {
        "score": 0.0-1.0,
        "is_responsive": True/False (score >= threshold),
        "evidence": [ { "type": "<signal>", "file": "<path>", "snippet": "<short>" }, ... ],
        "counts": { "<signal>": n, ... }
      }
    """
    p = Path(repo_path)
    files = list(p.rglob("*.*"))
    counts = {k: 0 for k in RESPONSIVE_PATTERNS.keys()}
    evidence = []

    # Scan relevant files: css, scss, html, jsx, tsx, js
    text_file_exts = {".css", ".scss", ".html", ".htm", ".jsx", ".tsx", ".js", ".ts"}
    aggregated_text_keywords = []

    for f in files:
        try:
            if f.suffix.lower() not in text_file_exts:
                continue
            raw = f.read_text(errors="ignore")
        except Exception:
            continue

        # quick check for viewport meta in HTML
        if RESPONSIVE_PATTERNS["viewport_meta"].search(raw):
            counts["viewport_meta"] = counts.get("viewport_meta", 0) + 1
            evidence.append({"type": "viewport_meta", "file": str(f), "snippet": "<meta viewport present>"})

        # test patterns
        for key, pattern in RESPONSIVE_PATTERNS.items():
            # skip viewport (handled)
            if key == "viewport_meta":
                continue
            m = pattern.search(raw)
            if m:
                counts[key] = counts.get(key, 0) + 1
                snippet = m.group(0)[:140].strip().replace("\n", " ")
                evidence.append({"type": key, "file": str(f), "snippet": snippet})

        # keyword search in visible JSX/HTML text
        lower = raw.lower()
        for kw in TEXT_RESPONSIVE_KEYWORDS:
            if kw in lower:
                aggregated_text_keywords.append({"file": str(f), "keyword": kw})

    # Build a simple weighted scoring model
    # weights tuned for balance: media queries and tailwind prefixes are strongest signals
    weights = {
        "media_queries": 0.30,
        "tailwind_prefixes": 0.25,
        "viewport_meta": 0.20,
        "flex_responsive": 0.10,
        "grid_auto_fit": 0.05,
        "percent_width": 0.04,
        "srcset_attr": 0.03,
        "picture_tag": 0.02,
        # other weak signals implicitly counted through counts
    }

    score = 0.0
    total_possible = sum(weights.values())

    # Add weighted evidence
    for k, w in weights.items():
        c = counts.get(k, 0)
        if c > 0:
            # increase proportionally but cap
            score += w * min(1.0, c / 3.0)  # more matches increases confidence up to 3 hits

    # small boost if any textual mention of mobile/responsive appears
    if aggregated_text_keywords:
        score += 0.04 * min(3, len(aggregated_text_keywords))

    # Normalize to 0..1
    score = max(0.0, min(1.0, score / total_possible))

    # Build final evidence shortened
    short_evidence = []
    for e in evidence[:12]:  # limit length
        short_evidence.append({"type": e["type"], "snippet": e["snippet"]})

    # final boolean using threshold (default 0.45) - you can tune this
    threshold = 0.45
    is_responsive = score >= threshold

    return {
        "score": round(score, 3),
        "is_responsive": bool(is_responsive),
        "evidence": short_evidence,
        "counts": counts,
        "keyword_hits": aggregated_text_keywords,
        "threshold_used": threshold,
    }
