import os
import json
import logging
import base64
from typing import List, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger("system_memory")

class SegmentValidator:
    """
    Quality Gate for AI Edits. Prevents "Broken" or "Fake" editing.
    Ported from AMTCE Core_Modules/segment_validator.py.
    """
    
    def validate(self, candidate_moments: List[Dict], selected_segments: List[Dict], signal_data: Dict) -> Dict:
        """Determines if the edit is high quality and 'REAL'."""
        if not selected_segments:
            return {"verdict": "FAILED", "reason": "No segments selected"}

        results = []
        low_quality_count = 0
        total_score = 0
        
        # 1. Check Hook Integrity (Must start < 1.5s for Shorts)
        first_start = selected_segments[0].get("start", 0)
        hook_valid = first_start <= 1.5
        
        # 2. Check for Robotic Patterns (Varied clip lengths)
        durations = [float(s.get("end", 0)) - float(s.get("start", 0)) for s in selected_segments]
        avg_dur = sum(durations) / len(durations) if durations else 0
        variance = sum((d - avg_dur)**2 for d in durations) / len(durations) if durations else 0
        robotic = variance < 0.05 if len(durations) >= 3 else False
        
        # 3. Scene Reconstruction Check (Detect Lazy Trimming)
        # Check if segments are in chronological order
        starts = [s.get("start", 0) for s in selected_segments]
        is_chronological = all(starts[i] <= starts[i+1] for i in range(len(starts)-1))
        non_chronological = not is_chronological
        
        # 4. Individual Segment Scoring
        for seg in selected_segments:
            score = self._calculate_segment_score(seg, signal_data)
            total_score += score
            if score < 0.35:
                low_quality_count += 1
            results.append({"t": seg.get("start"), "score": score})
            
        avg_score = total_score / len(selected_segments)
        lq_ratio = low_quality_count / len(selected_segments)
        
        # [Architect Rule] Editing Effective = (Non-Chronological or Score >= 0.5) AND segments >= 3
        editing_effective = (non_chronological or avg_score >= 0.5) and len(selected_segments) >= 3
        
        # Verdict Logic
        verdict = "PASS"
        reasons = []
        
        if not editing_effective:
            verdict = "WARNING"
            reasons.append("LAZY_EDITING_DETECTED")
        if not hook_valid:
            verdict = "WARNING"
            reasons.append("WEAK_HOOK")
        if robotic:
            verdict = "WARNING"
            reasons.append("ROBOTIC_PATTERN")
        if lq_ratio > 0.4:
            verdict = "FAIL"
            reasons.append("LOW_QUALITY_SELECTION")
            
        return {
            "verdict": verdict,
            "reasons": reasons,
            "metrics": {
                "hook_start": first_start,
                "variance": round(variance, 4),
                "lq_ratio": round(lq_ratio, 2),
                "avg_score": round(avg_score, 2),
                "editing_effective": editing_effective
            }
        }

    def _calculate_segment_score(self, seg: Dict, signals: Dict) -> float:
        """Simplified S(t) = 0.4*Retention + 0.3*Emotion + 0.2*Beat + 0.1*Motion"""
        t = seg.get("start", 0)
        
        # Resolve signals from the signal_data (fallback to defaults)
        r = self._get_signal_val(t, signals.get("retention_data", {}).get("curve", []))
        e = self._get_signal_val(t, signals.get("emotional_spikes", []))
        m = self._get_signal_val(t, signals.get("motion_scores", []))
        
        return (r * 0.4 + e * 0.3 + m * 0.3) # simplified for mobile

    def _get_signal_val(self, t: float, signal_list: List[Dict]) -> float:
        if not signal_list: return 0.5
        nearby = [s for s in signal_list if abs(s.get("t", s.get("time", 0)) - t) <= 0.8]
        if not nearby: return 0.2
        return max(s.get("r", s.get("score", 0.5)) for s in nearby)


class SystemMemory:
    """
    Persistent Memory for AMTCE Mobile. 
    Stores "Proven Patterns" and successful edit strategies.
    """
    
    def __init__(self, storage_path: str = "internal/editor_memory.json"):
        self.path = Path(storage_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._memory = self._load()
        self.memory_db = self._memory.get("memory_db", {})

    def _encrypt(self, data: str) -> str:
        # 🛡️ SECURITY: Application-Level Encryption for local RAG memory
        key = os.getenv("GEMINI_API_KEY", "fallback_secure_key")
        if not key: key = "fallback_secure_key"
        encrypted = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
        return base64.b64encode(encrypted.encode('utf-8')).decode('utf-8')

    def _decrypt(self, b64data: str) -> str:
        key = os.getenv("GEMINI_API_KEY", "fallback_secure_key")
        if not key: key = "fallback_secure_key"
        try:
            encrypted = base64.b64decode(b64data.encode('utf-8')).decode('utf-8')
            return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted))
        except:
            return "{}"

    def _load(self) -> Dict:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.startswith("{"): return json.loads(content) # Fallback for old unencrypted files
                    return json.loads(self._decrypt(content))
            except:
                pass
        return {
            "memory_db": {},
            "patterns": {},
            "successful_edits": 0
        }

    def get_hints(self, niche: str, energy: float = 0.5) -> Dict[str, Any]:
        """
        Retrieves optimization hints from memory. 
        Uses RAG-style re-ranking based on niche and energy level.
        """
        # Default fallback
        hints = {
        }
        
        # Find top 3 patterns for this niche
        niche_patterns = {k.split(":")[1]: v for k, v in self._memory["patterns"].items() if k.startswith(f"{niche}:")}
        sorted_p = sorted(niche_patterns.items(), key=lambda x: x[1], reverse=True)
        hints["preferred_tags"] = [p[0] for p in sorted_p[:3]]
        
        return hints

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json_str = json.dumps(self._memory)
                f.write(self._encrypt(json_str))
        except Exception as e:
            logger.error(f"Memory save failed: {e}")

class DecisionEngine:
    """
    RAG-Enabled Decision Engine for Android.
    Enforces 'Zero-Call' mode if memory confidence is high.
    """
    
    def __init__(self, memory: SystemMemory):
        self.memory = memory

    def generate_plan(self, profile: Dict, niche: str) -> Dict:
        """Decides editing style: Gemini vs Local RAG."""
        hints = self.memory.get_hints(niche)
        
        # Determine RAG Confidence (Match desktop generate_with_rag)
        confidence = "LOW"
        if hints["preferred_tags"] and not hints["is_cold"]:
            confidence = "HIGH"
            
        if confidence == "HIGH":
            logger.info(f"⚡ [RAG] Confidence HIGH for {niche}. Using local deterministic plan.")
            top_pattern = hints["preferred_tags"][0]
            
            # Deterministic Mapping (Zero Gemini Call)
            return {
                "hook": f"Memory-backed {top_pattern} hook.",
                "editing_style": f"Learned {niche} strategy",
                "cut_density": "high" if profile.get("energy", 0.5) > 0.7 else "medium",
                "transition_style": "whip" if profile.get("energy", 0.5) > 0.8 else "smooth",
                "pacing": "fast" if profile.get("energy", 0.5) > 0.7 else "steady",
                "effects": ["Learned Color Grade"],
                "strategy_tags": ["rag_governed", "local_decision"],
                "reasoning": f"Local RAG match found for pattern: {top_pattern}",
                "rag_mode": True
            }
            
        logger.info(f"☁️ [RAG] Confidence LOW for {niche}. Escalating to Gemini.")
        return {"rag_mode": False}

system_memory = SystemMemory()
validator = SegmentValidator()
decision_engine = DecisionEngine(system_memory)
