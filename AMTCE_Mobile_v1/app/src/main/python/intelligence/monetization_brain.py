# engine/intelligence/monetization_brain.py
import os
import json
import logging
import re
from typing import Dict, List, Optional
from intelligence.fashion_scout import FashionScout
from intelligence.money_flow import money_flow_engine
from utils.file_ops import file_lock, atomic_write


logger = logging.getLogger("amtce.brain")

class MonetizationBrain:
    """
    The 'Viral Brain' of AMTCE. 
    Extracted from Intelligence_Modules/monetization_brain.py.
    """

    def __init__(self, gemini_client=None):
        self.prompts_path = os.path.join(os.path.dirname(__file__), "niche_strategies.json")
        self.affiliate_path = os.path.join(os.path.dirname(__file__), "Amazon_affliate_link.json")
        self.strategies = self._load_strategies()
        self.scout = FashionScout(gemini_client) if gemini_client else None


    def _load_strategies(self):
        try:
            if os.path.exists(self.prompts_path):
                with open(self.prompts_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load niche strategies: {e}")
        return {}

    def get_affiliate_link(self, category: str) -> str:
        """Retrieves a persistent affiliate link for a given category."""
        try:
            if os.path.exists(self.affiliate_path):
                with open(self.affiliate_path, "r", encoding="utf-8") as f:
                    links = json.load(f)
                    # Find best match
                    for k, v in links.items():
                        if k.lower() in category.lower() or category.lower() in k.lower():
                            return v[0] if isinstance(v, list) else v
                    return links.get("default", "https://amazon.com")
        except Exception as e:
            logger.warning(f"Affiliate lookup failed: {e}")
        return "https://amazon.com"


    def get_master_prompt(self, niche="fashion", title="Video", duration=15.0):
        """Constructs the high-conversion prompt used by the original engine."""
        niche_config = self.strategies.get(niche, self.strategies.get("generic", {}))
        
        # Determine niche configuration
        _niche_label = niche.upper()
        _duration_label = "SHORT (<=60s)" if duration <= 60 else f"LONG ({int(duration)}s)"
        word_target = max(20, min(int((duration / 60) * 140), 55))
        _word_target_str = str(word_target)

        # The 'Secret Sauce' — The Master Hook Block (Ported from Desktop)
        hashtag_prompt = (
            # ── HASHTAGS ──────────────────────────────────────────────────────
            f'"generated_hashtags": "<NICHE={_niche_label}. '
            f'Generate 10-15 hashtags. RULES: '
            f'(1) First 3 MUST be #Shorts #Viral #Trending. '
            f'(2) Next 4-6 MUST be niche-specific. '
            f'(3) Remaining 3-5 MUST be long-tail curiosity tags.>",\n'

            # ── TITLE ─────────────────────────────────────────────────────────
            f'  "generated_title": "<SEO-OPTIMISED CLICKBAIT TITLE. RULES: '
            f'(1) MUST start with {title} verbatim. '
            f'(2) Append a curiosity gap suffix. '
            f'(3) Max 60 chars total.>",\n'

            # ── TELEGRAM HOOK ────────────────────────────────────────────────
            f'  "telegram_hook": "<TELEGRAM BROADCAST COPY. Desire + FOMO. '
            f'RULES: (1) Max 20 words. (2) Name specific item. (3) Scarcity framing.>",\n'

            # ── INSTAGRAM HOOK ────────────────────────────────────────────────
            f'  "instagram_hook": "<INSTAGRAM REEL CAPTION HOOK. '
            f'RULES: (1) 1-2 lines. (2) Open with emotional desire. (3) Curiosity gap. (4) End with Link in bio.>",\n'

            # ── YOUTUBE HOOK ──────────────────────────────────────────────────
            f'  "youtube_hook": "<YOUTUBE SHORTS ON-SCREEN HOOK TEXT. '
            f'RULES: (1) Max 15 words. (2) Standalone sentence. (3) No emojis.>",\n'

            # ── NARRATION SCRIPT ──────────────────────────────────────────────
            f'  "narration_script": "<VOICEOVER SCRIPT. '
            f'RULES: (1) Target: {_word_target_str} words. (2) FLOW: Hook -> Detail -> Reward. (3) No motivation filler.>"'
        )

        reviewer_prompt = niche_config.get("monetization_brain", {}).get("reviewer_prompt", "")
        if not reviewer_prompt:
            reviewer_prompt = "YOU ARE A PROFESSIONAL REVIEWER AI. Identify garments and products."

        final_prompt = (
            f"{reviewer_prompt}\n\n"
            f"STRATEGY: {niche_config.get('hook_strategy', {}).get('narration_purpose', 'High-conversion psychology.')}\n\n"
            f"INPUT:\nVideo Title: {title}\nDuration: {duration}s\n"
            f"OUTPUT FORMAT (JSON ONLY):\n{{\n  {hashtag_prompt}\n}}"
        )
        return final_prompt


    def parse_gemini_response(self, response_text: str) -> Dict:
        """Robust JSON parsing for Gemini outputs."""
        try:
            match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception as e:
            logger.error(f"Failed to parse Brain response: {e}")
        
        return {
            "generated_title": "Viral Edit — You missed this detail!",
            "generated_hashtags": ["#Shorts", "#Viral", "#Trending"],
            "telegram_hook": "Look at this find! Link below.",
            "narration_script": "This is a must-see moment."
        }
