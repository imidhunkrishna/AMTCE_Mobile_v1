import logging
from .metadata_generator import ViralMetadataGenerator

logger = logging.getLogger("amtce.refiner")

class RefinementSkill:
    """Modular skill for video analysis and refinement instructions."""

    def __init__(self):
        self.metadata_gen = ViralMetadataGenerator()
        self.pacing_config = {
            "min_spacing": 0.8,
            "max_gap": 2.5
        }

    def analyze_pacing(self, raw_cuts, duration):
        """
        Human-style pacing: ensures edits are neither too fast nor too slow.
        Ported from smart_scene_editor.py.
        """
        if not raw_cuts:
            return []

        # Step 1: Remove cuts that are too close (prevent flickering)
        stabilized = []
        last_cut = 0.0
        for c in sorted(raw_cuts):
            if c - last_cut >= self.pacing_config["min_spacing"]:
                stabilized.append(c)
                last_cut = c

        # Step 2: Fill gaps that are too long (maintain engagement)
        final_cuts = list(stabilized)
        all_points = [0.0] + final_cuts + [duration]
        
        for i in range(1, len(all_points)):
            start = all_points[i-1]
            end = all_points[i]
            gap = end - start
            if gap > self.pacing_config["max_gap"]:
                # Inject a cut in the middle
                final_cuts.append(round(start + (gap / 2.0), 2))

        return sorted(final_cuts)

    def generate_ffmpeg_filters(self, analysis):
        """
        Converts analysis data into FFmpeg filter strings.
        This is the "Android Secret Sauce": offloading AI logic to the GPU.
        """
        filters = []
        
        # Example: Zoom Logic
        for effect in analysis.get("effects", []):
            if effect["type"] == "zoom_in":
                # Logic to create an FFmpeg zoompan filter
                filters.append(f"zoompan=z='min(zoom+0.001,1.5)':d=25:s=720x1280")
        
        # Example: Watermark Overlay (Manual Patch)
        for box in analysis.get("watermarks", []):
            # Logic to blur or overlay the watermark region
            x, y, w, h = box['x'], box['y'], box['w'], box['h']
            filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}")

        return ",".join(filters)

    def create_edit_plan(self, video_meta, ai_hints):
        """
        Synthesizes AI hints (from Gemini) with human-style pacing rules.
        """
        duration = video_meta.get("duration", 0)
        raw_cuts = ai_hints.get("suggested_cuts", [])
        
        refined_cuts = self.analyze_pacing(raw_cuts, duration)
        
        # New Deep Extraction: Viral Metadata
        viral_meta = self.metadata_gen.generate(
            video_meta.get("title", "Video"),
            visual_context=ai_hints.get("visual_context", "")
        )
        
        plan = {
            "video_id": video_meta.get("id"),
            "cuts": refined_cuts,
            "filter_script": self.generate_ffmpeg_filters(ai_hints),
            "output_name": f"refined_{video_meta.get('id')}.mp4",
            "viral_metadata": viral_meta
        }
        
        logger.info(f"✨ Refinement Plan Created for {video_meta.get('id')}")
        return plan
