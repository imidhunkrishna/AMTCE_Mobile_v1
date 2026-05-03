"""
TrendBrain: Viral Narrative & Opportunity Optimizer (Mobile)
-----------------------------------------------------------
Aggregates trend signals and innovates narrative angles.
Zero-Token Strategy: Passes trend context to main Gemini flow.
"""

import os
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger("trend_brain")

# --- Constants ---
USER_TREND_FILE = os.path.join("trend_context", "user_trend_input.json")
TREND_MAX_AGE_DAYS = 40

class TrendBrain:
    def __init__(self):
        self.angle_strategies = ["humor", "satire", "explanation", "reaction", "comparison", "story", "unexpected_twist"]
        self.hook_templates = {
            "humor": "Nobody expected this — and that's exactly the problem.",
            "satire": "Imagine being this wrong on the internet.",
            "explanation": "This trend has a reason — here it is.",
            "reaction": "My reaction watching this unfold in real time.",
            "comparison": "Before vs After. Which version wins?",
            "story": "The story behind this moment is wilder than you think.",
            "unexpected_twist": "Nobody saw this coming. Neither did we."
        }

    def aggregate_trends(self, visual_entities: List[str] = None) -> Dict[str, Any]:
        """Gathers trend signals from user hints and visual forensics."""
        user_trends = self._load_user_trends()
        topics = [e.get("input", "") for e in user_trends if e.get("input")]
        
        # Keyword extraction (Simplified for mobile)
        keywords = []
        for t in topics:
            words = re.findall(r"[a-zA-Z]+", t.lower())
            keywords.extend([w for w in words if len(w) > 3])
            
        strength = min(1.0, len(topics) * 0.3 + (0.1 if visual_entities else 0.0))
        
        return {
            "topics": list(set(topics))[:10],
            "keywords": list(set(keywords))[:15],
            "visual_context": visual_entities or [],
            "trend_strength": round(strength, 2)
        }

    def analyze_opportunity(self, trend_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates opportunity score and innovates the narrative angle."""
        topics = trend_context.get("topics", [])
        keywords = trend_context.get("keywords", [])
        strength = trend_context.get("trend_strength", 0.0)
        
        if not topics and not keywords:
            return {"opportunity_score": 0.0, "recommended_angle": "story", "hook": "A moment of discovery."}

        # Heuristic Scoring
        growth = min(1.0, len(topics) / 5.0)
        volume = min(1.0, len(keywords) / 10.0)
        competition = min(1.0, strength * 0.8)
        
        score = round(max(0.0, min(1.0, 0.4 * growth + 0.3 * volume - 0.3 * competition)), 2)
        
        # Angle Innovation (High competition -> Humor/Twist)
        if competition > 0.6:
            angle = random.choice(["humor", "unexpected_twist", "satire"])
        else:
            angle = random.choice(["story", "explanation", "reaction"])
            
        return {
            "opportunity_score": score,
            "recommended_angle": angle,
            "hook": self.hook_templates.get(angle, "This changes everything."),
            "trend_stage": "viral" if score > 0.5 else "emerging",
            "competition_level": "high" if competition > 0.6 else "low"
        }

    def _load_user_trends(self) -> List[Dict]:
        """Loads and cleans user trend input."""
        try:
            if not os.path.exists(USER_TREND_FILE): return []
            with open(USER_TREND_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            cutoff = datetime.now(timezone.utc) - timedelta(days=TREND_MAX_AGE_DAYS)
            valid = []
            for entry in data:
                ts = datetime.fromisoformat(entry.get("timestamp", ""))
                if ts >= cutoff: valid.append(entry)
            return valid
        except:
            return []

import random # Required for angle selection
