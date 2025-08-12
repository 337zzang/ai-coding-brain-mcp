"""
O3 작업 파일 관리 시스템
- JSON 파일 자동 저장
- 오래된 파일 자동 삭제
- 작업 히스토리 관리
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import shutil

class O3TaskManager:
    """O3 작업 파일 관리자"""

    def __init__(self, base_dir: str = ".ai-brain/o3_tasks"):
        self.base_dir = base_dir
        self.ensure_directory()
        self._lock = threading.Lock()

        # 설정
        self.max_age_days = 7  # 7일 이상 된 파일 삭제
        self.max_files = 100   # 최대 100개 파일 유지
        self.auto_cleanup = True

    def ensure_directory(self):
        """디렉토리 생성"""
        os.makedirs(self.base_dir, exist_ok=True)

    def get_task_path(self, task_id: str) -> str:
        """작업 파일 경로"""
        return os.path.join(self.base_dir, f"{task_id}.json")

    def save_task(self, task_id: str, data: Dict[str, Any]) -> bool:
        """작업 상태를 JSON으로 저장"""
        try:
            # datetime 객체 처리
            data_copy = self._serialize_data(data)

            # 메타데이터 추가
            data_copy['_saved_at'] = datetime.now().isoformat()
            data_copy['_version'] = '1.0'

            # 파일 저장
            file_path = self.get_task_path(task_id)
            with self._lock:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_copy, f, indent=2, ensure_ascii=False)

            print(f"📝 Task 저장: {task_id}")

            # 자동 정리
            if self.auto_cleanup:
                self.cleanup_old_tasks()

            return True

        except Exception as e:
            print(f"❌ Task 저장 실패: {e}")
            return False

    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """JSON에서 작업 로드"""
        try:
            file_path = self.get_task_path(task_id)
            if not os.path.exists(file_path):
                return None

            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # datetime 역직렬화
            return self._deserialize_data(data)

        except Exception as e:
            print(f"❌ Task 로드 실패: {e}")
            return None

    def delete_task(self, task_id: str) -> bool:
        """작업 파일 삭제"""
        try:
            file_path = self.get_task_path(task_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Task 삭제: {task_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Task 삭제 실패: {e}")
            return False

    def list_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """모든 작업 목록"""
        tasks = []

        try:
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    task_id = filename[:-5]
                    task_data = self.load_task(task_id)

                    if task_data:
                        if status_filter is None or task_data.get('status') == status_filter:
                            tasks.append(task_data)
        except Exception as e:
            print(f"❌ Task 목록 조회 실패: {e}")

        return tasks

    def cleanup_old_tasks(self, max_age_days: Optional[int] = None) -> int:
        """오래된 작업 파일 정리"""
        if max_age_days is None:
            max_age_days = self.max_age_days

        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        try:
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.base_dir, filename)

                    # 파일 수정 시간 확인
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    if mtime < cutoff_time:
                        # 완료된 작업만 삭제
                        task_data = self.load_task(filename[:-5])
                        if task_data and task_data.get('status') in ['completed', 'error']:
                            os.remove(file_path)
                            deleted_count += 1
                            print(f"🗑️ 오래된 파일 삭제: {filename}")

            # 파일 수 제한
            files = sorted(os.listdir(self.base_dir), 
                         key=lambda x: os.path.getmtime(os.path.join(self.base_dir, x)))

            if len(files) > self.max_files:
                excess = len(files) - self.max_files
                for filename in files[:excess]:
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.base_dir, filename)
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"🗑️ 초과 파일 삭제: {filename}")

        except Exception as e:
            print(f"❌ 정리 실패: {e}")

        if deleted_count > 0:
            print(f"✅ {deleted_count}개 파일 정리 완료")

        return deleted_count

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보"""
        stats = {
            'total': 0,
            'running': 0,
            'completed': 0,
            'error': 0,
            'total_size': 0,
            'oldest_file': None,
            'newest_file': None
        }

        try:
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.base_dir, filename)
                    stats['total'] += 1
                    stats['total_size'] += os.path.getsize(file_path)

                    # 상태별 카운트
                    task_data = self.load_task(filename[:-5])
                    if task_data:
                        status = task_data.get('status', 'unknown')
                        if status == 'running':
                            stats['running'] += 1
                        elif status == 'completed':
                            stats['completed'] += 1
                        elif status == 'error':
                            stats['error'] += 1

                    # 시간 정보
                    mtime = os.path.getmtime(file_path)
                    if stats['oldest_file'] is None or mtime < stats['oldest_file'][1]:
                        stats['oldest_file'] = (filename, mtime)
                    if stats['newest_file'] is None or mtime > stats['newest_file'][1]:
                        stats['newest_file'] = (filename, mtime)

        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")

        return stats

    def archive_completed_tasks(self, archive_dir: str = None) -> int:
        """완료된 작업 아카이브"""
        if archive_dir is None:
            archive_dir = os.path.join(self.base_dir, "archive")

        os.makedirs(archive_dir, exist_ok=True)
        archived_count = 0

        try:
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    task_data = self.load_task(filename[:-5])

                    if task_data and task_data.get('status') == 'completed':
                        src = os.path.join(self.base_dir, filename)
                        dst = os.path.join(archive_dir, filename)
                        shutil.move(src, dst)
                        archived_count += 1
                        print(f"📦 아카이브: {filename}")

        except Exception as e:
            print(f"❌ 아카이브 실패: {e}")

        if archived_count > 0:
            print(f"✅ {archived_count}개 파일 아카이브 완료")

        return archived_count

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """datetime 객체 직렬화"""
        data_copy = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                data_copy[key] = value.isoformat()
            elif isinstance(value, dict):
                data_copy[key] = self._serialize_data(value)
            else:
                data_copy[key] = value
        return data_copy

    def _deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """datetime 문자열 역직렬화"""
        for key, value in data.items():
            if key in ['start_time', 'end_time', '_saved_at'] and isinstance(value, str):
                try:
                    data[key] = datetime.fromisoformat(value)
                except:
                    pass
            elif isinstance(value, dict):
                data[key] = self._deserialize_data(value)
        return data

# 글로벌 매니저 인스턴스
_task_manager = O3TaskManager()

# 편의 함수들
def save_o3_task(task_id: str, data: Dict[str, Any]) -> bool:
    """O3 작업 저장"""
    return _task_manager.save_task(task_id, data)

def load_o3_task(task_id: str) -> Optional[Dict[str, Any]]:
    """O3 작업 로드"""
    return _task_manager.load_task(task_id)

def delete_o3_task(task_id: str) -> bool:
    """O3 작업 삭제"""
    return _task_manager.delete_task(task_id)

def cleanup_o3_tasks(max_age_days: int = 7) -> int:
    """오래된 O3 작업 정리"""
    return _task_manager.cleanup_old_tasks(max_age_days)

def get_o3_statistics() -> Dict[str, Any]:
    """O3 작업 통계"""
    return _task_manager.get_statistics()

def archive_o3_tasks() -> int:
    """완료된 O3 작업 아카이브"""
    return _task_manager.archive_completed_tasks()
