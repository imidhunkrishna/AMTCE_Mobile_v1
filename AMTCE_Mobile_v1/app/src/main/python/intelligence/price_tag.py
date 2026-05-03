import logging
import random
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("price_tag")

class PriceTagEngine:
    """
    Android Premium Price Tag Engine.
    Implements price psychology and adaptive overlay placement.
    """

    def __init__(self):
        self._price_counter = 0

    def get_premium_price(self, lo: int, hi: int) -> int:
        """
        Price Psychology: Multiples of 7 feel 'Auspicious' and 'Calculated'.
        Every 7th price breaks the pattern with a 'Human' number (e.g., ₹8,499).
        """
        self._price_counter += 1
        
        # Pattern Break
        if self._price_counter % 7 == 0:
            raw = random.randint(lo, hi)
            return (raw // 100) * 100 + 99
            
        # Multiple of 7
        raw = random.randint(lo, hi)
        base = 7000
        above_base = max(0, raw - base)
        rounded = round(above_base / 7) * 7
        return base + rounded

    def compute_anchor(self, width: int, height: int, human_box: List[float], face_box: List[float] = None) -> Tuple[int, int]:
        """
        Adaptive Anchor System: Targets the garment (chest/torso).
        Ensures the tag never covers the face.
        """
        hx, hy, hw, hh = human_box # [x, y, w, h]
        
        if face_box:
            # Anchor below the chin
            fx, fy, fw, fh = face_box
            chin_y = fy + fh
            target_y = chin_y + (hh * 0.1) # 10% below chin
            # Clamp to mid-torso
            target_y = min(target_y, hy + (hh * 0.5))
        else:
            # No face: Target upper 40% of body box
            target_y = hy + (hh * 0.4)
            
        target_x = hx + (hw / 2) # Horizontal center
        
        return int(target_x), int(target_y)

    def generate_metadata(self, fashion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the price and placement metadata for the video engine.
        """
        # 1. Price Logic
        tiers = (7000, 15000) # Fallback range
        clone_price = self.get_premium_price(tiers[0], tiers[1])
        original_price = int(clone_price * random.uniform(1.5, 2.5))
        
        # 2. Placement Logic
        # (Mock boxes for logic demonstration)
        human_box = [0.2, 0.1, 0.6, 0.8] 
        face_box = [0.4, 0.15, 0.2, 0.15]
        
        anchor_x, anchor_y = self.compute_anchor(1080, 1920, human_box, face_box)
        
        data = {
            "original_price": f"₹{original_price:,}",
            "sale_price": f"₹{clone_price:,}",
            "savings_pct": int(((original_price - clone_price) / original_price) * 100),
            "anchor": {"x": anchor_x, "y": anchor_y},
            "urgency": "Selling fast - Stock dropping fast! 🔥"
        }
        
        logger.info(f"🏷️ [PriceTag] Metadata Generated: {data['sale_price']} at ({anchor_x}, {anchor_y})")
        return data

price_tag = PriceTagEngine()
