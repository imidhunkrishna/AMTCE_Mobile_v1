import os
import json
import logging
import statistics
import gc
from typing import List, Dict, Any, Optional, Tuple
from utils.import_gate import safe_import

# Gated Imports for Android Stability
cv2 = safe_import("cv2")
np = safe_import("numpy")

logger = logging.getLogger("content_brain")

class ContentBrain:
    """
    Advanced Viral Intelligence Engine for Android.
    Consolidates Emotional Spike Detection, Retention Prediction, and Hook Optimization.
    """

    def __init__(self):
        # 1. Retention Weights R(t) = 0.35*M + 0.25*F + 0.20*B + 0.20*D
        self.WEIGHT_MOTION = 0.35
        self.WEIGHT_FACE = 0.25
        self.WEIGHT_BEAT = 0.20
        self.WEIGHT_DIALOGUE = 0.20
        
        # 2. Emotional Spike Weights E(t) = 0.4*F + 0.3*M + 0.3*A
        self.WEIGHT_EMO_FACE = 0.4
        self.WEIGHT_EMO_MOTION = 0.3
        self.WEIGHT_EMO_AUDIO = 0.3

        # 3. Final Signal Fusion S(t) = 0.4*E + 0.3*F + 0.15*M + 0.1*R + 0.05*B
        self.FUSION_EMOTION = 0.40
        self.FUSION_FACE = 0.30
        self.FUSION_MOTION = 0.15
        self.FUSION_RETENTION = 0.10
        self.FUSION_BEAT = 0.05

    def process(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point to build the Content Intelligence profile.
        """
        logger.info("🧠 [ContentBrain] Initiating Deep Content Intelligence...")
        
        # 1. Emotional Spike Detection (Finding the Climax)
        spikes = self._detect_spikes(profile_data)
        profile_data["emotional_spikes"] = spikes
        
        # 2. Retention Curve (Finding the Sticky Parts)
        retention = self._build_retention_curve(profile_data)
        profile_data["retention_data"] = retention
        
        # 3. Professional Signal Fusion (Human Editor Logic)
        fused = self._fuse_signals(profile_data, spikes, retention)
        profile_data["fused_moments"] = fused
        
        # 4. Master Hook Selection (Finding the first 3s winner)
        hook = self._find_hook(profile_data)
        profile_data["master_hook"] = hook
        
        logger.info(f"✅ [ContentBrain] Deep Analysis Complete: FusedMoments={len(fused)} | HookTime={hook.get('time', 0):.2f}")
        return profile_data

    def _fuse_signals(self, data: Dict[str, Any], spikes: List[Dict], retention_data: Dict) -> List[Dict]:
        """Professional Signal Fusion with Human-Editor Overrides."""
        duration = data.get("duration", 15.0)
        curve = retention_data.get("curve", [])
        
        fused_timeline = []
        for entry in curve:
            t = entry["t"]
            r = entry["r"]
            
            # Resolve other signals at time t
            e = self._get_spike_score_at(t, spikes)
            f = self._get_face_score(t, data.get("subject_tracking", []))
            m = self._get_motion_score(t, data.get("motion_scores", []))
            b = self._get_beat_alignment(t, data.get("beat_data", {}).get("beats", []))
            
            # Weighted Base Score
            score = (self.FUSION_RETENTION * r + 
                     self.FUSION_EMOTION * e + 
                     self.FUSION_MOTION * m + 
                     self.FUSION_BEAT * b + 
                     self.FUSION_FACE * f)
            
            # --- HUMAN EDITOR OVERRIDES ---
            tag = "baseline"
            if e >= 0.75:
                score *= 1.5
                tag = "climax_anchor"
            elif f >= 0.7 and e >= 0.6:
                score *= 1.4
                tag = "hero_moment"
            elif m < 0.2 and e < 0.3:
                score *= 0.3
                tag = "dead_zone"
                
            fused_timeline.append({
                "time": t,
                "score": round(min(1.0, score), 4),
                "tag": tag
            })
            
        # Deduplicate with 1.5s gap
        fused_timeline.sort(key=lambda x: x["score"], reverse=True)
        final_moments = []
        for m in fused_timeline:
            if not any(abs(m["time"] - fm["time"]) < 1.5 for fm in final_moments):
                final_moments.append(m)
            if len(final_moments) >= 10:
                break
                
        final_moments.sort(key=lambda x: x["time"])
        return final_moments

    def _get_spike_score_at(self, t: float, spikes: List[Dict]) -> float:
        if not spikes: return 0.0
        nearby = [s for s in spikes if abs(s["time"] - t) <= 0.8]
        return max((s["score"] for s in nearby), default=0.0)

    def _detect_spikes(self, data: Dict[str, Any]) -> List[Dict]:
        """Hybrid Spike Detection: Algo + Gemini Vision."""
        duration = data.get("duration", 15.0)
        face_data = data.get("subject_tracking", [])
        motion_data = data.get("motion_scores", [])
        beat_data = data.get("beat_data", {}).get("beats", [])
        
        timeline = []
        # Sample every 0.5s
        t = 0.0
        while t <= duration:
            f = self._get_face_score(t, face_data)
            m = self._get_motion_score(t, motion_data)
            a = self._get_audio_spike(t, beat_data)
            
            score = (self.WEIGHT_EMO_FACE * f + 
                     self.WEIGHT_EMO_MOTION * m + 
                     self.WEIGHT_EMO_AUDIO * a)
            
            timeline.append({"time": t, "score": score})
            t += 0.5
            
        if not timeline:
            return []
            
        # Detect peaks (Mean + 1.2 StdDev)
        scores = [e["score"] for e in timeline]
        mean = sum(scores) / len(scores)
        std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        threshold = mean + 1.2 * std
        
        spikes = [e for e in timeline if e["score"] >= threshold]
        # Sort by score descending
        spikes.sort(key=lambda x: x["score"], reverse=True)
        
        # Keep top 5 unique-ish spikes (min 1.5s gap)
        unique_spikes = []
        for s in spikes:
            if not any(abs(s["time"] - us["time"]) < 1.5 for us in unique_spikes):
                unique_spikes.append(s)
            if len(unique_spikes) >= 5:
                break
                
        return unique_spikes

    def _build_retention_curve(self, data: Dict[str, Any]) -> Dict:
        """Predicts where viewers will stay vs drop off."""
        duration = data.get("duration", 15.0)
        motion_data = data.get("motion_scores", [])
        face_data = data.get("subject_tracking", [])
        beat_data = data.get("beat_data", {}).get("beats", [])
        
        curve = []
        t = 0.0
        while t <= duration:
            m = self._get_motion_score(t, motion_data)
            f = self._get_face_score(t, face_data)
            b = self._get_beat_alignment(t, beat_data)
            d = 0.5 # Default dialogue signal
            
            r = (self.WEIGHT_MOTION * m + 
                 self.WEIGHT_FACE * f + 
                 self.WEIGHT_BEAT * b + 
                 self.WEIGHT_DIALOGUE * d)
            
            curve.append({"t": round(t, 2), "r": round(r, 4)})
            t += 0.5
            
        # Find best segment (3-5s window with highest avg retention)
        best_start = 0.0
        max_r = 0.0
        window_size = 5 # 2.5 seconds
        
        for i in range(len(curve) - window_size):
            avg = sum(c["r"] for c in curve[i:i+window_size]) / window_size
            if avg > max_r:
                max_r = avg
                best_start = curve[i]["t"]
                
        return {
            "curve": curve,
            "best_segment_start": best_start,
            "avg_retention": max_r
        }

    def _find_hook(self, data: Dict[str, Any]) -> Dict:
        """Finds the most attention-grabbing moment in first 3s."""
        spikes = data.get("emotional_spikes", [])
        # Look for strongest spike in first 3.5 seconds
        hook_candidates = [s for s in spikes if s["time"] <= 3.5]
        
        if hook_candidates:
            best = max(hook_candidates, key=lambda x: x["score"])
            return {"time": best["time"], "score": best["score"], "type": "spike"}
            
        return {"time": 0.0, "score": 0.5, "type": "default"}

    # --- Signal Resolvers ---

    def _get_motion_score(self, t: float, motion_data: List[Dict]) -> float:
        if not motion_data: return 0.5
        # Find nearest
        nearest = min(motion_data, key=lambda x: abs(x.get("time", 0) - t))
        return nearest.get("score", 0.5)

    def _get_face_score(self, t: float, face_data: List[Dict]) -> float:
        if not face_data: return 0.0
        nearby = [f for f in face_data if abs(f.get("time", 0) - t) <= 0.4]
        if not nearby: return 0.0
        # Score by size/dominance
        return max(f.get("score", 0.5) for f in nearby)

    def _get_audio_spike(self, t: float, beats: List[Any]) -> float:
        if not beats: return 0.0
        # Check if t is near a high-energy beat
        nearby = [b for b in beats if abs((b.get("time", 0) if isinstance(b, dict) else b) - t) <= 0.2]
        return 0.8 if nearby else 0.2

    def _get_beat_alignment(self, t: float, beats: List[Any]) -> float:
        if not beats: return 0.0
        # Decay alignment score based on distance from beat
        min_dist = min(abs((b.get("time", 0) if isinstance(b, dict) else b) - t) for b in beats)
        return max(0.0, 1.0 - (min_dist / 0.5))

content_brain = ContentBrain()
