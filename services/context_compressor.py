import re
import json

def compress_agent1_context(agent1_output, metadata: dict):
    """
    Takes full Agent1 output (list or string)
    and compresses it into a tiny memory object.
    """

    # If output is a list → convert to a single string
    if isinstance(agent1_output, list):
        agent1_output = "\n".join(agent1_output)

    # If still not a string → convert to string safely
    if not isinstance(agent1_output, str):
        agent1_output = str(agent1_output)

    # Extract bullet titles
    bullets = re.findall(r"^\d+\.\s*(.+)", agent1_output, flags=re.MULTILINE)

    # Clean + limit to max 10
    clean_bullets = [b.strip() for b in bullets[:10]]

    compressed = {
        "project_name": metadata.get("project_name", ""),
        "duration": metadata.get("duration", ""),
        "expertise": metadata.get("expertise", ""),
        "tech_stack": metadata.get("tech_stack", []),
        "client_name": metadata.get("client_name", "Client"),
        "key_requirements": clean_bullets,
        "raw_acceptance_criteria": agent1_output,
    }

    return json.dumps(compressed)
