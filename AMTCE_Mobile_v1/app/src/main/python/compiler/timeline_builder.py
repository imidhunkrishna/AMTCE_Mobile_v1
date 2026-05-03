import logging
import random
from typing import List, Dict, Optional

logger = logging.getLogger("amtce.compiler.timeline")

# Human anticipation: cut 80ms BEFORE the beat lands
BEAT_ANTICIPATION = 0.080 

class TimelineBuilder:
    """
    Constructs a viral, beat-synced timeline for Android.
    """
    
    def build(self, ai_data: Dict, audio_intel: Dict = None) -> Dict:
        """
        Transforms Gemini/NZT intent into a concrete render timeline.
        Uses RhythmEngine for beat-synced sequencing if audio intelligence is provided.
        """
        logger.info("🥁 [TimelineBuilder] Constructing intelligent timeline...")
        
        raw_segments = ai_data.get("edited_segments", [])
        if not raw_segments:
            raw_segments = [{"start": 0.0, "end": 15.0, "source": "fallback"}]

        # 1. Rhythm-Based Sequencing
        from .rhythm_engine import rhythm_engine
        if audio_intel and audio_intel.get("beats"):
            final_segments = rhythm_engine.sequence_by_rhythm(raw_segments, audio_intel)
        else:
            # Fallback to basic beat snapping if we only have a simple beat grid
            final_segments = self._basic_snap(raw_segments, ai_data.get("beat_grid", []))

        # 2. Inject Effects (Zoom/Punch-in)
        # We automatically add punch-zooms on segments with high tension or energy
        zoom_effects = []
        for i, seg in enumerate(final_segments):
            tension = seg.get("tension_score", 0.5)
            if tension > 0.8:
                zoom_effects.append({
                    "type": "punch",
                    "start": seg["start"],
                    "end": min(seg["end"], seg["start"] + 1.5)
                })
            elif i % 3 == 0:
                zoom_effects.append({
                    "type": "slow",
                    "start": seg["start"],
                    "end": seg["end"]
                })

        return {
            "segments": final_segments,
            "zoom_effects": zoom_effects,
            "vibe": audio_intel.get("vibe", "neutral") if audio_intel else "neutral",
            "hashtags": ai_data.get("generated_hashtags", ["#Viral", "#Shorts"])
        }

    def _basic_snap(self, segments: List[Dict], beat_grid: List[float]) -> List[Dict]:
        if not beat_grid: return segments
        snapped = []
        for seg in segments:
            s, e = seg["start"], seg["end"]
            closest_s = min(beat_grid, key=lambda b: abs(b - s))
            if abs(closest_s - s) < 0.5: s = max(0.0, closest_s - 0.080)
            closest_e = min(beat_grid, key=lambda b: abs(b - e))
            if abs(closest_e - e) < 0.5: e = max(s + 1.0, closest_e - 0.080)
            seg["start"], seg["end"] = round(s, 3), round(e, 3)
            snapped.append(seg)
        return snapped

timeline_builder = TimelineBuilder()
