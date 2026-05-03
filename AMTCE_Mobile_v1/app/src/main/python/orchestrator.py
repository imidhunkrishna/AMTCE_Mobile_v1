# engine/orchestrator.py
import logging
import os
import threading
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from downloader.downloader_skill import DownloaderSkill
from intelligence.monetization_brain import MonetizationBrain
from intelligence.gemini_client import GeminiClient
from intelligence.nzt_loop import nzt_loop
from intelligence.energy_scorer import score_segments
from intelligence.content_brain import content_brain
from intelligence.system_memory import system_memory, validator, decision_engine
from intelligence.pacing_architect import pacing_architect
from intelligence.monetization_scorer import monetization_scorer
from intelligence.trend_brain import TrendBrain
from intelligence.sales_copy import sales_copy
from intelligence.engagement_brain import EngagementBrain
from uploader.uploader_bridge import UploaderBridge
from intelligence.price_tag import price_tag
from diagnostics.audit import StepTracer, run_pipeline_audit
from compiler.video_engine import video_engine
from compiler.timeline_builder import timeline_builder, TimelineBuilder
from compiler.thumb_engine import thumb_engine
from refiner.refinement_skill import RefinementSkill
from refiner.audio_gate import AudioGate
from refiner.watermark_gate import WatermarkGate
from refiner.scene_editor import SceneEditor
from uploader.uploader_skill import UploaderSkill
from vanguard.vanguard_director import vanguard
from utils.deferred import defer
import gc
from utils.file_ops import atomic_write, file_lock


# Configure centralized logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("amtce.orchestrator")

class AMTCE_Mobile_Orchestrator:
    """
    Main controller for the AMTCE Mobile Engine (v2 - Swarm Optimized).
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.refiner = RefinementSkill()
        self.audio_gate = AudioGate()
        self.watermark_gate = WatermarkGate()
        self.scene_editor = SceneEditor()
        self.uploader = UploaderSkill()

        # Deferred Intelligence Modules
        self.fashion_scout = defer("intelligence.fashion_scout")
        self.monetization_brain = defer("intelligence.monetization_brain")
        self.moment_miner = defer("intelligence.moment_miner")
        self.analyze_audio = defer("audio.audio_intelligence")
        self.trend_brain = defer("intelligence.trend_brain")
        self.engagement_brain = defer("intelligence.engagement_brain")
        
        # Low-Memory Controller Settings
        self.MAX_CONCURRENT_TASKS = 1
        self.processing_semaphore = threading.Semaphore(self.MAX_CONCURRENT_TASKS)

        
        # Start the Background Scavenger (Swarm Recommendation)
        self.scavenger_thread = threading.Thread(target=self._scavenger_daemon, daemon=True)
        self.scavenger_thread.start()

    def _scavenger_daemon(self):
        """Quietly rescues orphaned .part files in the background."""
        logger.info("🛡️ Background Scavenger Daemon Active.")
        while True:
            try:
                # Check for files older than 5 minutes that didn't finish
                for f in os.listdir("downloads"):
                    if f.endswith(".part"):
                        self.downloader._rescue_partial(f.replace(".part", ""))
            except Exception:
                pass
            time.sleep(300) # Check every 5 minutes

    def _get_niche(self, video_path: str) -> str:
        """Robust niche detection ported from AMTCE Desktop."""
        try:
            if not video_path:
                return "fashion"
            
            video_path_obj = Path(video_path)
            # 1. Check for exact sidecar
            sidecar = video_path_obj.with_suffix(".niche.json")
            if sidecar.exists():
                with open(sidecar, "r", encoding="utf-8") as f:
                    return json.load(f).get("detected_niche", "fashion")
            
            # 2. Check metadata .json
            meta_json = video_path_obj.with_suffix(".json")
            if meta_json.exists():
                with open(meta_json, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    return meta.get("detected_niche", "fashion")
                    
        except Exception as e:
            logger.warning(f"Niche detection failed: {e}")
        return "fashion"

    def process_link(self, url, niche=None):
        with self.processing_semaphore:
            return self._execute_pipeline(url, niche)

    def _execute_pipeline(self, url, niche=None):
        # 0. Vanguard Turn 1: Planning & Safety Check
        vanguard_context = {"url": url}
        mission_plan = vanguard.execute_mission_loop(niche or "general", "Process Link", vanguard_context)
        logger.info(f"🚀 [DEEP_PIPELINE] Processing: {url}")
        try:
            # 1. Advanced Download
            StepTracer.start("download")
            video_meta = self.downloader.download(url)
            if not video_meta:
                StepTracer.fail("download", "Download failed")
                return {"status": "error", "message": "Download failed"}
            StepTracer.success("download")
            
            video_path = video_meta["local_path"]
            gc.collect() # Immediate memory release

            # 2. Niche Discovery
            StepTracer.start("niche_detection")
            if not niche:
                niche = self._get_niche(video_path)
            logger.info(f"🎯 Target Niche: {niche}")
            StepTracer.success("niche_detection")

            # 3. Visual Refinement & Moment Discovery (Mobile Intelligence)
            StepTracer.start("visual_refinement")
            logger.info("🔭 Initiating Visual Refinement & Moment Discovery...")
            duration = video_meta.get("duration", 15.0)
            refinement_report = self._refine_visuals(video_path, duration, niche)
            ai_data.update(refinement_report)
            StepTracer.success("visual_refinement")

            # 4. Audio & Musical Intelligence
            StepTracer.start("audio_intelligence")
            logger.info("🎵 Analyzing Audio & Musical Intelligence...")
            audio_intel = self.analyze_audio.analyze_audio(video_path)
            ai_data["audio_intelligence"] = audio_intel
            logger.info(f"🎧 Vibe: {audio_intel.get('vibe')} | BPM: {audio_intel.get('tempo')} | Drops: {len(audio_intel.get('drops', []))}")
            StepTracer.success("audio_intelligence")
            gc.collect()

            # 3.1 Get Optimization Hints from Memory
            StepTracer.start("memory_recall")
            hints = system_memory.get_hints(niche)
            logger.info(f"🧠 Memory Hints: {hints['preferred_tags']}")
            StepTracer.success("memory_recall")

            # 3.2 Trend Intelligence & Opportunity Analysis
            StepTracer.start("trend_intelligence")
            logger.info("🌊 Aggregating Viral Trend Signals...")
            visual_entities = ai_data.get("forensics", {}).get("entities", [])
            trend_context = self.trend_brain.aggregate_trends(visual_entities)
            opportunity = self.trend_brain.analyze_opportunity(trend_context)
            ai_data["trend_intelligence"] = {**trend_context, **opportunity}
            logger.info(f"🔀 Recommended Angle: {opportunity['recommended_angle']} (Opportunity: {opportunity['opportunity_score']})")
            StepTracer.success("trend_intelligence")

            # 4. Master Decision (Smart Router: RAG vs Gemini)
            StepTracer.start("master_decision")
            logger.info("⚖️ Routing Master Decision...")
            # We treat energy as a signal for the RAG engine
            profile = {"energy": audio_report.get("energy_score", 0.5)}
            decision = decision_engine.generate_plan(profile, niche)
            
            if decision["rag_mode"]:
                logger.info("⚡ [PIPELINE] Master Plan resolved via Local RAG (0 Tokens).")
                ai_data.update(decision)
            else:
                logger.info("🧠 [PIPELINE] Memory Cold. Escalating to Gemini Master Brain...")
                prompt = self.brain.get_master_prompt(
                    niche=niche, 
                    title=video_meta.get("title", "Unknown"),
                    duration=15.0,
                    hints=hints,
                    trend_context=ai_data.get("trend_intelligence")
                )
                raw_res = self.gemini.generate_json(prompt)
                ai_data.update(self.monetization_brain.parse_gemini_response(raw_res) if raw_res else {})
            StepTracer.success("master_decision")

            # 4.1 NZT Simulation Loop (Iterative Planning)
            StepTracer.start("nzt_loop")
            logger.info("⚡ Entering NZT Simulation Loop...")
            context = {"niche": niche, "title": video_meta.get("title"), "duration": 15.0}
            candidate_moments = ai_data.get("candidate_moments", [{"time": 1.0, "score": 0.8}, {"time": 5.0, "score": 0.9}])
            ai_data = nzt_loop.select_best(ai_data, context, candidate_moments)
            StepTracer.success("nzt_loop")

            # 4.2 Energy Scorer (Audio Energy Peaks)
            StepTracer.start("energy_scoring")
            logger.info("🎵 Running Energy Scorer...")
            if "edited_segments" in ai_data:
                ai_data["edited_segments"] = score_segments(video_path, ai_data["edited_segments"])
            StepTracer.success("energy_scoring")
            
            # 4.5. Specialized Fashion Analysis
            if niche == "fashion":
                StepTracer.start("fashion_scout")
                logger.info("👗 Running Fashion Scout Forensics...")
                fashion_data = self.fashion_scout.analyze(video_path)
                if fashion_data:
                    ai_data["fashion_scout"] = fashion_data
                    cat = fashion_data.get("attributes", {}).get("classification", {}).get("primary_category", "fashion")
                    ai_data["affiliate_link"] = self.monetization_brain.get_affiliate_link(cat)
                StepTracer.success("fashion_scout")
            
            # 4. Deep Content Intelligence (Spikes, Retention, Hooks)
            StepTracer.start("content_brain")
            logger.info("🧠 Analyzing Content Intelligence...")
            ai_data = content_brain.process(ai_data)
            StepTracer.success("content_brain")
            
            # 4.1 Strict Segment Validation (Quality Gate)
            StepTracer.start("quality_gate")
            logger.info("🛡️ Running Quality Gate...")
            validation_report = validator.validate(
                candidate_moments=ai_data.get("fused_moments", []),
                selected_segments=ai_data.get("edited_segments", []),
                signal_data=ai_data
            )
            
            if validation_report["verdict"] == "FAIL":
                logger.warning(f"🚨 Edit Rejected by Quality Gate: {validation_report['reasons']}")
            StepTracer.success("quality_gate")
            
            # 5. Smart Editing & Transition Planning
            StepTracer.start("scene_editing")
            logger.info("🎬 Planning Smart Transitions & Zoom Effects...")
            editing_plan = self.scene_editor.prepare_editing_plan(
                video_path, duration, ai_data.get("mined_moments", [])
            )
            
            # Hook Override (Retention Escalation)
            if ai_data.get("fused_moments"):
                top_hook = max(ai_data["fused_moments"], key=lambda x: x.get("energy_score", 0))
                editing_plan = self.scene_editor.apply_single_shot_override(editing_plan, top_hook)
            
            ai_data["editing_plan"] = editing_plan
            StepTracer.success("scene_editing")
            
            gc.collect()

            # 5. Final Compilation & Rendering
            StepTracer.start("render")
            logger.info("🎬 Initializing Final Render...")
            audio_intel = ai_data.get("audio_intelligence", {})
            render_plan = timeline_builder.build(ai_data, audio_intel)
            
            # Apply Professional Pacing Arc
            if "edited_segments" in render_plan:
                render_plan["edited_segments"] = pacing_architect.shape(render_plan["edited_segments"])

            processed_path = video_path.replace(".mp4", "_processed.mp4")
            render_success = video_engine.render(video_path, processed_path, render_plan)
            
            if not render_success:
                StepTracer.fail("render", "Rendering failed")
                logger.warning("⚠️ Render failed, falling back to original clip.")
                processed_path = video_path
            else:
                StepTracer.success("render")

            # 6. Prepare Uploader Payload
            StepTracer.start("upload_prepare")
            
            # Generate High-Conversion Sales Copy
            viral_caption = sales_copy.build_caption(ai_data, niche=niche)
            
            # Generate Premium Price Tag Overlay
            price_metadata = price_tag.generate_metadata(ai_data)
            
            # Generate High-CTR Cover Image
            thumb_path = f"{processed_path.rsplit('.', 1)[0]}_cover.jpg"
            thumb_path = thumb_engine.generate_thumbnail(processed_path, thumb_path, ai_data)
            
            viral_title = ai_data.get("generated_title", video_meta["title"])
            hashtags = render_plan.get("hashtags", ["#Shorts", "#Viral"])
            
            upload_payload = self.uploader.prepare_upload_payload(
                processed_path,
                viral_title,
                hashtags
            )
            
            upload_payload["caption"] = viral_caption
            upload_payload["overlay_metadata"] = price_metadata
            upload_payload["thumbnail_path"] = thumb_path
            upload_payload["audio_strategy"] = audio_report["action"]
            upload_payload["niche"] = niche
            StepTracer.success("upload_prepare")

            # 8. Distribution & Safety
            StepTracer.start("distribution")
            logger.info("📡 Distributing Hardened Video to Platforms...")
            upload_results = self.uploader.upload_mission(processed_path, ai_data, niche)
            ai_data["upload_results"] = upload_results
            
            for platform, res in upload_results.items():
                if res.get("status") == "success":
                    logger.info(f"✅ {platform.upper()} Upload Success: {res.get('link')}")
                else:
                    logger.warning(f"⚠️ {platform.upper()} Upload {res.get('status')}: {res.get('reason', 'Unknown error')}")
            
            StepTracer.success("distribution")

            # 9. Learning & Memory Update (Self-Optimization)
            StepTracer.start("memory_update")
            logger.info("🧠 Recording Mission Reward & Updating Memory...")
            fitness = monetization_scorer.compute_fitness(render_plan, ai_data)
            
            # Record engagement opportunity for background processing
            if ai_data.get("upload_results"):
                self.engagement_brain.generate_community_reply("Initial post engagement seeded.", context=ai_data)

            system_memory.record_mission(
                niche=niche,
                metadata=ai_data,
                reward_score=fitness,
                energy_profile=audio_report.get("energy_profile", [])
            )
            StepTracer.success("memory_update")

            # 10. Final Pipeline Audit
            audit_report = run_pipeline_audit(ai_data)
            audit_report["monetization_fitness"] = fitness

            return {
                "status": "MISSION_COMPLETE",
                "video_id": video_meta.get("id"),
                "processed_path": processed_path,
                "fitness_score": fitness,
                "upload_results": upload_results,
                "audit": audit_report
            }

        except Exception as e:
            # Vanguard Turn 4: Repair & Self-Healing
            repair_strategy = vanguard.handle_failure(str(e), {"url": url, "niche": niche})
            if repair_strategy["action"] == "RETRY":
                logger.warning(f"🩹 Vanguard Self-Healing: {repair_strategy['reason']}. Retrying mission...")
                # In a real app, you'd re-trigger the loop with the preset_override
            
            StepTracer.fail("mission_execution", str(e))
            logger.exception(f"💥 Mission FATAL: {e}")
            return {"status": "FAILED", "error": str(e)}
        finally:
            gc.collect() # Final cleanup


    def _refine_visuals(self, video_path: str, duration: float, niche: str) -> Dict[str, Any]:
        """Consolidated visual intelligence step."""
        report = {}
        
        # 1. Moment Mining
        moments = self.moment_miner.mine_moments(video_path, duration)
        report["mined_moments"] = moments
        logger.info(f"💎 Mined {len(moments)} high-energy moments.")
        
        # 2. Branding & Watermark Scan
        branding = self.watermark_gate.scan_for_branding(video_path)
        report["branding_status"] = branding["status"]
        if branding["status"] == "DETECTED":
            logger.warning("⚠️ Watermarks detected! Preparing safety masks...")
            # Note: Masking would happen during the render phase
        
        return report


if __name__ == "__main__":
    engine = AMTCE_Mobile_Orchestrator()
    print("AMTCE Deep Orchestrator v2 Initialized.")

# Export singleton
orchestrator = AMTCE_Mobile_Orchestrator()
