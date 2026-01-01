# agents/agent3/prompts/tech_prompt.py
import json


def build_technical_prompt(
    repo_summary,
    api_shapes,
    frontend_usage,
    jsx_text,
    requirements,
    responsiveness,  # new single object
):
    return f"""
You are a senior full-stack technical evaluator.
Use ONLY the data below.

EXPECTED JSON:
{{
  "requirements_report":[
    {{
      "requirement":"original requirement text",
      "status":"satisfied | partial | missing",
      "evidence":"very short explanation (source)"
    }}
  ]
}}

SPECIAL RULE for responsiveness:
RESPONSIVENESS_OBJECT = {json.dumps(responsiveness, indent=2)}

If requirement mentions "responsive" or similar, use these rules:
- If responsiveness['score'] >= responsiveness.get('threshold_used', 0.45) AND responsiveness['is_responsive'] == true => mark "satisfied".  
- If responsiveness['score'] is close (>= 0.30 but < threshold) => mark "partial" and mention short evidence.  
- If below 0.30 => mark "missing".

Requirements:
{json.dumps(requirements, indent=2)}

REPO_SUMMARY:
{json.dumps(repo_summary, indent=2)}

API_SHAPES:
{json.dumps(api_shapes, indent=2)}

FRONTEND_USAGE:
{json.dumps(frontend_usage, indent=2)}

JSX_TEXT:
{json.dumps(jsx_text, indent=2)}

Now output ONLY the strict JSON.
"""
