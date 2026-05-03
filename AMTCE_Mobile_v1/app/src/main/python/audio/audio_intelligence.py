import os
import json
import logging
import sqlite3
import hashlib
import time
from typing import Dict, Any, Optional
from google import genai
from .beat_engine import get_beats_with_drops

logger = logging.getLogger("audio_intelligence")

# ─── Config ───────────────────────────────────────────────────────────────────
CACHE_DB = os.path.join(os.getenv("AMTCE_MEMORY_DIR", "intelligence/memory"), "audio_intel_cache.db")
ENABLE_GEMINI_INTEL = os.getenv("ENABLE_GEMINI_AUDIO", "true").lower() in ("true", "1", "yes")

_PROMPT = """You are a music supervisor. Listen and return ONLY a strict JSON object:
{
  "has_vocals": bool,
  "tempo_bpm": float,
  "dominant_emotion": "joy|hype|power|sadness|neutral",
  "energy_profile": "low|medium|high|explosive",
  "sections": [{"start": float, "end": float, "type": "intro|verse|chorus|drop", "energy": float}],
  "tension_arc": [{"time": float, "tension": float}],
  "emotional_peak_moments": [float]
}
"""

class AudioIntelligence:
    def __init__(self):
        os.makedirs(os.path.dirname(CACHE_DB), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audio_cache (
                    hash TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp REAL
                )
            """)

    def _get_fingerprint(self, file_path: str) -> str:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            while chunk:
                hasher.update(chunk)
                chunk = f.read(8192)
        return hasher.hexdigest()

    def get_report(self, audio_path: str) -> Dict[str, Any]:
        """
        Main entry point. Returns cached report, Gemini report, or local fallback.
        """
        if not os.path.exists(audio_path):
            return {}

        file_hash = self._get_fingerprint(audio_path)
        
        # 1. Check Cache
        cached = self._read_cache(file_hash)
        if cached:
            logger.info(f"🎧 Audio Intelligence: Cache Hit ({file_hash[:8]})")
            return cached

        # 2. Local Base Analysis (Always do this as baseline/fallback)
        local_data = get_beats_with_drops(audio_path)
        
        # 3. Gemini High-Level Analysis
        if ENABLE_GEMINI_INTEL:
            gemini_data = self._call_gemini(audio_path)
            if gemini_data:
                # Merge local beats with Gemini structural intel
                local_data.update(gemini_data)
                self._write_cache(file_hash, local_data)
                return local_data

        return local_data

    def _read_cache(self, file_hash: str) -> Optional[Dict]:
        try:
            with sqlite3.connect(CACHE_DB) as conn:
                cursor = conn.execute("SELECT data FROM audio_cache WHERE hash = ?", (file_hash,))
                row = cursor.fetchone()
                return json.loads(row[0]) if row else None
        except: return None

    def _write_cache(self, file_hash: str, data: Dict):
        try:
            with sqlite3.connect(CACHE_DB) as conn:
                conn.execute("INSERT OR REPLACE INTO audio_cache (hash, data, timestamp) VALUES (?, ?, ?)",
                            (file_hash, json.dumps(data), time.time()))
        except: pass

    def _call_gemini(self, audio_path: str) -> Optional[Dict]:
        try:
            from intelligence.gemini_router import gemini_router
            logger.info(f"🎵 Requesting Musical Intelligence from Gemini for {os.path.basename(audio_path)}...")
            
            # Note: In a real mobile app, you'd use a dedicated uploader for speed
            # But here we follow the desktop logic for consistency
            uploaded_file = genai.upload_file(audio_path)
            
            # Simple wait loop
            for _ in range(30):
                if genai.get_file(uploaded_file.name).state.name == "ACTIVE": break
                time.sleep(1)
            
            raw_response = gemini_router.generate(
                task_type="analysis",
                prompt=[uploaded_file, _PROMPT],
                module_name="audio_intelligence"
            )
            
            # Cleanup
            genai.delete_file(uploaded_file.name)
            
            # Parse JSON
            match = __import__("re").search(r"\{.*\}", raw_response, __import__("re").DOTALL)
            return json.loads(match.group(0)) if match else None

        except Exception as e:
            logger.warning(f"⚠️ Gemini Audio Intel failed: {e}")
            return None

intel_engine = AudioIntelligence()

def analyze_audio(path: str) -> Dict[str, Any]:
    return intel_engine.get_report(path)
