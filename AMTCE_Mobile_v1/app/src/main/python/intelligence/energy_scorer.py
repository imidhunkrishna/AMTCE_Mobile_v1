import logging
import os
import subprocess
import math
from typing import List, Dict

logger = logging.getLogger("amtce.energy_scorer")

def score_segments(video_path: str, segments: List[Dict]) -> List[Dict]:
    """
    Annotates segments with audio energy scores using FFmpeg astats.
    This identifies the loudest/most energetic moments for dynamic zooms.
    """
    if not segments: return segments
    if not os.path.exists(video_path): return segments

    logger.info(f"🎵 [EnergyScorer] Analyzing audio energy for {len(segments)} segments.")
    
    scored_segments = []
    for seg in segments:
        start = seg.get("start", 0.0)
        end = seg.get("end", 1.0)
        duration = max(0.1, end - start)

        # FFmpeg command to get RMS stats for this segment
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-t", str(duration),
            "-i", video_path,
            "-vn",
            "-filter:a", "astats=metadata=1:reset=1",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, timeout=10)
            stderr = result.stderr.decode(errors="ignore")
            
            # Extract RMS level dB
            rms_db = -60.0
            for line in stderr.splitlines():
                if "RMS_level" in line and "Overall" in line:
                    try:
                        rms_db = float(line.split("=")[-1].strip())
                        break
                    except: pass
            
            # Convert dB to 0-1 score
            # -60dB is silence, 0dB is max
            score = max(0.0, min(1.0, (rms_db + 60.0) / 60.0))
            seg["energy_score"] = round(score, 4)
            seg["importance"] = seg["energy_score"] # Legacy compat
        except Exception as e:
            logger.warning(f"⚠️ [EnergyScorer] Failed to score segment {start}-{end}: {e}")
            seg["energy_score"] = 0.5
            seg["importance"] = 0.5
            
        scored_segments.append(seg)

    return scored_segments
