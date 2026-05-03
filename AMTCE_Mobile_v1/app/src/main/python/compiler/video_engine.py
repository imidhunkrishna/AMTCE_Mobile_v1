import logging
import os
import subprocess
import json
from typing import List, Dict, Optional

logger = logging.getLogger("amtce.compiler.video_engine")

# --- MOBILE HARDWARE SETTINGS ---
# On Android, we MUST use h264_mediacodec for performance
HW_ENCODER = "h264_mediacodec" 
PIX_FMT = "yuv420p"

def get_video_info(path: str) -> Dict:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration,r_frame_rate",
            "-of", "json", path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        return {
            "width": int(stream.get("width", 1080)),
            "height": int(stream.get("height", 1920)),
            "duration": float(stream.get("duration", 0)),
            "fps": eval(stream.get("r_frame_rate", "30/1"))
        }
    except:
        return {"width": 1080, "height": 1920, "duration": 0, "fps": 30}

class VideoEngine:
    """
    Mobile-Optimized Single-Pass Pipeline Engine.
    Ported from AMTCE Desktop with Hardware Acceleration.
    """
    
    def render(self, input_path: str, output_path: str, timeline: Dict) -> bool:
        if not os.path.exists(input_path):
            return False

        logger.info(f"🏎️  [VideoEngine] Starting Hardware-Accelerated Render: {output_path}")
        
        # 1. Inputs
        inputs = ["-i", input_path]
        
        # 2. Build Filter Graph
        graph_nodes = []
        vid_node = "[0:v]"
        aud_node = "[0:a]"
        
        # -- STAGE A: Trim & Reset --
        # We handle this via simple -ss and -t if it's a single clip, 
        # but for complex timelines we use the filter graph.
        
        # -- STAGE B: Zooms & Pacing --
        zoom_effects = timeline.get("zoom_effects", [])
        if zoom_effects:
            z_expr = "1.0"
            for zfx in reversed(zoom_effects):
                z_start = round(float(zfx.get("start", 0.0)), 3)
                z_end = round(float(zfx.get("end", z_start + 1.0)), 3)
                mag = 0.15 if zfx.get("type") == "punch" else 0.1
                
                ease = f"min((t-{z_start})/0.3, 1.0)"
                inner = f"(1.0+{mag}*{ease})"
                z_expr = f"if(between(t,{z_start},{z_end}),{inner},{z_expr})"
            
            z_filter = (
                f"crop=w='iw/({z_expr})':h='ih/({z_expr})':x='(iw-iw/({z_expr}))/2':y='(ih-ih/({z_expr}))/2',"
                f"scale=1080:1920:flags=bilinear"
            )
            graph_nodes.append(f"{vid_node}{z_filter}[v_zoom]")
            vid_node = "[v_zoom]"

        # -- STAGE C: Color Grading (Fashion/Cinematic) --
        c_intensity = timeline.get("color_intensity", 1.0)
        grading = f"eq=contrast={1.0+0.1*c_intensity}:saturation={1.0+0.3*c_intensity}:brightness=0.02"
        graph_nodes.append(f"{vid_node}{grading},setsar=1[v_grade]")
        vid_node = "[v_grade]"

        # -- STAGE D: Overlays (Watermark/Price) --
        # Placeholder for overlay logic...
        
        # 3. Construct Command
        cmd = ["ffmpeg", "-y", "-hwaccel", "mediacodec"]
        cmd.extend(inputs)
        
        if graph_nodes:
            cmd.extend(["-filter_complex", ";".join(graph_nodes)])
            # Map the final nodes
            cmd.extend(["-map", vid_node, "-map", "0:a?"])
        else:
            cmd.extend(["-map", "0:v", "-map", "0:a?"])

        # Encoder Settings
        cmd.extend([
            "-c:v", HW_ENCODER,
            "-b:v", "5M", # High bitrate for 1080p
            "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ])

        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            logger.info("✅ Render Successful.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Render Failed: {e.stderr.decode()[-500:]}")
            return False

video_engine = VideoEngine()
