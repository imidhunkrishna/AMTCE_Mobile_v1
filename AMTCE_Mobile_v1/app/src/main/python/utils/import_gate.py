import sys
import logging
import importlib
import os

logger = logging.getLogger("import_gate")

class ImportGate:
    """
    Mobile Safety Gate for Heavy Python Imports.
    Prevents Android OOM (Out of Memory) by blocking heavy modules on low-end devices.
    """
    _loaded_modules = {}
    
    # Modules that consume significant RAM on Android
    HEAVY_REGISTRY = {
        "cv2": "OpenCV (Visual Forensics)",
        "numpy": "NumPy (Mathematical Intelligence)",
        "pandas": "Pandas (Data Analytics)",
        "librosa": "Librosa (Audio Analysis)"
    }

    @staticmethod
    def get(module_name: str, fallback_action: str = "warn"):
        """
        Safely imports a module. 
        Returns module object if allowed/successful, else None.
        """
        if module_name in ImportGate._loaded_modules:
            return ImportGate._loaded_modules[module_name]

        # 1. Check System Specs (Simplified for Mobile)
        # On Android, we check for a custom flag or just memory pressure
        is_low_mem = os.environ.get("AMTCE_LOW_MEM_MODE", "false").lower() == "true"
        
        # 2. Enforce Block for Heavy Modules in Low Mem Mode
        if module_name in ImportGate.HEAVY_REGISTRY and is_low_mem:
            logger.warning(f"🚫 [ImportGate] BLOCKING {module_name} ({ImportGate.HEAVY_REGISTRY[module_name]}) due to Low-Mem Mode.")
            return None

        # 3. Attempt Dynamic Import
        try:
            # We use import_module to avoid top-level import crashes
            mod = importlib.import_module(module_name)
            ImportGate._loaded_modules[module_name] = mod
            logger.info(f"⚡ [ImportGate] Loaded: {module_name}")
            return mod
        except ImportError:
            if fallback_action == "warn":
                logger.warning(f"⚠️ [ImportGate] Module {module_name} not available in this environment.")
            return None
        except Exception as e:
            logger.error(f"❌ [ImportGate] Critical failure importing {module_name}: {e}")
            return None

    @staticmethod
    def is_available(module_name: str) -> bool:
        """Lightweight check without triggering import."""
        return importlib.util.find_spec(module_name) is not None

def safe_import(module_name: str):
    """Convenience alias."""
    return ImportGate.get(module_name)
