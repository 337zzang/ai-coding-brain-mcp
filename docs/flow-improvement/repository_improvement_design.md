# JsonFlowRepository 개선 설계

## 1. 현재 문제점
- storage_path가 초기화 시 고정됨
- 프로젝트 전환 시 경로 업데이트 불가
- 싱글톤 패턴으로 인한 유연성 부족

## 2. 개선된 설계

```python
# python/ai_helpers_new/infrastructure/flow_repository.py

from pathlib import Path
from typing import Dict, Optional
import json
import shutil
from datetime import datetime

from ..domain.models import Flow
from .project_context import ProjectContext

class JsonFlowRepository(FlowRepository):
    """ProjectContext 기반 동적 Flow Repository"""

    def __init__(self, context: ProjectContext):
        """
        Args:
            context: 프로젝트 컨텍스트
        """
        self._context = context
        self._ensure_file()
        self._cache: Optional[Dict[str, Flow]] = None

    @property
    def storage_path(self) -> Path:
        """동적 storage path - context 변경 시 자동 반영"""
        return self._context.flow_file

    def set_context(self, context: ProjectContext):
        """프로젝트 컨텍스트 변경

        Args:
            context: 새 프로젝트 컨텍스트
        """
        self._context = context
        self._cache = None  # 캐시 무효화
        self._ensure_file()

    def _ensure_file(self):
        """flows.json 파일 확인 및 생성"""
        if not self.storage_path.exists():
            self._write_data({})

    def load_all(self) -> Dict[str, Flow]:
        """모든 Flow 로드 (캐시 사용)"""
        if self._cache is None:
            self._cache = self._load_from_disk()
        return self._cache.copy()

    def _load_from_disk(self) -> Dict[str, Flow]:
        """디스크에서 Flow 데이터 로드"""
        try:
            data = self._read_data()
            flows = {}

            for flow_id, flow_data in data.items():
                if isinstance(flow_data, dict):
                    try:
                        flows[flow_id] = Flow.from_dict(flow_data)
                    except Exception as e:
                        print(f"Warning: Failed to load flow {flow_id}: {e}")
                        continue

            return flows
        except Exception as e:
            print(f"Error loading flows: {e}")
            return {}

    def save(self, flow: Flow) -> None:
        """단일 Flow 저장"""
        flows = self.load_all()
        flows[flow.id] = flow
        self.save_all(flows)

    def save_all(self, flows: Dict[str, Flow]) -> None:
        """모든 Flow 저장"""
        # 백업 생성
        self._create_backup()

        # 데이터 변환 및 저장
        data = {}
        for flow_id, flow in flows.items():
            if isinstance(flow, Flow):
                data[flow_id] = flow.to_dict()
            else:
                data[flow_id] = flow

        self._write_data(data)
        self._cache = flows.copy()  # 캐시 업데이트

    def delete(self, flow_id: str) -> bool:
        """Flow 삭제"""
        flows = self.load_all()
        if flow_id in flows:
            del flows[flow_id]
            self.save_all(flows)
            return True
        return False

    def _create_backup(self):
        """자동 백업 생성"""
        if self.storage_path.exists():
            backup_dir = self._context.ai_brain_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"flows_backup_{timestamp}.json"

            # 최대 10개 백업 유지
            self._cleanup_old_backups(backup_dir, max_backups=10)

            shutil.copy2(self.storage_path, backup_path)

    def _cleanup_old_backups(self, backup_dir: Path, max_backups: int):
        """오래된 백업 파일 정리"""
        backups = sorted(backup_dir.glob("flows_backup_*.json"))
        if len(backups) > max_backups:
            for backup in backups[:-max_backups]:
                backup.unlink()

    def _read_data(self) -> dict:
        """JSON 데이터 읽기"""
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_data(self, data: dict):
        """JSON 데이터 쓰기 (atomic write)"""
        # 임시 파일에 먼저 쓰기
        temp_path = self.storage_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 원자적 교체
        temp_path.replace(self.storage_path)

    def get_project_info(self) -> dict:
        """현재 프로젝트 정보 반환"""
        return {
            'project': str(self._context.root),
            'storage_path': str(self.storage_path),
            'flows_count': len(self.load_all()),
            'file_size': self.storage_path.stat().st_size if self.storage_path.exists() else 0
        }
```

## 3. 마이그레이션 호환성

```python
# 레거시 지원을 위한 팩토리 메서드
@classmethod
def from_path(cls, storage_path: Optional[str] = None) -> 'JsonFlowRepository':
    """경로 기반 생성 (레거시 호환)"""
    if storage_path:
        # 경로에서 프로젝트 루트 추론
        path = Path(storage_path)
        if path.name == "flows.json" and path.parent.name == ".ai-brain":
            project_root = path.parent.parent
        else:
            project_root = Path.cwd()
    else:
        project_root = Path.cwd()

    context = ProjectContext(project_root)
    return cls(context)
```

## 4. 테스트 계획

- 동적 경로 변경 테스트
- 캐시 무효화 테스트
- 백업 생성/정리 테스트
- 원자적 쓰기 테스트
- 레거시 호환성 테스트
