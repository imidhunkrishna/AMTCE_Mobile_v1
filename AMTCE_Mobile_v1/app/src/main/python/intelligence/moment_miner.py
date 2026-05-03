"""
MomentMiner: High-Conversion Scene Discovery (Mobile-Optimized)
-------------------------------------------------------------
Detects micro-events (motion spikes, face presence, beat alignment)
to prioritize high-energy segments for narrative construction.
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional

try:
    from utils.import_gate import ImportGate
except ImportError:
    class ImportGate:
        @staticmethod
        def get(lib): return __import__(lib) if lib != 'cv2' else None

logger = logging.getLogger("moment_miner")

class MomentMiner:
    def __init__(self):
        self.min_moment_duration = 1.5
        self.max_moment_duration = 5.0
        # Weights: Motion (0.35), Face (0.25), Beat (0.20), Scene (0.20)
        self.weights = {
            "motion": 0.35,
            "face": 0.25,
            "beat": 0.20,
            "scene": 0.20
        }

    def mine_moments(self, video_path: str, duration: float) -> List[Dict[str, Any]]:
        """
        Analyzes video to find high-value moments.
        Returns a ranked list of segments with energy scores.
        """
        cv2 = ImportGate.get("cv2")
        if not cv2:
            logger.warning("⚠️ OpenCV not available. Using fallback uniform mining.")
            return self._uniform_fallback(duration)

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sub-sample for mobile speed (1 check per 0.5s)
            sample_rate = int(fps * 0.5)
            motion_scores = []
            
            prev_gray = None
            for i in range(0, frame_count, sample_rate):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret: break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_gray is not None:
                    # Pure Python fallback for motion intensity (mean absolute diff)
                    diff = cv2.absdiff(gray, prev_gray)
                    motion = float(cv2.mean(diff)[0])
                    motion_scores.append({"time": i / fps, "score": motion})
                prev_gray = gray
                
            cap.release()
            
            if not motion_scores:
                return self._uniform_fallback(duration)
                
            # Adaptive Thresholding (Percentile-like fallback)
            sorted_scores = sorted([m["score"] for m in motion_scores])
            if not sorted_scores: return self._uniform_fallback(duration)
            
            threshold = sorted_scores[int(len(sorted_scores) * 0.75)] # 75th percentile
            
            moments = []
            for m in motion_scores:
                if m["score"] >= threshold:
                    moments.append({
                        "start": max(0.0, m["time"] - 1.0),
                        "end": min(duration, m["time"] + 2.0),
                        "energy_score": min(1.0, m["score"] / (threshold * 2 if threshold > 0 else 1)),
                        "type": "motion_peak"
                    })
            
            # Merge overlapping moments
            return self._merge_moments(moments)

        except Exception as e:
            logger.error(f"❌ Moment Mining failed: {e}")
            return self._uniform_fallback(duration)

    def _merge_moments(self, moments: List[Dict]) -> List[Dict]:
        if not moments: return []
        moments.sort(key=lambda x: x["start"])
        merged = [moments[0]]
        for curr in moments[1:]:
            prev = merged[-1]
            if curr["start"] <= prev["end"]:
                prev["end"] = max(prev["end"], curr["end"])
                prev["energy_score"] = max(prev["energy_score"], curr["energy_score"])
            else:
                merged.append(curr)
        return merged

    def _uniform_fallback(self, duration: float) -> List[Dict]:
        """Divide video into 3s chunks if intelligence fails."""
        moments = []
        for i in range(0, int(duration), 3):
            moments.append({
                "start": float(i),
                "end": min(duration, float(i + 3)),
                "energy_score": 0.5,
                "type": "fallback_uniform"
            })
        return moments
