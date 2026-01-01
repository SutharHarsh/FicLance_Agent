# agents/agent3/orchestrator.py
import json
import os
import re
from pathlib import Path
from core.llm_wrapper import GeminiLLM

from .extractors.jsx_text_extractor import extract_jsx_visible_text
from .extractors.api_extractor import extract_api_shapes
from .extractors.frontend_extractor import extract_frontend_usage
from .extractors.route_detector import detect_routes
from .extractors.detect_responsiveness import detect_responsiveness
from .prompts.tech_prompt import build_technical_prompt


def run_agent3_technical(repo_path: str, requirements: list):
    repo_path = str(repo_path)

    # ----------------------------------
    # REPO SUMMARY
    # ----------------------------------
    try:
        from services.repo_preprocessor import generate_repo_summary_lightweight

        repo_summary = generate_repo_summary_lightweight(repo_path)
    except:
        repo_summary = {"repo_name": Path(repo_path).name}

    # ----------------------------------
    # EXTRACTORS
    # ----------------------------------
    api_shapes = extract_api_shapes(repo_path)
    frontend_usage = extract_frontend_usage(repo_path)
    jsx_text = extract_jsx_visible_text(repo_path)

    # detect visible routes (even if we are not using screenshots)
    routes = detect_routes(repo_path) or []
    print("DETECTED ROUTES:", routes)

    # ----------------------------------
    # RESPONSIVENESS DETECTOR
    # ----------------------------------
    responsiveness = detect_responsiveness(repo_path)
    # responsiveness = {
    #   "is_responsive": bool,
    #   "css_evidence": [...],
    #   "layout_evidence": [...]
    # }

    # ----------------------------------
    # BUILD TECHNICAL PROMPT (UPDATED)
    # ----------------------------------
    prompt = build_technical_prompt(
        repo_summary=repo_summary,
        api_shapes=api_shapes,
        frontend_usage=frontend_usage,
        jsx_text=jsx_text,
        requirements=requirements,
        responsiveness=responsiveness,
    )

    gemini = GeminiLLM(api_key=os.getenv("GEMINI_API_KEY"))
    raw = gemini(prompt)

    # ----------------------------------
    # CLEAN GEMINI OUTPUT INTO JSON
    # ----------------------------------
    cleaned = re.sub(r"```json|```", "", raw).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)

    try:
        tech_json = json.loads(match.group(0)) if match else json.loads(cleaned)
    except:
        tech_json = {"error": "invalid_tech_json", "raw": raw}

    # ----------------------------------
    # REQUIREMENT STATS (ALWAYS ACCURATE)
    # ----------------------------------
    reqs = tech_json.get("requirements_report", [])

    completed = sum(1 for r in reqs if r.get("status") == "satisfied")
    pending = len(reqs) - completed
    percent = round((completed / len(reqs)) * 100, 1) if len(reqs) else 0.0

    missing_list = [
        r.get("requirement", "") for r in reqs if r.get("status") != "satisfied"
    ]

    # ----------------------------------
    # FINAL RETURN
    # ----------------------------------
    return {
        "repo_summary": repo_summary,
        "api_shapes": api_shapes,
        "frontend_usage": frontend_usage,
        "jsx_text": jsx_text,
        "responsiveness": responsiveness,
        "tech_json": tech_json,
        "requirements_completed": completed,
        "requirements_pending": pending,
        "completion_percentage": percent,
        "missing_requirements": missing_list,
    }
