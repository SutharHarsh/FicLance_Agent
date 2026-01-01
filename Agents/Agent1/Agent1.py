from typing import List, Tuple
from pydantic import BaseModel
from crewai import LLM, Agent, Task
import random

class Requirements(BaseModel):
    client_name: str
    project_name: str
    description: str
    duration: str
    tech_stack: List[str]
    acceptance_criteria: List[str]

def Agent1(gemini_llm: LLM, Agent1Data) -> Tuple[Agent, Task]:

    Expertise = Agent1Data.Expertise
    TechStack = Agent1Data.TechStack
    Duration = Agent1Data.Duration
    ProjectName = Agent1Data.ProjectName
    Description = Agent1Data.Description

    # ---- Random Indian Names ----
    indian_names = [
        "Rohan Sharma", "Amit Patel", "Neha Gupta", "Rajesh Kumar", "Priya Mehta",
        "Sanjay Verma", "Kriti Desai", "Anil Nair", "Pooja Reddy", "Devansh Joshi",
        "Harshit Singh", "Rekha Yadav", "Nikhil Soni", "Manisha Shah"
    ]
    random_client_name = random.choice(indian_names)

    # ----------------------------
    # ULTRA-MINIFIED ROLE / GOAL / BACKSTORY
    # ----------------------------
    role_text = (
        "You are a practical, real client who writes clear, simple, non-technical, business-focused "
        "requirements. You care about clarity, user value, outcomes, and realistic scope."
    )

    goal_text = (
        f"Write precise, testable requirements for '{ProjectName}' using its description "
        f"({Description}), expertise ({Expertise}), timeline ({Duration}), and tech stack "
        f"({TechStack}). Each bullet must clearly state WHAT + WHY."
    )

    backstory_text = (
        f"You know exactly what '{ProjectName}' should achieve within {Duration}. You adjust depth "
        f"based on expertise ({Expertise}) and rely only on {TechStack}. Tone is warm, direct, "
        "and like a real client briefing a dev team."
    )

    # ----------------------------
    # ULTRA-MINIFIED TASK DESCRIPTION
    # ----------------------------
    task_description = (
        f"Create a numbered requirement list for '{ProjectName}'. Context: {Description}. "
        "Write like a real client focusing on clarity, UX, outcomes, and user/business value.\n\n"
        "Rules:\n"
        "- Number every bullet.\n"
        "- No technical terms (no React, Node, API words, etc.).\n"
        "- Requirements must be specific, testable, realistic.\n"
        "- Max 2 lines per bullet.\n"
        "- Match depth to expertise.\n"
        "- Use ONLY the given tech stack; flag limits.\n"
        "- Respect the timeline and flag unrealistic scope.\n"
        "- No templates or vague statements.\n"
        "- Each bullet must include WHAT + WHY.\n"
    )

    # ----------------------------
    # UPDATED EXPECTED OUTPUT WITH CLIENT NAME
    # ----------------------------
    expected_output = (
        f"Client_name: {random_client_name}\n"
        f"Project: {ProjectName}\n"
        f"Expertise: {Expertise}\n"
        f"Tech Stack: {TechStack}\n"
        f"Duration: {Duration}\n\n"
        "Overview: Briefly explain what '{ProjectName}' is, the problem it solves, and the value it adds.\n\n"
        "Requirements: Beginner: 6–8 | Intermediate: 8–10 | Advanced: 10–12.\n\n"
        "Each requirement must:\n"
        "- Be max 2 lines\n"
        "- Be specific to this project\n"
        "- Use simple business language\n"
        "- Fit expertise + duration\n"
        "- Use ONLY the provided tech stack\n"
        "- Explain WHAT + WHY\n"
        "- Be testable and measurable\n\n"
        "Tone: Warm, natural, clear, client-like, non-generic. No nested lists."
    )

    # ----------------------------
    # Create Agent
    # ----------------------------
    client_agent = Agent(
        role=role_text,
        goal=goal_text,
        backstory=backstory_text,
        verbose=False,
        cache=True,
        memory=False,
        llm=gemini_llm,
    )

    # ----------------------------
    # Create Task
    # ----------------------------
    client_task = Task(
        description=task_description,
        agent=client_agent,
        output_pydantic=Requirements,
        expected_output=expected_output,
    )

    return client_agent, client_task, random_client_name