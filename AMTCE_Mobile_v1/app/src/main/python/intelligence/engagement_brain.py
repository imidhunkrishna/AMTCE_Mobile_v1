"""
EngagementBrain: Brand-Voice & Community Optimizer (Mobile)
---------------------------------------------------------
Automates human-like interactions and community engagement.
Uses Gemini to mimic the account owner's personality.
"""

import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("engagement_brain")

class EngagementBrain:
    def __init__(self):
        self.owner_name = os.getenv("IG_OWNER_NAME", "Creator")
        self.owner_bio = os.getenv("IG_OWNER_BIO", "High-energy content creator focused on value.")
        self.max_reply_len = 300

    def generate_community_reply(self, incoming_text: str, context: Dict = None) -> str:
        """
        Generates a natural, human-style reply to a comment or DM.
        This is a lightweight simulation of the Gemini-powered DM responder.
        """
        # In a real implementation, this would call Gemini with the persona prompt.
        # For the mobile bridge, we provide the logic to weave context.
        
        # Detect 'Buy' intent
        buy_keywords = ["link", "buy", "price", "where", "how much"]
        has_buy_intent = any(k in incoming_text.lower() for k in buy_keywords)
        
        affiliate_link = context.get("affiliate_link", "https://amazon.com/shop/placeholder") if context else None
        
        if has_buy_intent and affiliate_link:
            return f"Hey! I actually found it here: {affiliate_link} - it's a total game changer! 🙌"
        
        # Default Engagement
        return "Thanks for the support! Glad you enjoyed the content. Stay tuned for more! 🔥"

    def build_persona_prompt(self, niche: str) -> str:
        """Constructs the master persona prompt for Gemini."""
        return f"""
        You are {self.owner_name}, a {niche} creator.
        Persona: {self.owner_bio}
        Style: Casual, friendly, human. No robotic templates.
        Rule: If someone asks about a product, naturally mention the affiliate link.
        """
