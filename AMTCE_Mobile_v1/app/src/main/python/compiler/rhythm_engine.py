import logging
from typing import List, Dict, Any

logger = logging.getLogger("rhythm_engine")

class RhythmEngine:
    """
    The Director of the Timeline.
    Aligns visual pacing with musical tension and beats.
    """
    def __init__(self):
        self.anticipation = 0.080 # 80ms before the beat
        
    def sequence_by_rhythm(self, raw_segments: List[Dict], audio_intel: Dict) -> List[Dict]:
        """
        Reorders and resizes segments based on audio tension and beats.
        """
        beats = audio_intel.get("beats", [])
        drops = audio_intel.get("drops", [])
        vibe = audio_intel.get("vibe", "neutral")
        tension_arc = audio_intel.get("tension_arc", [])
        
        if not beats:
            logger.warning("⚠️ No beats found, using linear sequencing.")
            return raw_segments

        beat_times = [b["time"] for b in beats]
        final_segments = []
        
        # Mapping tension to pacing
        # High Tension (>0.8) -> 1 beat duration
        # Med Tension (0.5-0.8) -> 2 beats
        # Low Tension (<0.5) -> 4 beats
        
        current_beat_idx = 0
        seg_idx = 0
        
        while current_beat_idx < len(beat_times) - 1 and seg_idx < len(raw_segments):
            start_beat = beat_times[current_beat_idx]
            
            # Determine how many beats this segment should hold
            tension = self._get_tension_at(tension_arc, start_beat)
            
            if tension > 0.8 or vibe == "explosive":
                beat_step = 1
            elif tension > 0.5 or vibe == "hype":
                beat_step = 2
            else:
                beat_step = 4
                
            # Clamp step to remaining beats
            beat_step = min(beat_step, len(beat_times) - 1 - current_beat_idx)
            end_beat = beat_times[current_beat_idx + beat_step]
            
            # Apply Anticipation
            s = max(0.0, start_beat - self.anticipation)
            e = max(s + 0.2, end_beat - self.anticipation)
            
            # Check for Drops: If a drop occurs within this window, force the clip to end exactly at the drop
            for d in drops:
                if start_beat < d <= end_beat:
                    e = max(s + 0.2, d - self.anticipation)
                    # We also increment beat_idx to match the drop
                    break
            
            seg = raw_segments[seg_idx].copy()
            seg["start"] = round(s, 3)
            seg["end"] = round(e, 3)
            seg["tension_score"] = tension
            
            final_segments.append(seg)
            
            # Advance
            current_beat_idx += beat_step
            seg_idx = (seg_idx + 1) % len(raw_segments) # Loop segments if needed
            
            # Safety exit for long tracks
            if len(final_segments) > 30: break

        logger.info(f"🥁 [RhythmEngine] Sequenced {len(final_segments)} clips to {vibe} rhythm.")
        return final_segments

    def _get_tension_at(self, arc: List[Dict], time_sec: float) -> float:
        if not arc: return 0.5
        for i in range(len(arc)-1):
            if arc[i]["time"] <= time_sec <= arc[i+1]["time"]:
                return arc[i]["tension"]
        return arc[-1]["tension"] if arc else 0.5

rhythm_engine = RhythmEngine()
