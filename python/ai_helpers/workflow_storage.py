"""
워크플로우 데이터 저장소 - 안전한 읽기/쓰기 with 백업과 복구
"""
import json
import shutil
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger("workflow_storage")

# 경로 설정
WORKFLOW_DIR = Path("memory")
WORKFLOW_FILE = WORKFLOW_DIR / "workflow_data.json"
BACKUP_DIR = Path("backup") / "workflow_backups"

# 디렉토리 생성
WORKFLOW_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# 스키마 정의
WORKFLOW_SCHEMA = {
    "plans": dict,
    "current_plan_id": (str, type(None)),
    "settings": dict
}

def _timestamp() -> str:
    """타임스탬프 생성"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 밀리초까지

def _validate_schema(data: Dict[str, Any]) -> bool:
    """워크플로우 데이터 스키마 검증"""
    for key, expected_type in WORKFLOW_SCHEMA.items():
        if key not in data:
            logger.error(f"필수 키 누락: {key}")
            return False

        if isinstance(expected_type, tuple):
            # 여러 타입 허용 (예: str or None)
            if not isinstance(data[key], expected_type):
                logger.error(f"타입 오류: {key}는 {expected_type} 중 하나여야 함")
                return False
        else:
            if not isinstance(data[key], expected_type):
                logger.error(f"타입 오류: {key}는 {expected_type}여야 함")
                return False

    # plans 내부 구조 검증
    if not isinstance(data.get("plans"), dict):
        return False

    return True

def _create_backup(reason: str = "manual") -> Optional[Path]:
    """현재 워크플로우 파일 백업"""
    if not WORKFLOW_FILE.exists():
        return None

    try:
        backup_name = f"workflow_{_timestamp()}_{reason}.json"
        backup_path = BACKUP_DIR / backup_name
        shutil.copy2(WORKFLOW_FILE, backup_path)
        logger.info(f"백업 생성: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"백업 실패: {e}")
        return None

def _get_default_data() -> Dict[str, Any]:
    """기본 워크플로우 데이터 구조"""
    return {
        "plans": {},
        "current_plan_id": None,
        "settings": {
            "auto_save": True,
            "backup_on_save": True,
            "max_backups": 50
        }
    }

def load() -> Dict[str, Any]:
    """워크플로우 데이터 로드 (안전하게)"""
    if not WORKFLOW_FILE.exists():
        logger.info("워크플로우 파일이 없음. 기본값 반환")
        return _get_default_data()

    try:
        content = WORKFLOW_FILE.read_text(encoding='utf-8')
        if not content.strip():
            logger.warning("워크플로우 파일이 비어있음")
            return _get_default_data()

        data = json.loads(content)

        # 스키마 검증
        if not _validate_schema(data):
            logger.error("스키마 검증 실패. 백업 후 기본값 반환")
            _create_backup("schema_error")
            return _get_default_data()

        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        _create_backup("json_error")
        return _get_default_data()
    except Exception as e:
        logger.error(f"로드 중 오류: {e}")
        return _get_default_data()

def save(data: Dict[str, Any], reason: str = "update") -> bool:
    """워크플로우 데이터 저장 (원자적 쓰기)"""
    try:
        # 1. 스키마 검증
        if not _validate_schema(data):
            logger.error("저장 실패: 스키마 검증 오류")
            return False

        # 2. 백업 생성 (설정에 따라)
        if data.get("settings", {}).get("backup_on_save", True):
            _create_backup(reason)

        # 3. 임시 파일에 쓰기
        temp_file = WORKFLOW_FILE.with_suffix('.tmp')
        temp_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # 4. 원자적 교체
        temp_file.replace(WORKFLOW_FILE)

        logger.info(f"워크플로우 저장 완료: {reason}")
        return True

    except Exception as e:
        logger.error(f"저장 실패: {e}")
        return False

def restore_from_backup(backup_name: str) -> bool:
    """백업에서 복원"""
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        logger.error(f"백업 파일 없음: {backup_path}")
        return False

    try:
        # 현재 파일 백업
        if WORKFLOW_FILE.exists():
            _create_backup("before_restore")

        # 백업에서 복원
        shutil.copy2(backup_path, WORKFLOW_FILE)
        logger.info(f"백업에서 복원 완료: {backup_name}")

        # 복원된 데이터 검증
        restored_data = load()
        if _validate_schema(restored_data):
            return True
        else:
            logger.error("복원된 데이터 검증 실패")
            return False

    except Exception as e:
        logger.error(f"복원 실패: {e}")
        return False

def list_backups() -> list[Dict[str, Any]]:
    """백업 목록 조회"""
    backups = []

    for backup_file in BACKUP_DIR.glob("workflow_*.json"):
        try:
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "age_hours": (time.time() - stat.st_mtime) / 3600
            })
        except Exception as e:
            logger.warning(f"백업 정보 읽기 실패: {backup_file} - {e}")

    # 최신 순으로 정렬
    backups.sort(key=lambda x: x["modified"], reverse=True)
    return backups

def cleanup_old_backups(max_age_hours: int = 24 * 7) -> int:
    """오래된 백업 정리"""
    removed = 0

    for backup_info in list_backups():
        if backup_info["age_hours"] > max_age_hours:
            try:
                Path(backup_info["path"]).unlink()
                removed += 1
                logger.info(f"오래된 백업 삭제: {backup_info['name']}")
            except Exception as e:
                logger.error(f"백업 삭제 실패: {backup_info['name']} - {e}")

    return removed

def get_status() -> Dict[str, Any]:
    """저장소 상태 조회"""
    return {
        "workflow_file_exists": WORKFLOW_FILE.exists(),
        "workflow_file_size": WORKFLOW_FILE.stat().st_size if WORKFLOW_FILE.exists() else 0,
        "backup_count": len(list(BACKUP_DIR.glob("workflow_*.json"))),
        "latest_backup": list_backups()[0] if list_backups() else None,
        "is_valid": _validate_schema(load()) if WORKFLOW_FILE.exists() else False
    }

# 트랜잭션 컨텍스트 매니저
class WorkflowTransaction:
    """워크플로우 트랜잭션 지원"""

    def __init__(self):
        self.original_data = None
        self.backup_path = None

    def __enter__(self):
        # 트랜잭션 시작 시 현재 상태 백업
        self.original_data = load()
        self.backup_path = _create_backup("transaction")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 오류 발생 시 롤백
            logger.error(f"트랜잭션 실패, 롤백: {exc_val}")
            if self.original_data:
                save(self.original_data, "rollback")
            return False
        return True

    def commit(self, data: Dict[str, Any]) -> bool:
        """트랜잭션 커밋"""
        return save(data, "transaction_commit")

# Export
__all__ = [
    'load', 'save', 'restore_from_backup', 'list_backups',
    'cleanup_old_backups', 'get_status', 'WorkflowTransaction'
]
