# FlowService 개선 설계

## 1. 현재 문제점
- ~/.ai-flow/current_flow.txt 전역 파일 사용
- 프로젝트 간 current_flow 공유
- 캐시와 파일 시스템 불일치

## 2. 개선된 설계

```python
# python/ai_helpers_new/service/flow_service.py

from typing import Dict, List, Optional
from pathlib import Path

from ..domain.models import Flow
from ..infrastructure.flow_repository import FlowRepository
from ..infrastructure.project_context import ProjectContext

class FlowService:
    """프로젝트별 격리된 Flow Service"""

    def __init__(self, repository: FlowRepository, context: ProjectContext):
        self.repository = repository
        self.context = context
        self._flows: Dict[str, Flow] = {}
        self._current_flow_id: Optional[str] = None
        self._sync_with_repository()
        self._load_current_flow()

    @property
    def current_flow_file(self) -> Path:
        """프로젝트별 current_flow 파일"""
        return self.context.current_flow_file

    def set_context(self, context: ProjectContext):
        """컨텍스트 변경 (프로젝트 전환)"""
        self.context = context
        self._current_flow_id = None
        self._sync_with_repository()
        self._load_current_flow()

    def _sync_with_repository(self):
        """Repository와 동기화"""
        self._flows = self.repository.load_all()

    def _load_current_flow(self):
        """프로젝트별 current flow 로드"""
        if self.current_flow_file.exists():
            try:
                flow_id = self.current_flow_file.read_text().strip()
                if flow_id in self._flows:
                    self._current_flow_id = flow_id
                else:
                    # 유효하지 않은 flow ID면 파일 삭제
                    self.current_flow_file.unlink()
                    self._current_flow_id = None
            except Exception as e:
                print(f"Error loading current flow: {e}")
                self._current_flow_id = None

    def _save_current_flow(self):
        """현재 flow ID 저장"""
        if self._current_flow_id:
            self.current_flow_file.write_text(self._current_flow_id)
        elif self.current_flow_file.exists():
            self.current_flow_file.unlink()

    def create_flow(self, name: str) -> Flow:
        """새 Flow 생성"""
        flow = Flow(name=name)
        self._flows[flow.id] = flow
        self.repository.save(flow)

        # 첫 번째 flow면 자동으로 current로 설정
        if len(self._flows) == 1:
            self.set_current_flow(flow.id)

        return flow

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 조회"""
        return self._flows.get(flow_id)

    def list_flows(self) -> List[Flow]:
        """모든 Flow 목록"""
        return list(self._flows.values())

    def update_flow(self, flow: Flow) -> bool:
        """Flow 업데이트"""
        if flow.id in self._flows:
            self._flows[flow.id] = flow
            self.repository.save(flow)
            return True
        return False

    def delete_flow(self, flow_id: str) -> bool:
        """Flow 삭제"""
        if flow_id in self._flows:
            # current flow면 해제
            if self._current_flow_id == flow_id:
                self._current_flow_id = None
                self._save_current_flow()

            del self._flows[flow_id]
            self.repository.delete(flow_id)
            return True
        return False

    def get_current_flow(self) -> Optional[Flow]:
        """현재 Flow 반환"""
        if self._current_flow_id:
            return self._flows.get(self._current_flow_id)
        return None

    def set_current_flow(self, flow_id: str) -> bool:
        """현재 Flow 설정"""
        if flow_id in self._flows:
            self._current_flow_id = flow_id
            self._save_current_flow()
            return True
        return False

    def sync(self):
        """Repository와 강제 동기화"""
        self._sync_with_repository()
        self._load_current_flow()

    def get_project_info(self) -> dict:
        """프로젝트별 서비스 정보"""
        return {
            'project': str(self.context.root),
            'flows_count': len(self._flows),
            'current_flow': self._current_flow_id,
            'current_flow_name': self.get_current_flow().name if self.get_current_flow() else None
        }
```

## 3. 전역 파일 마이그레이션

```python
def migrate_global_current_flow(self):
    """전역 current_flow.txt 마이그레이션"""
    global_file = Path.home() / ".ai-flow" / "current_flow.txt"

    if global_file.exists() and not self.current_flow_file.exists():
        try:
            # 전역 파일 내용 읽기
            flow_id = global_file.read_text().strip()

            # 현재 프로젝트에 해당 flow가 있으면 마이그레이션
            if flow_id in self._flows:
                self._current_flow_id = flow_id
                self._save_current_flow()
                print(f"Migrated current flow from global: {flow_id}")
        except Exception as e:
            print(f"Failed to migrate global current flow: {e}")
```

## 4. 캐시 전략

- 메모리 캐시는 서비스 수명 동안 유지
- Context 변경 시 캐시 무효화
- sync() 메서드로 수동 동기화 가능
- 파일 시스템 감시는 구현하지 않음 (복잡도 vs 이득)
