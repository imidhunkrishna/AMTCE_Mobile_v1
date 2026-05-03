# engine/downloader/downloader_skill.py
import os
import sqlite3
import re
import json
import time
import hashlib
import logging
import threading
import glob
from datetime import datetime
from typing import Dict, Optional, Tuple
import yt_dlp

logger = logging.getLogger("amtce.downloader")

# ---------------------------------------------------------------------------
# SQLite3 Index Layer (Swarm Optimized for Mobile)
# ---------------------------------------------------------------------------

class DownloadIndexDB:
    """Atomic, Persistent SQLite index for O(1) duplicate detection."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    path TEXT,
                    content_hash TEXT,
                    platform TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON downloads (content_hash)")

    def register(self, meta: Dict):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO downloads (id, url, title, path, content_hash, platform)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(meta.get("id")),
                    meta.get("url"),
                    meta.get("title"),
                    meta.get("local_path"),
                    meta.get("content_hash"),
                    meta.get("platform")
                ))
        except Exception as e:
            logger.error(f"Failed to register in SQLite: {e}")

    def find_by_id(self, url_id: str) -> Optional[str]:
        if not url_id: return None
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT path FROM downloads WHERE id = ?", (str(url_id),))
                row = cursor.fetchone()
                if row and os.path.exists(row[0]):
                    return row[0]
        except Exception:
            pass
        return None

# ---------------------------------------------------------------------------
# Heavy-Duty Downloader Skill (v2 - Swarm Enhanced)
# ---------------------------------------------------------------------------

class DownloaderSkill:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        self.db = DownloadIndexDB(os.path.join(self.download_dir, "amtce_index.db"))
        self.cookies_file = os.getenv("COOKIES_FILE", "cookies.txt")

    def _get_auth_strategies(self):
        return [
            ("no_auth", {}),
            ("cookies_file", {"cookiefile": self.cookies_file} if os.path.exists(self.cookies_file) else None),
            ("browser_chrome", {"cookiesfrombrowser": ("chrome",)}),
            ("browser_firefox", {"cookiesfrombrowser": ("firefox",)})
        ]

    def download(self, url: str) -> Optional[Dict]:
        url_id = self._extract_url_id(url)
        
        # 1. SQL Cache Check (Atomic)
        existing = self.db.find_by_id(url_id)
        if existing:
            logger.info(f"♻️  SQL Index Hit: {existing}")
            return self._load_meta(existing)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_base = f"dl_{timestamp}_{url_id or 'unknown'}"
        temp_tmpl = os.path.join(self.download_dir, f"{temp_base}.%(ext)s")

        base_opts = {
            "outtmpl": temp_tmpl,
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
        }

        success = False
        downloaded_path = None
        info_dict = {}

        # 2. Multi-Strategy Auth Loop
        for strategy, extra_opts in self._get_auth_strategies():
            if extra_opts is None: continue
            logger.info(f"🎯 Strategy Attempt: {strategy}")
            opts = {**base_opts, **extra_opts}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        info_dict = info
                        candidates = glob.glob(os.path.join(self.download_dir, f"{temp_base}.*"))
                        candidates = [c for c in candidates if not c.endswith((".part", ".ytdl", ".json"))]
                        if candidates:
                            downloaded_path = candidates[0]
                            success = True
                            break
            except Exception as e:
                logger.warning(f"🚨 Strategy {strategy} failed: {e}")

        # 3. Partial-File Rescue (Optimized for Mobile)
        if not success:
            downloaded_path = self._rescue_partial(temp_base)
            if downloaded_path:
                success = True

        if not success or not downloaded_path:
            return None

        # 4. Commit to DB
        content_hash = self.get_file_hash(downloaded_path)
        meta = {
            "id": url_id or info_dict.get("id"),
            "url": url,
            "title": info_dict.get("title", "Unknown Video"),
            "content_hash": content_hash,
            "local_path": downloaded_path,
            "platform": info_dict.get("extractor_key")
        }
        self.db.register(meta)
        return meta

    def _rescue_partial(self, temp_base: str) -> Optional[str]:
        """Attempts to recover a file if yt-dlp was killed mid-process."""
        parts = glob.glob(os.path.join(self.download_dir, f"{temp_base}.*.part"))
        if not parts: return None
        
        part_file = parts[0]
        rescued = part_file.replace(".part", "")
        logger.info(f"🚑 Attempting File Rescue: {os.path.basename(part_file)}")
        
        for i in range(5):
            try:
                os.rename(part_file, rescued)
                logger.info(f"✅ Rescue Success on attempt {i+1}")
                return rescued
            except Exception:
                time.sleep(1)
        return None

    def _extract_url_id(self, url: str) -> str:
        m = re.search(r"/(?:reel|p|video)/([A-Za-z0-9_-]+)", url)
        return m.group(1) if m else hashlib.md5(url.encode()).hexdigest()[:10]

    def _load_meta(self, video_path: str) -> Dict:
        # Use DB instead of sidecar JSON for speed
        with sqlite3.connect(os.path.join(self.download_dir, "amtce_index.db")) as conn:
            cursor = conn.execute("SELECT * FROM downloads WHERE path = ?", (video_path,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "url": row[1], "title": row[2], "local_path": row[3], "content_hash": row[4]}
        return {"local_path": video_path, "id": "unknown"}

    @staticmethod
    def get_file_hash(path):
        sha1 = hashlib.sha1()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha1.update(chunk)
        return sha1.hexdigest()[:10]
