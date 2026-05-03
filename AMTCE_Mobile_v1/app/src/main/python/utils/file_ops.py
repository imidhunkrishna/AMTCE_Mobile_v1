# engine/utils/file_ops.py
import os
import json
import logging
import threading
import tempfile
import time
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger("amtce.utils")

# Locking Mechanisms
file_locks = {}
fl_lock = threading.Lock()

@contextmanager
def file_lock(path_str, timeout=5):
    """
    Simple in-process file/path locking to prevent split-brain issues.
    """
    path_str = str(path_str)
    with fl_lock:
        if path_str not in file_locks:
            file_locks[path_str] = threading.Lock()
        lock = file_locks[path_str]

    acquired = lock.acquire(timeout=timeout)
    try:
        if not acquired:
            logger.warning(f"🔒 Could not acquire lock for {path_str} in {timeout}s.")
        yield acquired
    finally:
        if acquired:
            lock.release()

def atomic_write(target_path, content, mode="w", encoding="utf-8"):
    """
    Atomic write using tempfile and os.replace.
    Ensures data integrity during app crashes or OS process kills.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=target_path.parent, prefix=".tmp_")
    try:
        with os.fdopen(fd, mode, encoding=encoding) as f:
            f.write(content)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass 

        # Atomic Rename
        os.replace(temp_path, target_path)
        return True
    except Exception as e:
        logger.error(f"❌ Atomic write failed for {target_path}: {e}")
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass
        return False
