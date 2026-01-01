import json
import re

def extract_and_parse_json(text: str):
    # 1. Extract JSON inside ```json ... ```
    code_block = re.search(r"```json(.*?)```", text, re.DOTALL)
    
    if code_block:
        cleaned = code_block.group(1).strip()
    else:
        # 2. Fallback: extract first {...} block
        fallback = re.search(r"\{.*\}", text, re.DOTALL)
        if fallback:
            cleaned = fallback.group(0).strip()
        else:
            return None  # No JSON found
    
    # 3. Parse JSON safely
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"error": "JSON parsing failed", "cleaned": cleaned, "exception": str(e)}
