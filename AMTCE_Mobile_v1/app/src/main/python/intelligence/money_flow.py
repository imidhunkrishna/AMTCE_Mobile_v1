import random
import logging
import json
import os
from typing import Dict, List, Optional
from utils.file_ops import atomic_write

logger = logging.getLogger("amtce.money_flow")

# --- CLICK TRACKING FILE ---
_TRACK_FILE = "intelligence/hook_performance.json"

OFFER_MAP = {
    "LUXURY": {
        "hooks": [
            "She walked in wearing this and the entire room went quiet 😶\nGuess the price. Then guess again 👇",
            "3 people in that room recognised this look. You could be the 4th 😏\nPrice will shock you 👇",
            "This sold out in 4 hours. Someone left it in their cart.\nDon't be that person 👇",
            "Looks like ₹20,000. Feels like ₹20,000. Isn't ₹20,000 😱\nSee the actual price 👇",
        ],
        "hindi_hooks": [
            "Woh aayi aur poora room chup ho gaya 😶\nPrice dekh ke aankh phat jayegi 👇",
            "Yeh look ₹20,000 ka lagta hai. Yeh ₹20,000 ka nahi hai 😱👇",
            "4 ghante mein sold out. Kisi ne cart mein chhod diya.\nWoh galti mat karo 👇",
        ],
        "urgency": "Selling fast today.",
    },
    "STREETWEAR": {
        "hooks": [
            "This dropped. Sold out. Then resold for 3x the price 🔥\nOne restock. Right now 👇",
            "6 hours online before it was gone the first time 😱\nIt's back. Not for long 👇",
            "The colorway nobody was supposed to see publicly 👀\nNow it's yours 👇",
        ],
        "hindi_hooks": [
            "Yeh drop hua. Sold out. 3x pe resell hua 🔥\nEk restock. Abhi 👇",
            "6 ghante mein gone. Wapas aa gaya. Zyada time nahi 👇",
        ],
        "urgency": "Stock running out fast.",
    },
    "MINIMALIST": {
        "hooks": [
            "No logo. No pattern. No announcement.\nJust the right room — and this outfit 🖤👇",
            "People who dress like this never tell you where it's from.\nWe will 😏👇",
            "Quiet luxury has one rule: the cut is everything.\nThis cut is everything 👇",
        ],
        "hindi_hooks": [
            "Logo nahi. Pattern nahi. Sirf ek sahi room aur yeh outfit 🖤👇",
            "Jo log aise pehnte hain woh source nahi batate. Hum batate hain 😏👇",
        ],
        "urgency": "Few pieces left.",
    },
    "ATHLEISURE": {
        "hooks": [
            "She walked into the gym in this and the entire floor looked up 👀\nPrice below 👇",
            "Gymshark energy. Indian price.\nYou don't need to import it anymore 😏👇",
            "Her gym set costs less than your post-workout protein tub 😱\nSee the price 👇",
        ],
        "hindi_hooks": [
            "Gym mein aayi is mein aur sab ne dekha 👀\nPrice neeche hai 👇",
            "Gymshark energy. Indian price.\nImport karne ki zaroorat nahi 😏👇",
        ],
        "urgency": "Back in stock — limited units.",
    },
    "GLOBAL": {
        "hooks": [
            "Everyone scrolled past this.\nThe ones who didn't are wearing it now 🔥👇",
            "₹? and it looks like you spent 10x.\nWe tested it. It works 😏👇",
            "She got 3 compliments in 10 minutes.\nThis was the reason 😱👇",
        ],
        "hindi_hooks": [
            "Sabne scroll kiya.\nJinhone nahi kiya woh ab yeh pehnte hain 🔥👇",
            "₹? mein 10x lagta hai.\nHumne test kiya. Kaam karta hai 😏👇",
        ],
        "urgency": "Limited stock today.",
    },
}

class HookTracker:
    def __init__(self):
        self._data: Dict = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(_TRACK_FILE):
                with open(_TRACK_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        try:
            # Use atomic write from our utils to ensure no data loss on Android
            atomic_write(_TRACK_FILE, json.dumps(self._data, indent=2))
        except Exception as e:
            logger.warning(f"[HookTracker] Save failed: {e}")

    def record_serve(self, hook: str):
        entry = self._data.setdefault(hook, {"serves": 0, "clicks": 0})
        entry["serves"] += 1
        self._save()

    def get_ctr(self, hook: str) -> float:
        entry = self._data.get(hook, {})
        serves = entry.get("serves", 0)
        clicks = entry.get("clicks", 0)
        return clicks / serves if serves > 0 else 0.0

    def pick_best(self, hooks: List[str]) -> str:
        """Weighted random pick based on CTR."""
        ctrs = [self.get_ctr(h) for h in hooks]
        total = sum(ctrs)
        if total == 0:
            chosen = random.choice(hooks)
        else:
            r = random.uniform(0, total)
            cumulative = 0.0
            chosen = hooks[-1]
            for hook, ctr in zip(hooks, ctrs):
                cumulative += ctr
                if r <= cumulative:
                    chosen = hook
                    break
        self.record_serve(chosen)
        return chosen

class MoneyFlowEngine:
    def __init__(self):
        self.tracker = HookTracker()
        self._HIGH_INTENT_NICHES = ["LUXURY", "GLOBAL", "STREETWEAR", "MINIMALIST"]

    def get_optimized_offer(self, category: str = "GLOBAL") -> Dict:
        category = category.upper().strip()
        
        # Aliases
        _ALIASES = {
            "FITNESS": "ATHLEISURE",
            "GYM": "ATHLEISURE",
            "CASUAL": "GLOBAL",
        }
        category = _ALIASES.get(category, category)

        if category not in OFFER_MAP:
            category = "GLOBAL"

        offer_data = OFFER_MAP[category]
        selected_hook = self.tracker.pick_best(offer_data["hooks"])

        return {
            "category": category,
            "hook": selected_hook,
            "urgency": offer_data.get("urgency", ""),
        }

    def get_hinglish_hook(self, category: str = "GLOBAL") -> str:
        category = category.upper().strip()
        if category not in OFFER_MAP: category = "GLOBAL"
        
        offer_data = OFFER_MAP[category]
        hindi_hooks = offer_data.get("hindi_hooks", offer_data["hooks"])
        hook = self.tracker.pick_best(hindi_hooks)
        urgency = offer_data.get("urgency", "")
        return f"{hook}\n⚡ {urgency}" if urgency else hook

money_flow_engine = MoneyFlowEngine()
