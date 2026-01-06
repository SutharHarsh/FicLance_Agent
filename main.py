from unittest import result
from fastapi import FastAPI
from crewai import LLM, Crew, Process
import os
from pydantic import BaseModel
from redis import Redis
import json

from Agents.Agent3.orchestrator import run_agent3_technical
from Agents.Agent3.extractors.api_extractor import extract_api_shapes
from Agents.Agent3.extractors.frontend_extractor import extract_frontend_usage
from Agents.Agent3.extractors.route_detector import detect_routes
from Agents.Agent1.Agent1 import Agent1
from Agents.Agent2.Agent2 import Agent2
from Agents.Agent3.Agent3 import Agent3
from services.parse_json import extract_and_parse_json
from services.redis_client import redis_cache
from services.clone_repo import clone_repo
from services.repo_preprocessor import generate_repo_summary_lightweight
from services.context_compressor import compress_agent1_context

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os

load_dotenv(override=True)

print("GEMINI_API_KEY loaded:", bool(os.getenv("GEMINI_API_KEY")))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_redis():
    url = os.getenv("UPSTASH_REDIS_URL")
    if not url:
        print("WARNING: UPSTASH_REDIS_URL is missing. TCP Redis client will be disabled.")
        return None
    try:
        if not (url.startswith("redis://") or url.startswith("rediss://")):
             print(f"ERROR: UPSTASH_REDIS_URL must start with 'redis://' or 'rediss://'. Got: {url[:10]}...")
             return None
        return Redis.from_url(url, socket_timeout=5, decode_responses=True)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Redis TCP client: {str(e)}")
        return None

redis_client = init_redis()

import json
import re


def force_json(text: str):
    if not text or text.strip() == "":
        return None

    cleaned = re.sub(r"```json|```", "", text).strip()

    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")

    # Try normal JSON
    try:
        return json.loads(cleaned)
    except:
        pass

    # Try extracting first { ... }
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    return None


# -------------------------------
# LLM
# -------------------------------
gemini_llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# -------------------------------
# Repo Settings
# -------------------------------
PROJECT_PATH = "./project"


# -------------------------------
# Request Models
# -------------------------------
class Agent1Data(BaseModel):
    SimulationId: str
    Expertise: str
    TechStack: list[str]
    Duration: str
    ProjectName: str
    Description: str

class Agent1Output(BaseModel):
    client_name: str


class Agent2Data(BaseModel):
    SimulationId: str
    Question: str
    Context: Optional[dict] = None


class Agent3Data(BaseModel):
    RepoURL: str
    SimulationId: str
    Context: Optional[dict] = None


# -------------------------------
# AGENT 1 API
# -------------------------------
@app.post("/requirements")
async def run_agent1(item: Agent1Data):

    client_agent, client_task, random_client_name = Agent1(gemini_llm, item)

    crew = Crew(
        agents=[client_agent],
        tasks=[client_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    parsed = extract_and_parse_json(result.raw)

    # Extract requirements from the pydantic output
    requirements_text = parsed["acceptance_criteria"]

    # Persist the selected client name within the compressed context

    # Metadata to store
    metadata = {
        "client_name": random_client_name,
        "project_name": item.ProjectName,
        "duration": item.Duration,
        "expertise": item.Expertise,
        "tech_stack": item.TechStack,
    }

    # Compress
    compressed_memory = compress_agent1_context(requirements_text, metadata)

    # Store context per simulation to avoid cross-chat leakage
    redis_cache.set(f"agent1_context:{item.SimulationId}", compressed_memory)

    return {"message": parsed}


# -------------------------------
# AGENT 2 API
# -------------------------------
@app.post("/messages")
async def run_agent2(item: Agent2Data):

    # Try to get context from payload first, then Redis
    context_data = item.Context
    if not context_data:
        redis_data = redis_cache.get(f"agent1_context:{item.SimulationId}")
        if not redis_data:
            return {"error": "No context provided and /requirements not found in cache."}
        context_data = json.loads(redis_data)

    # Convert the full object into a compact JSON string
    agent1_context = json.dumps(context_data, indent=2)

    user_question = item.Question

    question_agent, question_task = Agent2(
        gemini_llm,
        context_string=agent1_context,
        question=user_question,
        client_name=context.get("client_name", "Client"),
    )

    crew = Crew(
        agents=[question_agent],
        tasks=[question_task],
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = crew.kickoff()
        raw = getattr(result, "raw", None)
        if not raw:
            # Crew sometimes fails to aggregate when tool/LLM returns empty
            return {
                "message": "I'm having trouble responding right now. Please try again in a moment.",
                "error": "No task outputs from CrewAI",
            }
        return {"message": raw}
    except Exception as e:
        # Provide a friendly, non-crashing fallback so UI doesn't break
        return {
            "message": "I'm having trouble responding right now. Please try again in a moment.",
            "error": str(e),
        }


# -------------------------------
# AGENT 3 API (SUPER AGENT3)
# -------------------------------
@app.post("/feedback")
async def run_agent3(item: Agent3Data):
    print("Received Repo URL:", item.RepoURL)
    project_cloned = clone_repo(item.RepoURL)
    if not project_cloned:
        return {"error": "Failed to clone repository"}
    repo_path = PROJECT_PATH

    # Load requirements (try payload first, then Redis)
    context_data = item.Context
    if not context_data:
        redis_data = redis_cache.get(f"agent1_context:{item.SimulationId}")
        if not redis_data:
             return {"error": "No context provided and /requirements not found in cache."}
        context_data = json.loads(redis_data)
    
    requirements = context_data.get("key_requirements", [])
    if not requirements:
        raw = context_data.get("raw_acceptance_criteria", "")
        # Derive simple lines from raw acceptance criteria if available
        derived = [line.strip("-* ").strip() for line in raw.splitlines() if line.strip()]
        requirements = derived

    agent1_context = json.dumps(context_data, indent=2)

    # Run technical pipeline
    technical = run_agent3_technical(repo_path, requirements)

    # Build CrewAI emotional agent
    agent3, task3 = Agent3(
        gemini_llm=gemini_llm, technical_report=technical, context_string=agent1_context
    )

    crew = Crew(
        agents=[agent3],
        tasks=[task3],
        process=Process.sequential,
        verbose=False,
    )

    try:
        result = crew.kickoff()
        raw = getattr(result, "raw", None)
    except Exception as e:
        return {"error": f"Feedback generation failed: {str(e)}"}

    # Extract emotional part
    emotional = force_json(raw) or {}
    feedback_summary = emotional.get("feedback_summary", [])

    # Merge

    parsed = extract_and_parse_json(raw)

    return {"message": parsed}