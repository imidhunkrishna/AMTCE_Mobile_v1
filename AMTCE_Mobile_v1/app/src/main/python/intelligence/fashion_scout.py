# engine/intelligence/fashion_scout.py
import logging
import json
import re
from typing import Dict, List, Optional
from intelligence.gemini_client import GeminiClient

logger = logging.getLogger("amtce.fashion_scout")

FASHION_SCOUT_PROMPT = """
YOU ARE A SENIOR FASHION FORENSIC ANALYST + AMAZON SEARCH OPTIMIZATION EXPERT.
YOU HAVE 15+ YEARS EXPERIENCE IN LUXURY FASHION, STREETWEAR, ETHNIC WEAR, AND SPORTSWEAR.

YOUR JOB:
1. Perform DEEP visual forensics on every garment visible in the image
2. Extract hyper-specific attributes — no guessing, no generalizing
3. Build HIGH-CONVERSION Amazon search queries using only findable, real product terms
4. Return STRICT JSON — zero prose, zero markdown

ABSOLUTE RULES:
* BANNED WORDS: stylish, trendy, nice, beautiful, elegant, chic, modern, classic
* ADVANCED WEAR DETECTION: Do not use generic names. Use hyper-specific structural terms (e.g. asymmetrical ruched peplum, tiered organza A-line).
* COLOR USAGE RESTRICTION: AVOID using colors in the description or search query UNLESS the garment structure/wear name is mostly non-understandable or highly ambiguous.
* Every word must directly help a shopper FIND this exact product
* If unsure about a field, make your BEST SPECIFIC GUESS — never leave fields empty
* Fabric texture, sheen, drape, weight — all detectable visually. Analyze them.
* DO NOT use any text overlaid on the video frame as a source of truth for garment info.

STEP 1 — ATTRIBUTE FORENSICS
A. COLOR: primary shade, secondary, tone, finish
B. FABRIC: exact material, weight, texture, sheen, structure
C. FIT: fit_type, silhouette, length, waist_style, sleeve_type, neckline, closure, lining
D. PATTERN: type, scale, embellishment, placement
E. CLASSIFICATION: primary_category, sub_category, gender_target, age_group, occasion
F. BRAND DNA: brand_style_match, price_tier, market
G. STYLING: body_coverage, season_suitability, styling_notes

CATEGORY ENUM: saree|lehenga|kurta|salwar-kameez|anarkali|sharara|dress|top|blouse|shirt|t-shirt|polo|hoodie|sweatshirt|jacket|blazer|coat|denim-jacket|leather-jacket|vest|jeans|trousers|shorts|skirt|leggings|joggers|cargo-pants|ethnic-set|co-ord-set|jumpsuit|romper|swimwear|activewear|saree-blouse|dupatta|shawl|scarf|accessory|footwear|bag

STEP 2 — AMAZON SEARCH QUERY
Formula: [Fabric] + [Fit] + [Category] + [Key Detail] + [Occasion] (+ [Color] ONLY if wear name is ambiguous)
Rules: 6-10 words max, exact Amazon-searchable terms. 

STEP 3 — SEO KEYWORDS (exactly 7)
* 2 technical spec keywords
* 2 brand-style keywords
* 2 occasion-fit keywords
* 1 direct buyer search phrase

OUTPUT — STRICT JSON ONLY.
{
  "attributes": {
    "color": {"primary": "", "secondary": "", "tone": "", "finish": ""},
    "fabric": {"primary_material": "", "weight": "", "texture": "", "sheen": "", "structure": ""},
    "fit": {"fit_type": "", "silhouette": "", "length": "", "waist_style": "", "sleeve_type": "", "neckline": "", "closure_type": "", "lining": ""},
    "pattern": {"type": "", "scale": "", "embellishment": "", "placement": ""},
    "classification": {"primary_category": "", "sub_category": "", "gender_target": "", "age_group": "", "occasion": ""},
    "brand_dna": {"brand_style_match": "", "price_tier": "", "market": ""},
    "styling": {"body_coverage": "", "season_suitability": "", "styling_notes": ""}
  },
  "outfit_description": "",
  "search_query": "",
  "seo_keywords": [],
  "vibe": "LUXURY|STREETWEAR|MINIMALIST|ETHNIC|ATHLEISURE",
  "confidence": {"overall": 0.0}
}
"""

REFINEMENT_PROMPT = """
YOU PREVIOUSLY GENERATED A LOW-CONFIDENCE FASHION ANALYSIS RESULT.
Re-examine the same image and produce a STRICTLY IMPROVED output.
FOCUS: Better material detection, color accuracy, specific search query.
RETURN IMPROVED JSON NOW.
"""


class FashionScout:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    def analyze(self, image_path: str) -> Optional[Dict]:
        """Runs visual analysis on a single frame."""
        try:
            # Note: In a real mobile app, we'd pass the actual image bytes or path to the Gemini SDK
            # Here we simulate the prompt execution
            res = self.gemini.generate_json(FASHION_SCOUT_PROMPT)
            if res:
                return self._parse_and_enrich(res)
        except Exception as e:
            logger.error(f"Fashion Scout failed: {e}")
        return None

    def _parse_and_enrich(self, raw_json: str) -> Dict:
        try:
            data = json.loads(raw_json)
            # Add Amazon Search Links
            query = data.get("search_query", "fashion wear").replace(" ", "+")
            data["search_links"] = {
                "amazon_us": f"https://www.amazon.com/s?k={query}",
                "amazon_in": f"https://www.amazon.in/s?k={query}"
            }
            return data
        except:
            return {}
