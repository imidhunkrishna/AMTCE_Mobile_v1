import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("vanguard")

# ─── Config ───────────────────────────────────────────────────────────────────
REGISTRY_PATH = "vanguard/vanguard_registry.json"
MISSION_LOG = "logs/mission_dashboard.json"

class VanguardDirector:
    """
    Mobile Safety & Optimization Controller.
    Implements a simplified 3-Turn Vanguard Loop for Android.
    """
    def __init__(self):
        os.makedirs("vanguard", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        self._init_registry()

    def _init_registry(self):
        if not os.path.exists(REGISTRY_PATH):
            default_memory = {
                "winning_styles": {
                    "fashion": "Cinematic Slow Zoom | 1.2x | Warm LUT",
                    "lifestyle": "Micro-Captions | Center-Screen | High Hype",
                    "general": "80ms Beat Anticipation | Tight Hook <1.0s"
                },
                "safety_guardrails": {
                    "max_api_calls_per_mission": 5,
                    "max_render_retries": 2,
                    "cooldown_upload_hours": 2,
                    "ram_threshold_mb": 512
                },
                "failed_patterns": [
                    "Generic 'Link in Bio' captions",
                    "1080p60 exports on <4GB RAM (Causes OOM)",
                    "Saturation > 1.2 (Triggers AI-Slop filters)"
                ]
            }
            with open(REGISTRY_PATH, "w") as f:
                json.dump(default_memory, f, indent=2)

    def execute_mission_loop(self, niche: str, mission_task: str, context: Dict):
        """
        Turn 1: Plan (Local Memory)
        Turn 2: Execute (Renderer/Downloader)
        Turn 3: Verify & Repair (Self-Healing)
        """
        mission_id = f"m_{int(time.time())}"
        logger.info(f"🛡️ Vanguard: Mission {mission_id} started for {niche}.")
        
        # --- TURN 1: LOCAL PLANNING ---
        with open(REGISTRY_PATH, "r") as f:
            registry = json.load(f)
        
        # 0.1 Context Compaction (RAG Optimization)
        self.compact_memory()
        
        style_hint = registry["winning_styles"].get(niche, registry["winning_styles"]["general"])
        logger.info(f"📋 [TURN 1] Plan Formed: Using style '{style_hint}' (0 Tokens).")
        
        # --- TURN 2: EXECUTION ---
        # This is handled by the orchestrator, but Vanguard monitors the result
        return {
            "mission_id": mission_id,
            "style_hint": style_hint,
            "safety_profile": registry["safety_guardrails"]
        }

    def handle_failure(self, error_type: str, context: Dict) -> Dict:
        """
        Vanguard Self-Healing: Recommends repair strategies for Turn 3/4.
        """
        if "OOM" in error_type or "Memory" in error_type:
            logger.warning("🩹 Vanguard: OOM Detected. Recommending 'Efficiency' preset.")
            return {
                "action": "RETRY",
                "preset_override": "720p_30fps_fast",
                "reason": "OOM Prevention"
            }
        
        if "Ban" in error_type or "Lock" in error_type:
            logger.error("🛑 Vanguard: Safety Lock Triggered. Entering 2h Cooldown.")
            return {
                "action": "LOCK",
                "cooldown": 7200,
                "reason": "Platform Safety"
            }
            
        return {"action": "FAIL", "reason": "Unrecoverable error"}

    def compact_memory(self):
        """
        Cleans up old logs and RAG entries to keep mobile storage lean.
        Retains only high-fitness mission summaries.
        """
        if not os.path.exists(MISSION_LOG):
            return

        try:
            with open(MISSION_LOG, "r") as f:
                logs = json.load(f)
            
            # Keep only last 50 missions or last 24h
            if len(logs) > 50:
                logger.info(f"🧹 Vanguard: Compacting {len(logs)} missions to 50...")
                compacted = logs[-50:]
                with open(MISSION_LOG, "w") as f:
                    json.dump(compacted, f, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ Vanguard: Compaction failed ({e})")

vanguard = VanguardDirector()
