"""
UploaderBridge: Multi-Platform Distribution & Safety (Mobile)
------------------------------------------------------------
Handles YouTube and Instagram distribution with automated safety.
Features: Metadata Hardening (Unique ID), Platform Lock, and Niche Auth.
"""

import os
import json
import logging
import uuid
import subprocess
import time
from typing import Dict, Optional, List

logger = logging.getLogger("uploader_bridge")

# --- Constants ---
CRED_ROOT = "Credentials/social_media"
PLATFORM_LOCK_FILE = "platform_safety.lock"
LOCK_DURATION_SEC = 7200 # 2 hours

class UploaderBridge:
    def __init__(self):
        self.active_lock = self._check_lock()

    def upload_mission(self, file_path: str, ai_data: Dict, niche: str) -> Dict:
        """Main entry point for mission distribution."""
        if self.active_lock:
            logger.warning("🚫 Platform Safety Lock is ACTIVE. Upload aborted.")
            return {"status": "locked", "reason": "Safety cooldown"}

        results = {}
        
        # 1. Metadata Hardening (Crucial for platform uniqueness)
        hardened_path = self._harden_metadata(file_path)
        
        # 2. YouTube Upload
        youtube_res = self._youtube_upload(hardened_path, ai_data, niche)
        results["youtube"] = youtube_res
        
        # 3. Instagram Upload (If enabled)
        if os.getenv("ENABLE_IG_UPLOAD", "yes").lower() == "yes":
            ig_res = self._instagram_upload(hardened_path, ai_data, niche)
            results["instagram"] = ig_res
            
        return results

    def _harden_metadata(self, file_path: str) -> str:
        """Injects a Unique ID into video metadata to prevent 'Reused Content' flags."""
        try:
            unique_id = str(uuid.uuid4())
            temp_path = file_path.replace(".mp4", "_hardened.mp4")
            
            # -metadata comment="ID:<uuid>" -c copy (No re-encoding)
            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-metadata", f"comment=Unique_ID:{unique_id}",
                "-c", "copy", temp_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return temp_path
        except Exception as e:
            logger.warning(f"⚠️ Metadata hardening failed: {e}. Using original file.")
            return file_path

    def _youtube_upload(self, file_path: str, ai_data: Dict, niche: str) -> Dict:
        """Simulated YouTube Upload Logic (Requires Google API Client)."""
        logger.info(f"🚀 Uploading to YouTube [Niche: {niche}]...")
        # In a real mobile app, this would trigger a WorkManager task or an Intent
        return {"status": "success", "link": "https://youtube.com/shorts/placeholder"}

    def _instagram_upload(self, file_path: str, ai_data: Dict, niche: str) -> Dict:
        """Simulated Instagram Upload Logic (Requires Meta Graph API)."""
        logger.info(f"📸 Uploading to Instagram [Niche: {niche}]...")
        return {"status": "success", "link": "https://instagram.com/reels/placeholder"}

    def _check_lock(self) -> bool:
        if not os.path.exists(PLATFORM_LOCK_FILE): return False
        try:
            with open(PLATFORM_LOCK_FILE, "r") as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < LOCK_DURATION_SEC:
                return True
            os.remove(PLATFORM_LOCK_FILE)
            return False
        except:
            return False

    def set_lock(self, reason: str):
        with open(PLATFORM_LOCK_FILE, "w") as f:
            json.dump({"timestamp": time.time(), "reason": reason}, f)
        self.active_lock = True
        logger.error(f"🛑 PLATFORM LOCK SET: {reason}")
