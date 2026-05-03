import os
import logging
import subprocess
import wave
import struct
import math
import tempfile
from typing import List, Dict, Any

logger = logging.getLogger("beat_engine")

FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")

class BeatEngine:
    """
    Mobile-optimized Beat Detection for AMTCE.
    Uses chunked PCM analysis to remain stable on 4GB RAM devices.
    """
    def __init__(self):
        self.sensitivity = 1.35  # Swarm Approved: 1.35x multiplier
        self.min_beat_interval = 0.45  # Swarm Approved: 0.45s debounce
        self.window_size = 0.05  # 50ms window for smoothing
        self.chunk_size_sec = 30  # Analyze in 30-second blocks to save RAM

    def analyze_beats_with_drops(self, audio_path: str) -> Dict[str, Any]:
        """
        Full analysis: beats, drops, BPM, energy, vibe.
        """
        if not os.path.exists(audio_path):
            return {"beats": [], "drops": [], "tempo": 120, "avg_energy": 0.5, "vibe": "neutral"}

        # 1. Convert to temporary WAV (16-bit PCM, Mono, 44.1kHz)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_wav = tmp.name

        try:
            cmd = [
                FFMPEG_BIN, "-y", "-i", audio_path,
                "-ac", "1", "-ar", "44100", "-acodec", "pcm_s16le",
                temp_wav
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            
            return self._process_wav_chunked(temp_wav)

        except Exception as e:
            logger.error(f"🥁 Beat analysis failed: {e}")
            return {"beats": [], "drops": [], "tempo": 120, "avg_energy": 0.5, "vibe": "neutral"}
        finally:
            if os.path.exists(temp_wav):
                try: os.remove(temp_wav)
                except: pass

    def _process_wav_chunked(self, wav_path: str) -> Dict[str, Any]:
        beats_raw = []
        envelopes = []
        
        try:
            with wave.open(wav_path, 'rb') as wf:
                framerate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                if sampwidth != 2: return {"beats": [], "drops": []}

                # Calculate windows per chunk
                window_samples = int(framerate * self.window_size)
                
                # We read in chunks to keep memory usage low
                # Each chunk is ~5MB of raw PCM
                while True:
                    frames = wf.readframes(framerate * self.chunk_size_sec)
                    if not frames: break
                    
                    count = len(frames) // 2
                    samples = struct.unpack(f"<{count}h", frames)
                    
                    # Process envelopes for this chunk
                    for i in range(0, len(samples), window_samples):
                        chunk = samples[i:i + window_samples]
                        if not chunk: continue
                        rms = math.sqrt(sum(s * s for s in chunk) / len(chunk))
                        envelopes.append(rms)

            # Peak Detection on full envelope list
            # (Envelopes for a 1min song is only ~1200 floats, safe for RAM)
            local_window = 40
            last_beat_time = -self.min_beat_interval
            
            for i, amp in enumerate(envelopes):
                start = max(0, i - local_window // 2)
                end = min(len(envelopes), i + local_window // 2)
                context = envelopes[start:end]
                avg_energy = sum(context) / len(context) if context else 0
                
                threshold = avg_energy * self.sensitivity
                time_sec = i * self.window_size
                
                if amp > threshold and amp > 1000:
                    if time_sec - last_beat_time >= self.min_beat_interval:
                        beats_raw.append(time_sec)
                        last_beat_time = time_sec

            # Drop Detection
            drops_raw = self._detect_drops(envelopes, beats_raw)
            
            # Metadata construction
            max_energy = max(envelopes) if envelopes else 1.0
            beats_full = []
            for b in beats_raw:
                idx = int(b / self.window_size)
                e_val = envelopes[idx] if idx < len(envelopes) else 0
                beats_full.append({
                    "time": b,
                    "energy": round(min(1.0, e_val / max_energy), 3) if max_energy > 0 else 0.5
                })

            # Tempo & Vibe
            tempo = 120.0
            if len(beats_raw) >= 4:
                intervals = [beats_raw[i+1] - beats_raw[i] for i in range(len(beats_raw)-1)]
                tempo = round(60.0 / (sum(intervals)/len(intervals)), 1)

            avg_energy = round(sum(b["energy"] for b in beats_full) / len(beats_full), 3) if beats_full else 0.5
            
            def _get_vibe(b, e):
                if b > 145: return "explosive"
                if b > 115: return "hype"
                if b > 85: return "groove"
                return "cinematic"

            return {
                "beats": beats_full,
                "drops": drops_raw,
                "tempo": tempo,
                "avg_energy": avg_energy,
                "vibe": _get_vibe(tempo, avg_energy)
            }

        except Exception as e:
            logger.error(f"❌ Chunked WAV processing failed: {e}")
            return {"beats": [], "drops": []}

    def _detect_drops(self, envelopes: list, beats: list) -> list:
        drops = []
        drop_ratio = 2.5
        window_size = self.window_size
        
        for beat_time in beats:
            idx = int(beat_time / window_size)
            pre = envelopes[max(0, idx-10):idx]
            post = envelopes[idx:min(len(envelopes), idx+10)]
            
            if not pre or not post: continue
            
            pre_e = sum(pre)/len(pre)
            post_e = sum(post)/len(post)
            
            if post_e / max(pre_e, 50) >= drop_ratio:
                drops.append(beat_time)
        return drops

engine = BeatEngine()

def get_beats_with_drops(path: str) -> Dict[str, Any]:
    return engine.analyze_beats_with_drops(path)
