"""Flow 백업 유틸리티"""
import os
import json
import shutil
from datetime import datetime
from typing import Optional, List, Dict

def create_backup(reason: str = "manual") -> Optional[str]:
    """Flow 데이터 백업 생성

    Args:
        reason: 백업 사유

    Returns:
        백업 파일 경로 또는 None
    """
    try:
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"flows_backup_{timestamp}_{reason}.json")

        source_file = ".ai-brain/flows.json"
        if os.path.exists(source_file):
            shutil.copy2(source_file, backup_file)

            # 백업 정보 추가
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['backup_info'] = {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'flow_count': len(data.get('flows', {}))
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            cleanup_old_backups()
            return backup_file

    except Exception as e:
        print(f"백업 실패: {e}")
        return None

def cleanup_old_backups(keep_count: int = 10):
    """오래된 백업 정리"""
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return

        backups = [f for f in os.listdir(backup_dir) 
                  if f.startswith("flows_backup_") and f.endswith(".json")]
        backups.sort(reverse=True)

        for old_file in backups[keep_count:]:
            os.remove(os.path.join(backup_dir, old_file))

    except Exception:
        pass

def list_backups() -> List[Dict]:
    """백업 목록 조회"""
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return []

        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("flows_backup_") and filename.endswith(".json"):
                file_path = os.path.join(backup_dir, filename)
                file_stat = os.stat(file_path)

                backup_files.append({
                    "filename": filename,
                    "path": file_path,
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime)
                })

        backup_files.sort(key=lambda x: x["created"], reverse=True)
        return backup_files

    except Exception:
        return []

def restore_backup(backup_file: str) -> bool:
    """백업 복구"""
    try:
        # 복구 전 백업
        create_backup("before_restore")

        if not os.path.isabs(backup_file):
            backup_file = os.path.join("backups", backup_file)

        if not os.path.exists(backup_file):
            return False

        # 복구
        shutil.copy2(backup_file, ".ai-brain/flows.json")
        return True

    except Exception:
        return False
