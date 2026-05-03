# engine/refiner/metadata_generator.py
import os
import json
import logging
from typing import Dict, List

logger = logging.getLogger("amtce.metadata")

class ViralMetadataGenerator:
    """
    Ported from AMTCE Monetization Brain.
    Generates high-conversion titles, hashtags, and YPP-compliant descriptions.
    """
    
    @staticmethod
    def get_system_prompt(niche="fashion"):
        return f"""
        YOU ARE A HIGH-CONVERSION VIRAL MARKETING EXPERT. 
        Your goal is to generate SEO-optimized metadata for a {niche} video.
        
        STRICT OUTPUT FORMAT (JSON ONLY):
        {{
          "generated_title": "<Clickbait Title starting with input title>",
          "hashtags": ["tag1", "tag2", "..."],
          "description": "<Psychological editorial script - 2 sentences>",
          "viral_score": 0-100
        }}
        
        TITLE RULES:
        1. MUST start with the original title.
        2. Append a curiosity gap suffix (e.g. " — you missed this", " | Hidden Detail").
        3. Max 60 chars.
        
        HASHTAG RULES:
        1. 3 high-volume tags (#Shorts #Viral #Trending).
        2. 5 niche-specific tags.
        3. 2 curiosity tags.
        """

    def generate(self, video_title: str, visual_context: str = "A beautiful clip.") -> Dict:
        """
        In the real app, this calls Gemini. 
        For the extraction phase, we use the strategic logic to build the request.
        """
        # This mirrors the logic in monetization_brain.py
        logger.info(f"Generating Viral Metadata for: {video_title}")
        
        # We will connect this to the Gemini Router in the next step
        fallback_data = {
            "generated_title": f"{video_title} — The secret detail you missed ✨",
            "hashtags": ["#Shorts", "#Viral", "#Trending", "#FashionEdit", "#AMTCE", "#ViralStyle"],
            "description": f"Analyzing the stunning presence of {video_title}. This moment captures the perfect balance of style and timing.",
            "viral_score": 95
        }
        
        return fallback_data
