import importlib
import logging

logger = logging.getLogger("deferred")

class DeferredModule:
    """
    Lazy-loader for heavy Python modules.
    Only imports the module when an attribute is accessed.
    Saves RAM and improves startup time on Android.
    """
    def __init__(self, module_path: str):
        self._module_path = module_path
        self._module = None

    def _load(self):
        if self._module is None:
            logger.info(f"⏳ Lazy-loading heavy module: {self._module_path}")
            self._module = importlib.import_module(self._module_path)
        return self._module

    def __getattr__(self, name):
        module = self._load()
        return getattr(module, name)

    def __call__(self, *args, **kwargs):
        module = self._load()
        if hasattr(module, "execute") or callable(module):
            return module(*args, **kwargs)
        raise TypeError(f"Module {self._module_path} is not callable")

def defer(module_path: str):
    return DeferredModule(module_path)
