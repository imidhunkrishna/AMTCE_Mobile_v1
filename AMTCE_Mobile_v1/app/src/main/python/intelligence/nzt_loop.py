import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional
from utils.file_ops import atomic_write

logger = logging.getLogger("amtce.nzt_loop")

_NZT_MEMORY_PATH = "intelligence/nzt_memory.json"

class IntentVariantGenerator:
    """Generates N alternative edit plans by perturbing the base intent."""
    def generate(self, base_intent: Dict, candidate_moments: List[Dict], n_variants: int = 3) -> List[Dict]:
        variants = []
        v0 = dict(base_intent)
        v0["_variant_id"] = 0
        v0["_variant_label"] = "base"
        variants.append(v0)

        if not candidate_moments or n_variants <= 1:
            return variants

        # Extract potential hook/climax times from high-score moments
        sorted_moments = sorted(candidate_moments, key=lambda m: m.get("score", 0.0), reverse=True)
        top_times = [m.get("time", 0.0) for m in sorted_moments[:5]]
        
        duration = max([m.get("time", 0.0) for m in candidate_moments])
        
        for i in range(1, n_variants):
            variant = dict(base_intent)
            variant["_variant_id"] = i
            # Perturb times
            variant["hook_time"] = random.choice(top_times) if top_times else random.uniform(1.0, 3.0)
            variant["climax_time"] = random.uniform(duration * 0.7, duration * 0.9)
            variant["pacing_style"] = random.choice(["fast_cut", "rhythm_driven", "steady"])
            variant["_variant_label"] = f"variant_{i}"
            variants.append(variant)
            
        return variants

class NZTScorer:
    """Predictive scorer for edit variants."""
    def score(self, variant: Dict, context: Dict, candidate_moments: List[Dict]) -> float:
        hook_t = variant.get("hook_time", 0.0)
        # Find closest moment
        closest = min(candidate_moments, key=lambda m: abs(m.get("time", 0.0) - hook_t))
        moment_score = closest.get("score", 0.5)
        
        # Pacing bonus
        pacing = variant.get("pacing_style", "steady")
        pacing_bonus = 0.1 if pacing == "fast_cut" and context.get("niche") == "fashion" else 0.0
        
        return moment_score + pacing_bonus

class NZTSimulationLoop:
    """The 'Limitless' iterative planning engine for Android."""
    def __init__(self):
        self.generator = IntentVariantGenerator()
        self.scorer = NZTScorer()
        self._memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(_NZT_MEMORY_PATH):
            try:
                with open(_NZT_MEMORY_PATH, "r") as f: return json.load(f)
            except: return {}
        return {}

    def select_best(self, base_intent: Dict, context: Dict, candidate_moments: List[Dict]) -> Dict:
        start_t = time.time()
        try:
            variants = self.generator.generate(base_intent, candidate_moments)
            scored = []
            for v in variants:
                s = self.scorer.score(v, context, candidate_moments)
                scored.append((s, v))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            winner_score, winner = scored[0]
            
            logger.info(f"🚀 [NZT] Selected {winner.get('_variant_label')} with score {winner_score:.2f}")
            
            # Clean up and return
            result = {k: v for k, v in winner.items() if not k.startswith("_variant")}
            result["_nzt_score"] = winner_score
            return result
        except Exception as e:
            logger.error(f"❌ [NZT] Loop failed: {e}")
            return base_intent

nzt_loop = NZTSimulationLoop()
