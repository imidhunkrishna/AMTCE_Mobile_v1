import logging
from typing import Dict, List, Any

logger = logging.getLogger("monetization_scorer")

class MonetizationRewardScorer:
    """
    Evaluates the 'Profit Potential' of a video mission.
    Used for the self-optimizing learning loop.
    """

    def compute_fitness(self, render_plan: Dict, ai_data: Dict) -> float:
        """
        Calculates a score from 0.0 to 1.0 based on viral/monetization heuristics.
        """
        segments = render_plan.get("edited_segments", [])
        if not segments:
            return 0.0

        # 1. Hook Score (Critical for Monetization)
        # Prefer the best moment to be in the first 2.5 seconds
        first_seg_start = segments[0].get("start", 0.0)
        hook_score = max(0.0, 1.0 - (first_seg_start / 3.0)) # Rapid decay after 3s

        # 2. Interest Strength
        # Average score of all fused moments included in the edit
        moments = ai_data.get("fused_moments", [])
        if moments:
            avg_interest = sum(m.get("score", 0.0) for m in moments) / len(moments)
        else:
            avg_interest = 0.5

        # 3. Monetization Alignment (Fashion/Products)
        # Reward if a product or affiliate link is successfully attached
        monetization_bonus = 0.0
        if ai_data.get("affiliate_link"):
            monetization_bonus = 0.2
        if ai_data.get("fashion_scout"):
            monetization_bonus += 0.1

        # 4. Final Weighted Blend
        # 40% Hook, 40% Interest, 20% Monetization Bonus
        fitness = (0.40 * hook_score) + (0.40 * avg_interest) + monetization_bonus
        
        final_score = max(0.0, min(1.0, round(fitness, 3)))
        
        logger.info(f"💰 [RewardScorer] Final Fitness: {final_score} (Hook: {hook_score:.2f}, Interest: {avg_interest:.2f}, Bonus: {monetization_bonus:.2f})")
        return final_score

monetization_scorer = MonetizationRewardScorer()
