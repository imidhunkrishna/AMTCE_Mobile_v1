import random
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("sales_copy")

class SalesCopyEngine:
    """
    Android Sales Copy Generator.
    Produces high-conversion captions for Instagram/YouTube.
    Enforces #AD compliance and rotates templates to avoid spam flags.
    """

    TEMPLATES = [
        # Template A: Professional & Scannable
        "#AD {hook}\n\n{title}\n✦ {benefit_1}\n✦ {benefit_2}\n✦ {benefit_3}\n\n"
        "MRP ₹{price_original} → ₹{price_sale} today ({discount}% off)\n\n"
        "Comment \"{keyword}\" and I'll DM the link instantly 👇\n\n"
        "As an Amazon Associate I earn from qualifying purchases.\n{hashtags}",

        # Template B: Personal & Direct
        "#AD — {hook}\n\n{title}\n\nWhat actually makes this worth it:\n"
        "— {benefit_1}\n— {benefit_2}\n— {benefit_3}\n\n"
        "Was ₹{price_original}, now ₹{price_sale} ({discount}% off).\n\n"
        "Drop \"{keyword}\" in the comments for the link 👇\n\n"
        "As an Amazon Associate I earn from qualifying purchases.\n{hashtags}"
    ]

    VIBE_HOOKS = {
        "LUXURY": ["Old-money look, no old-money price 😏", "Looks ₹20k. Isn't ₹20k 😱"],
        "CASUAL": ["The lazy-girl outfit that never misses ✨", "3 compliments in 10 minutes 🤯"],
        "DEFAULT": ["Everyone asks where this is from 👇", "This almost didn't make it to the feed 😏"]
    }

    def __init__(self):
        self._template_index = 0

    def build_caption(self, fashion_data: Dict[str, Any], niche: str = "fashion") -> str:
        """
        Builds a high-conversion caption string.
        """
        # 1. Select Template
        template = self.TEMPLATES[self._template_index % len(self.TEMPLATES)]
        self._template_index += 1

        # 2. Extract Data
        vibe = fashion_data.get("vibe", "DEFAULT").upper()
        hook = random.choice(self.VIBE_HOOKS.get(vibe, self.VIBE_HOOKS["DEFAULT"]))
        
        attrs = fashion_data.get("attributes", {}) or {}
        cat = (attrs.get("classification", {}) or {}).get("primary_category", "Outfit")
        title = f"My pick: {cat.title()}"

        # 3. Benefits (Simplified Fallback)
        benefits = [
            "Premium quality fabric",
            "True to size fit",
            "Perfect for daily wear"
        ]

        # 4. Mock Prices (In real app, pull from affiliate link data)
        price_org = 12999
        price_sale = 7999
        discount = int(((price_org - price_sale) / price_org) * 100)

        # 5. Render
        caption = template.format(
            hook=hook,
            title=title,
            benefit_1=benefits[0],
            benefit_2=benefits[1],
            benefit_3=benefits[2],
            price_original=f"{price_org:,}",
            price_sale=f"{price_sale:,}",
            discount=discount,
            keyword="LINK",
            hashtags="#Fashion #Trending #Shorts"
        )

        logger.info(f"📝 [SalesCopy] Generated caption ({len(caption)} chars)")
        return caption

sales_copy = SalesCopyEngine()
