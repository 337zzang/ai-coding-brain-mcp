"""
Log Management System for AI Coding Brain MCP

This module provides log rotation and management capabilities including:
- File size based rotation
- Time based retention
- Total size limits
- Automatic cleanup
"""

import os
import time
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class LogRotationPolicy:
    """Log rotation policy configuration"""
    max_file_size_mb: float = 10.0  # Maximum size per log file in MB
    max_total_size_mb: float = 100.0  # Maximum total size for all logs in MB
    retention_days: int = 30  # How long to keep old logs
    max_files: int = 10  # Maximum number of log files to keep
    auto_cleanup_interval_hours: float = 24.0  # How often to run cleanup

    def should_rotate_by_size(self, file_path: str) -> bool:
        """Check if file should be rotated based on size"""
        if not os.path.exists(file_path):
            return False

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return size_mb >= self.max_file_size_mb

    def should_delete_by_age(self, file_path: str) -> bool:
        """Check if file should be deleted based on age"""
        if not os.path.exists(file_path):
            return False

        file_time = os.path.getmtime(file_path)
        file_age = time.time() - file_time
        max_age_seconds = self.retention_days * 24 * 60 * 60

        return file_age > max_age_seconds

    def to_dict(self) -> dict:
        """Convert policy to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'LogRotationPolicy':
        """Create policy from dictionary"""
        return cls(**data)


class LogManager:
    """Manages log files with rotation and cleanup"""

    def __init__(self, log_dir: str = "logs", policy: Optional[LogRotationPolicy] = None):
        self.log_dir = Path(log_dir)
        self.policy = policy or LogRotationPolicy()
        self.config_file = self.log_dir / "log_manager_config.json"
        self.last_cleanup_file = self.log_dir / ".last_cleanup"

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Load or save configuration
        self._load_or_create_config()

        # Initialize logger
        self.logger = logging.getLogger(__name__)

    def _load_or_create_config(self):
        """Load existing config or create new one"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.policy = LogRotationPolicy.from_dict(config_data.get('policy', {}))
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")
        else:
            self.save_config()

    def save_config(self):
        """Save current configuration"""
        config_data = {
            'policy': self.policy.to_dict(),
            'last_updated': datetime.now().isoformat()
        }

        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    def get_log_files(self) -> List[Path]:
        """Get all log files in the directory"""
        return sorted(self.log_dir.glob("*.log"))

    def get_statistics(self) -> Dict:
        """Get statistics about log files"""
        log_files = self.get_log_files()

        total_size = 0
        oldest_file = None
        newest_file = None

        for file in log_files:
            size = file.stat().st_size
            total_size += size

            mtime = file.stat().st_mtime
            if oldest_file is None or mtime < oldest_file[1]:
                oldest_file = (file, mtime)
            if newest_file is None or mtime > newest_file[1]:
                newest_file = (file, mtime)

        return {
            'total_files': len(log_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_file': oldest_file[0].name if oldest_file else None,
            'oldest_file_age_days': round((time.time() - oldest_file[1]) / (24 * 60 * 60), 1) if oldest_file else None,
            'newest_file': newest_file[0].name if newest_file else None,
            'policy': self.policy.to_dict()
        }

    def rotate_file(self, file_path: str) -> Optional[str]:
        """Rotate a log file by renaming it with timestamp"""
        source = Path(file_path)
        if not source.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = source.stem
        suffix = source.suffix

        rotated_name = f"{stem}_{timestamp}{suffix}"
        rotated_path = source.parent / rotated_name

        try:
            source.rename(rotated_path)
            self.logger.info(f"Rotated {source.name} to {rotated_name}")
            return str(rotated_path)
        except Exception as e:
            self.logger.error(f"Failed to rotate {source.name}: {e}")
            return None

    def cleanup_old_files(self) -> Tuple[int, float]:
        """Remove old files based on retention policy
        Returns: (files_deleted, space_freed_mb)
        """
        files_deleted = 0
        space_freed = 0

        log_files = self.get_log_files()

        # Check retention days
        for file in log_files:
            if self.policy.should_delete_by_age(str(file)):
                size = file.stat().st_size
                try:
                    file.unlink()
                    files_deleted += 1
                    space_freed += size
                    self.logger.info(f"Deleted old file: {file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to delete {file.name}: {e}")

        # Check max files
        if len(log_files) > self.policy.max_files:
            # Sort by modification time and delete oldest
            sorted_files = sorted(log_files, key=lambda f: f.stat().st_mtime)
            files_to_delete = len(log_files) - self.policy.max_files

            for file in sorted_files[:files_to_delete]:
                size = file.stat().st_size
                try:
                    file.unlink()
                    files_deleted += 1
                    space_freed += size
                    self.logger.info(f"Deleted excess file: {file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to delete {file.name}: {e}")

        # Check total size limit
        stats = self.get_statistics()
        if stats['total_size_mb'] > self.policy.max_total_size_mb:
            # Delete oldest files until under limit
            sorted_files = sorted(self.get_log_files(), key=lambda f: f.stat().st_mtime)

            for file in sorted_files:
                if stats['total_size_mb'] <= self.policy.max_total_size_mb:
                    break

                size = file.stat().st_size
                try:
                    file.unlink()
                    files_deleted += 1
                    space_freed += size
                    stats['total_size_mb'] -= size / (1024 * 1024)
                    self.logger.info(f"Deleted file to meet size limit: {file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to delete {file.name}: {e}")

        return files_deleted, round(space_freed / (1024 * 1024), 2)

    def should_run_cleanup(self) -> bool:
        """Check if cleanup should run based on interval"""
        if not self.last_cleanup_file.exists():
            return True

        last_cleanup = self.last_cleanup_file.stat().st_mtime
        hours_since = (time.time() - last_cleanup) / 3600

        return hours_since >= self.policy.auto_cleanup_interval_hours

    def run_auto_cleanup(self) -> Optional[Dict]:
        """Run automatic cleanup if needed"""
        if not self.should_run_cleanup():
            return None

        files_deleted, space_freed = self.cleanup_old_files()

        # Update last cleanup time
        self.last_cleanup_file.touch()

        result = {
            'timestamp': datetime.now().isoformat(),
            'files_deleted': files_deleted,
            'space_freed_mb': space_freed
        }

        self.logger.info(f"Auto cleanup completed: {result}")
        return result

    def update_policy(self, **kwargs):
        """Update policy settings"""
        for key, value in kwargs.items():
            if hasattr(self.policy, key):
                setattr(self.policy, key, value)

        self.save_config()
        self.logger.info(f"Policy updated: {kwargs}")
