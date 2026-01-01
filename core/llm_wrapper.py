# agents/agent3/llm_wrapper.py

import os
from crewai import LLM


class GeminiLLM:
    """
    CrewAI-based Gemini wrapper
    - Uses CrewAI's native google-genai provider
    - No direct Google SDK imports
    - Future-proof & production-safe
    """

    def __init__(self, model: str = "gemini/gemini-2.0-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment variables")

        self.llm = LLM(
            model=model,
            api_key=api_key,
        )

    def __call__(self, prompt: str) -> str:
        """
        Returns raw string output from Gemini via CrewAI
        """
        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            return f"LLM_ERROR: {e}"
