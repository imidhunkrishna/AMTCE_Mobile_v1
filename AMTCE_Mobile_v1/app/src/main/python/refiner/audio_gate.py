# engine/refiner/audio_gate.py
import subprocess
import json
import logging
import os

logger = logging.getLogger("amtce.audio_gate")

class AudioGate:
    """
    Lightweight Audio Quality Sentinel (Swarm Optimized).
    Uses FFmpeg astats to detect garbage/ambient noise without high RAM usage.
    """

    def __init__(self):
        self.ffprobe_path = "ffprobe" # Assumed in PATH on Android/Linux

    def analyze_quality(self, video_path: str) -> dict:
        """
        Returns a quality report: { 'is_music': bool, 'score': float, 'action': str }
        """
        logger.info(f"🎵 Analyzing Audio: {os.path.basename(video_path)}")
        
        cmd = [
            self.ffprobe_path, "-v", "error",
            "-show_entries", "frame=pkt_pts_time:side_data_list",
            "-select_streams", "a",
            "-af", "astats=metadata=1:reset=1",
            "-show_entries", "frame_tags=lavfi.astats.Overall.RMS_level",
            "-of", "json", video_path
        ]

        try:
            # We only sample the first 5 seconds to save battery
            result = subprocess.run(cmd + ["-read_intervals", "%+5"], capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            
            frames = data.get("frames", [])
            if not frames:
                return {"is_music": False, "score": 0.0, "reason": "No audio stream"}

            # Calculate RMS variance (erratic spikes = noise, rhythmic = music)
            rms_values = [float(f["tags"]["lavfi.astats.Overall.RMS_level"]) for f in frames if "tags" in f]
            
            if not rms_values:
                return {"is_music": False, "score": 0.0, "reason": "Silence detected"}

            avg_rms = sum(rms_values) / len(rms_values)
            variance = sum((x - avg_rms) ** 2 for x in rms_values) / len(rms_values)

            # --- THE MAGIC NUMBERS (Optimized for Mobile) ---
            # Real music has consistent rhythmic energy.
            # Crowd noise/wind has high erratic variance.
            is_music = variance < 50.0 and avg_rms > -60.0
            
            return {
                "is_music": is_music,
                "rms_avg": avg_rms,
                "variance": variance,
                "action": "keep" if is_music else "overlay_bgm"
            }

        except Exception as e:
            logger.error(f"Audio Gate check failed: {e}")
            return {"is_music": True, "score": 0.5, "action": "fallback_keep"}
