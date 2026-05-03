import logging
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger("pacing_architect")

class PacingArchitect:
    """
    Android Pacing Engine.
    Post-processes the video timeline to enforce a human-like energy curve.
    
    Energy Curve Strategy:
    - 0-20%  (Setup): Establish the scene, slower cuts (2.0s - 3.5s)
    - 20-60% (Build): Rising tension, medium cuts (1.5s - 2.5s)
    - 60-85% (Escalation): High momentum, fast cuts (0.8s - 1.5s)
    - 85-100% (Climax): High impact, variable cuts (1.0s - 3.0s)
    """

    PRESETS = {
        "viral_fast": {
            "setup": (1.5, 2.5),
            "build": (1.0, 1.8),
            "escalation": (0.5, 1.2),
            "climax": (1.0, 2.0),
        },
        "cinematic": {
            "setup": (3.0, 5.0),
            "build": (2.0, 3.5),
            "escalation": (1.5, 2.5),
            "climax": (2.0, 4.0),
        }
    }

    def shape(self, timeline: List[Dict], style: str = "viral_fast") -> List[Dict]:
        """
        Adjusts segment durations based on their position in the video.
        """
        if not timeline:
            return timeline

        preset = self.PRESETS.get(style, self.PRESETS["viral_fast"])
        total_duration = sum(s["end"] - s["start"] for s in timeline)
        
        if total_duration <= 0:
            return timeline

        shaped = []
        elapsed = 0.0
        
        for seg in timeline:
            seg = dict(seg) # Copy
            dur = seg["end"] - seg["start"]
            
            # 1. Determine position band [0.0 - 1.0]
            pos = elapsed / total_duration
            band = self._get_band(pos)
            min_d, max_d = preset[band]
            
            # 2. Target duration (Trim if too long)
            # We never extend segments beyond original duration to avoid quality loss
            target_dur = random.uniform(min_d, max_d)
            actual_dur = min(dur, target_dur)
            
            # 3. Ensure minimum cut length for visibility
            if actual_dur < 0.5:
                actual_dur = 0.5
                
            seg["end"] = seg["start"] + actual_dur
            seg["pacing_band"] = band
            
            shaped.append(seg)
            elapsed += actual_dur
            
        logger.info(f"⚡ [PacingArchitect] Shaped {len(shaped)} segments using '{style}' curve.")
        return shaped

    def _get_band(self, pos: float) -> str:
        if pos < 0.20: return "setup"
        if pos < 0.60: return "build"
        if pos < 0.85: return "escalation"
        return "climax"

pacing_architect = PacingArchitect()
