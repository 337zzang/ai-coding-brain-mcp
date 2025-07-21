"""
Session Manager for Flow Project v2
Handles session persistence, restoration, and conflict resolution
"""

import json
import os
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import threading
import time


class SessionManager:
    """Manages session saving, restoration, and auto-save functionality"""

    def __init__(self, context_manager, auto_save_interval: int = 300):
        """
        Initialize SessionManager

        Args:
            context_manager: ContextManager instance
            auto_save_interval: Auto-save interval in seconds (default: 5 minutes)
        """
        self.context_manager = context_manager
        self.auto_save_interval = auto_save_interval
        self.sessions_dir = Path(context_manager.data_dir) / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)

        self._auto_save_thread = None
        self._stop_auto_save = threading.Event()
        self._save_lock = threading.Lock()

    def start_auto_save(self):
        """Start auto-save thread"""
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            return

        self._stop_auto_save.clear()
        self._auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
        self._auto_save_thread.start()
        print(f"Auto-save started (interval: {self.auto_save_interval}s)")

    def stop_auto_save(self):
        """Stop auto-save thread"""
        self._stop_auto_save.set()
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=5)
        print("Auto-save stopped")

    def _auto_save_worker(self):
        """Worker thread for auto-saving"""
        while not self._stop_auto_save.is_set():
            # Wait for interval or stop signal
            if self._stop_auto_save.wait(self.auto_save_interval):
                break

            # Perform auto-save
            try:
                self.save_session("auto")
            except Exception as e:
                print(f"Auto-save error: {e}")

    def save_session(self, save_type: str = "manual") -> Optional[str]:
        """
        Save current session

        Args:
            save_type: Type of save ("manual", "auto", "checkpoint")

        Returns:
            Path to saved session file or None if failed
        """
        with self._save_lock:
            try:
                session_data = {
                    "save_type": save_type,
                    "saved_at": datetime.now().isoformat(),
                    "context": self.context_manager.context,
                    "metadata": {
                        "context_version": self.context_manager.context["metadata"]["context_version"],
                        "session_duration": self._calculate_session_duration()
                    }
                }

                # Generate filename
                session_id = self.context_manager.context["session"]["session_id"]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"session_{session_id[:8]}_{timestamp}_{save_type}.json"

                # Save uncompressed first
                temp_path = self.sessions_dir / f"temp_{filename}"
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)

                # Compress if manual or checkpoint
                if save_type in ["manual", "checkpoint"]:
                    compressed_path = self.sessions_dir / f"{filename}.gz"
                    with open(temp_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove temp file
                    temp_path.unlink()
                    saved_path = compressed_path
                else:
                    # For auto-saves, just rename
                    saved_path = self.sessions_dir / filename
                    temp_path.rename(saved_path)

                # Clean up old auto-saves
                if save_type == "auto":
                    self._cleanup_old_autosaves()

                return str(saved_path)

            except Exception as e:
                print(f"Failed to save session: {e}")
                return None

    def restore_session(self, session_file: Optional[str] = None) -> bool:
        """
        Restore a session

        Args:
            session_file: Path to session file (latest if None)

        Returns:
            True if restored successfully
        """
        try:
            if session_file is None:
                # Find latest session
                session_file = self._find_latest_session()
                if not session_file:
                    print("No session files found")
                    return False

            session_path = Path(session_file)

            # Check if compressed
            if session_path.suffix == '.gz':
                with gzip.open(session_path, 'rt', encoding='utf-8') as f:
                    session_data = json.load(f)
            else:
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

            # Validate version compatibility
            saved_version = session_data["metadata"]["context_version"]
            current_version = self.context_manager.context["metadata"]["context_version"]

            if saved_version != current_version:
                print(f"Warning: Version mismatch (saved: {saved_version}, current: {current_version})")
                # Could implement migration logic here

            # Restore context
            self.context_manager.context = session_data["context"]
            self.context_manager.save()

            print(f"Session restored from: {session_path.name}")
            print(f"  Session ID: {session_data['context']['session']['session_id'][:8]}")
            print(f"  Saved at: {session_data['saved_at']}")
            print(f"  Type: {session_data['save_type']}")

            return True

        except Exception as e:
            print(f"Failed to restore session: {e}")
            return False

    def list_sessions(self, limit: int = 10) -> List[Dict[str, str]]:
        """List available sessions"""
        sessions = []

        for file_path in sorted(self.sessions_dir.glob("session_*.json*"), reverse=True):
            try:
                # Extract info from filename
                parts = file_path.stem.split('_')
                if len(parts) >= 4:
                    session_info = {
                        "file": str(file_path),
                        "session_id": parts[1],
                        "timestamp": f"{parts[2]}_{parts[3]}",
                        "type": parts[4] if len(parts) > 4 else "unknown",
                        "compressed": file_path.suffix == '.gz',
                        "size": file_path.stat().st_size
                    }
                    sessions.append(session_info)

                    if len(sessions) >= limit:
                        break

            except Exception:
                continue

        return sessions

    def create_checkpoint(self, name: str = "") -> Optional[str]:
        """Create a named checkpoint"""
        # Save current state
        checkpoint_path = self.save_session("checkpoint")

        if checkpoint_path and name:
            # Rename to include checkpoint name
            old_path = Path(checkpoint_path)
            new_name = old_path.stem.replace("checkpoint", f"checkpoint_{name}")
            new_path = old_path.parent / f"{new_name}{old_path.suffix}"
            old_path.rename(new_path)
            checkpoint_path = str(new_path)

        if checkpoint_path:
            print(f"Checkpoint created: {Path(checkpoint_path).name}")

        return checkpoint_path

    def _calculate_session_duration(self) -> int:
        """Calculate session duration in seconds"""
        try:
            started = datetime.fromisoformat(self.context_manager.context["session"]["started_at"])
            duration = (datetime.now() - started).total_seconds()
            return int(duration)
        except Exception:
            return 0

    def _find_latest_session(self) -> Optional[str]:
        """Find the most recent session file"""
        sessions = self.list_sessions(limit=1)
        return sessions[0]["file"] if sessions else None

    def _cleanup_old_autosaves(self, keep_count: int = 3):
        """Clean up old auto-save files, keeping only the most recent ones"""
        auto_saves = []

        for file_path in self.sessions_dir.glob("session_*_auto.json"):
            auto_saves.append((file_path, file_path.stat().st_mtime))

        # Sort by modification time (newest first)
        auto_saves.sort(key=lambda x: x[1], reverse=True)

        # Remove old auto-saves
        for file_path, _ in auto_saves[keep_count:]:
            try:
                file_path.unlink()
                print(f"Cleaned up old auto-save: {file_path.name}")
            except Exception:
                pass

    def merge_sessions(self, session1_file: str, session2_file: str) -> bool:
        """
        Merge two sessions (advanced feature)
        Useful when recovering from crashes or combining work
        """
        # This is a placeholder for advanced merge functionality
        # Would need careful conflict resolution logic
        print("Session merge not yet implemented")
        return False
