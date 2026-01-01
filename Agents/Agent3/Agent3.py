from typing import List
from pydantic import BaseModel
from crewai import LLM, Agent, Task


class ClientFeedback(BaseModel):
    feedback_summary: List[str]
    requirements_completed: int
    requirements_pending: int
    completion_percentage: float
    missing_requirements: List[str]


def Agent3(gemini_llm: LLM, context_string: str, technical_report: dict):

    repo_summary = technical_report.get("repo_summary", {})
    api_shapes = technical_report.get("api_shapes", {})
    frontend_usage = technical_report.get("frontend_usage", {})
    jsx_text = technical_report.get("jsx_text", "")
    ocr_text = technical_report.get("ocr_text", {})
    screenshots = technical_report.get("screenshots", [])
    tech_json = technical_report.get("tech_json", {})
    css_responsiveness = technical_report.get("css_responsiveness", {})
    layout_responsiveness = technical_report.get("layout_responsiveness", {})

    # -------- ROLE / GOAL / BACKSTORY (Ultra Short) --------
    # --- ULTRA-COMPRESSED ROLE / GOAL / BACKSTORY ---
    role_text = (
        "You are a simple non-technical client. You care only about whether the project feels complete, "
        "clear, useful, and real. Speak in warm, normal, everyday English."
    )

    goal_text = (
        "Judge the project ONLY from the repo summary. Say what is done, what is missing, "
        "and give exact % completion. If under 30%, say not acceptable. If 30%+, say it is moving well."
    )

    backstory_text = "You don't understand code. You judge like a normal person. If the work feels AI-made, say so."

    feedback_agent = Agent(
        role=role_text,
        goal=goal_text,
        backstory=backstory_text,
        verbose=False,
        llm=gemini_llm,
        cache=True,
        memory=False,
        tools=[],
    )

    # -------- DESCRIPTION --------
    description_text = (
        f"{context_string}\n\n"
        "Use ONLY this repo summary to understand the work:\n\n"
        f"Repo Summary: {repo_summary}\n\n"
        "Here are more technical details to help you understand the project better:\n\n"
        f"API Shapes: {api_shapes}\n\n"
        f"Frontend Usage: {frontend_usage}\n\n"
        f"JSX Text: {jsx_text}\n\n"
        f"OCR Text: {ocr_text}\n\n"
        f"Screenshots: {screenshots}\n\n"
        f"Tech JSON: {tech_json}\n\n"
        f"CSS Responsiveness: {css_responsiveness}\n\n"
        f"Layout Responsiveness: {layout_responsiveness}"
    )

    # -------- EXPECTED OUTPUT --------
    expected_output_text = (
        "Before writing JSON:\n"
        "1. Read all requirements in order.\n"
        "2. Match each requirement ONLY with clear info in the repo summary.\n"
        "3. If the summary supports it → COMPLETED. If not → MISSING.\n"
        "4. Count done/missing. % = done/total*100.\n"
        "5. Missing list must use: 'number. requirement text'.\n\n"
        "Final JSON rules:\n"
        "- feedback_summary = 5–7 short bullets (10–15 words).\n"
        "- Use ONLY requirement words like hero section, pictures, travel places, testimonials, booking button, trust area, responsive design.\n"
        "- Never use coding words, files, components, jsx, or technical phrases.\n"
        "- Do NOT use uncertainty words (no maybe, seems, unclear, might, hard to tell).\n"
        "- Give clear yes/no based only on repo summary.\n"
        "- If requirement is done, describe it warmly and simply.\n"
        "- If missing, say it plainly but kindly.\n"
        "- If work feels AI-made, say so in simple human English.\n"
        "- Tone must be warm, friendly, human, and easy to understand.\n"
        "- Help the developer by explaining briefly WHY done things feel helpful and WHY missing things matter.\n"
        "- Only output JSON with: feedback_summary, requirements_completed, requirements_pending, completion_percentage, missing_requirements.\n"
    )

    # -------- TASK --------
    feedback_task = Task(
        description=description_text,
        agent=feedback_agent,
        output_pydantic=ClientFeedback,
        expected_output=expected_output_text,
    )

    return feedback_agent, feedback_task
