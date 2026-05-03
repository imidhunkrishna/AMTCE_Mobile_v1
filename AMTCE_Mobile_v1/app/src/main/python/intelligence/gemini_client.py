# engine/intelligence/gemini_client.py
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env for both local and cloud-injected builds
load_dotenv()

logger = logging.getLogger("amtce.gemini")

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_json(self, prompt: str):
        """Calls Gemini and returns the raw text."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None
