"""
SceneEditor: Smart Timeline & Transition Coordinator
--------------------------------------------------
Manages edit pacing, transition assignment, and retention-hooks.
Includes 'Cold Start' acceleration for high-retention social content.
"""

import os
import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger("scene_editor")

class SceneEditor:
    def __init__(self):
        self.enable_cold_start = True
        self.transition_presets = ["whip_pan", "zoom_blur", "glitch_pop", "cross_dissolve"]

    def prepare_editing_plan(self, video_path: str, duration: float, moments: List[Dict]) -> Dict[str, Any]:
        """
        Creates a smart editing plan with transitions and zoom effects.
        """
        plan = {
            "input": video_path,
            "duration": duration,
            "cuts": [],
            "effects": [],
            "transitions": []
        }

        # 1. Generate Cuts from Moments
        for m in moments:
            if m["start"] > 0:
                plan["cuts"].append(round(m["start"], 2))

        # 2. Cold Start Acceleration (Force early edit at 1.5s for retention)
        if self.enable_cold_start and duration > 4.0:
            if not any(0 < c < 3.0 for c in plan["cuts"]):
                plan["cuts"].append(1.5)
                logger.info("📊 Cold Start Injected at 1.5s (Retention Hack)")

        plan["cuts"] = sorted(list(set(plan["cuts"])))

        # 3. Assign Transitions
        for cut in plan["cuts"]:
            plan["transitions"].append({
                "time": cut,
                "type": random.choice(self.transition_presets)
            })

        # 4. Smart Zoom Effects (Alternate segments)
        points = [0.0] + plan["cuts"] + [duration]
        for i in range(len(points) - 1):
            if i % 2 == 0: # Apply zoom to every other segment
                plan["effects"].append({
                    "start": points[i],
                    "end": points[i+1],
                    "type": random.choice(["slow_zoom_in", "punch_zoom"])
                })

        return plan

    def apply_single_shot_override(self, plan: Dict, hook_moment: Dict) -> Dict:
        """Overrides the plan for high-scoring single-shot highlights."""
        if hook_moment.get("energy_score", 0.0) > 0.85:
            logger.info("🔥 High-Energy Hook Detected! Switching to Highlight Mode.")
            t = hook_moment["start"]
            return {
                "input": plan["input"],
                "mode": "single_shot_highlight",
                "start": max(0.0, t),
                "end": min(plan["duration"], t + 5.0),
                "effects": [{"type": "punch_zoom", "start": t, "end": t+1}]
            }
        return plan
