import logging
import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("pipeline_audit")

@dataclass
class StepRecord:
    name: str
    status: str = "PENDING" # PENDING, SUCCESS, FAILED, RUNNING
    duration: float = 0.0
    error: Optional[str] = None

class StepTracer:
    """Thread-safe background step tracer for Android services."""
    _lock = threading.Lock()
    _steps: Dict[str, StepRecord] = {}
    _start_times: Dict[str, float] = {}

    @classmethod
    def start(cls, name: str):
        with cls._lock:
            cls._steps[name] = StepRecord(name=name, status="RUNNING")
            cls._start_times[name] = time.monotonic()
        logger.info(f"📍 [Audit] START: {name}")

    @classmethod
    def success(cls, name: str):
        with cls._lock:
            if name in cls._steps:
                rec = cls._steps[name]
                rec.status = "SUCCESS"
                rec.duration = round(time.monotonic() - cls._start_times.get(name, time.monotonic()), 2)
        logger.info(f"✅ [Audit] SUCCESS: {name} ({rec.duration}s)")

    @classmethod
    def fail(cls, name: str, error: str):
        with cls._lock:
            if name in cls._steps:
                rec = cls._steps[name]
                rec.status = "FAILED"
                rec.error = error
                rec.duration = round(time.monotonic() - cls._start_times.get(name, time.monotonic()), 2)
        logger.error(f"❌ [Audit] FAILED: {name} -> {error}")

    @classmethod
    def get_report(cls) -> Dict[str, Any]:
        with cls._lock:
            return {
                "steps": {k: vars(v) for k, v in cls._steps.items()},
                "failed_count": len([s for s in cls._steps.values() if s.status == "FAILED"]),
                "total_duration": sum(s.duration for s in cls._steps.values())
            }

class DataAuditor:
    """Validates pipeline integrity and data flow."""
    
    REQUIRED_KEYS = [
        "fused_moments",
        "retention_data",
        "emotional_spikes",
        "master_hook",
        "edited_segments"
    ]

    def audit_session(self, ai_data: Dict) -> Dict:
        """Checks if the session data is healthy."""
        missing = [k for k in self.REQUIRED_KEYS if k not in ai_data or not ai_data[k]]
        
        health = "ACTIVE"
        if len(missing) > 2:
            health = "DEGRADED"
        if "edited_segments" in missing:
            health = "FAILED"

        return {
            "health": health,
            "missing_signals": missing,
            "is_valid": health != "FAILED"
        }

def run_pipeline_audit(ai_data: Dict) -> Dict:
    """Convenience wrapper for a full session audit."""
    auditor = DataAuditor()
    report = auditor.audit_session(ai_data)
    
    # Add step trace to report
    report["trace"] = StepTracer.get_report()
    
    if not report["is_valid"]:
        logger.error(f"🚨 Pipeline Audit Failed: Missing {report['missing_signals']}")
    else:
        logger.info(f"🛡️ Pipeline Health: {report['health']}")
        
    return report
