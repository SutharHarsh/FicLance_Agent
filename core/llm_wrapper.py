# agents/agent3/llm_wrapper.py

import google.generativeai as genai


class GeminiLLM:
    """
    2 Brain Cell Explanation:
    - You create this once with API key
    - call(message) returns raw string from Gemini
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def __call__(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"LLM_ERROR: {e}"
