# 📋 폴더 기반 Flow 시스템 상세 설계

## 🏗️ 전체 설계 (Architecture Design)

### 🎯 목표
- 기존 단일 flows.json 구조를 프로젝트별 폴더 구조로 전환
- Git 협업 시 충돌 최소화 및 리뷰 용이성 향상
- 무중단 마이그레이션으로 기존 데이터 보존

### 📁 새로운 디렉토리 구조
```
프로젝트루트/
└── .ai-brain/
    └── flows/
        ├── flow_metadata.json     # (선택) 전체 Flow 인덱스
        └── <flow_id>/             # Flow별 독립 폴더
            ├── flow_metadata.json # Flow 메타데이터
            └── plans/             # Plan 전용 폴더
                ├── <plan_id>_<name>.json
                └── ...
```

### 🔍 현재 상태 분석

1. **기존 구조의 문제점**
   - 모든 Flow가 하나의 flows.json에 저장
   - 여러 사람이 동시 작업 시 Git 충돌 빈발
   - 파일 크기 증가로 성능 저하 가능성
   - Flow/Plan별 독립적 관리 불가

2. **현재 구현 분석**
   - FlowRepository (추상 클래스)
   - FileFlowRepository (미구현 상태)
   - flows.json 직접 읽기/쓰기

3. **영향 범위**
   - infrastructure/flow_repository.py 수정
   - service/cached_flow_service.py 호환성 확인
   - 마이그레이션 스크립트 신규 작성

## 📐 상세 설계 (Detailed Design)

### 1. JsonFlowRepository 클래스 구현

```python
# python/ai_helpers_new/infrastructure/json_flow_repository.py

from pathlib import Path
import json
import shutil
from typing import Dict, Optional
from datetime import datetime

from ai_helpers_new.models import Flow, Plan
from .flow_repository import FlowRepository
from .project_context import ProjectContext

class JsonFlowRepository(FlowRepository):
    FLOW_DIR = '.ai-brain/flows'
    META_FILENAME = 'flow_metadata.json'
    PLANS_DIR = 'plans'

    def __init__(self, context: Optional[ProjectContext] = None):
        self._context = context

    def _root(self) -> Path:
        """Flow 저장 루트 디렉토리"""
        base = self._context.root if self._context else Path.cwd()
        return base / self.FLOW_DIR

    def _flow_dir(self, flow_id: str) -> Path:
        """특정 Flow의 디렉토리"""
        return self._root() / flow_id

    def _plan_file(self, flow_id: str, plan: Plan) -> Path:
        """Plan 파일 경로 생성"""
        safe_name = self._sanitize_filename(plan.name)
        filename = f"{plan.id}_{safe_name}.json"
        return self._flow_dir(flow_id) / self.PLANS_DIR / filename

    def _sanitize_filename(self, name: str) -> str:
        """파일명으로 사용 가능한 문자열로 변환"""
        # 한글 유지, 특수문자를 _로 치환
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '_', name)
        return safe[:50]  # 최대 50자

    def load_all(self) -> Dict[str, Flow]:
        """모든 Flow 로드"""
        flows = {}
        root = self._root()

        if not root.exists():
            # 레거시 flows.json 확인
            return self._load_legacy()

        # 새 구조에서 로드
        for flow_path in root.iterdir():
            if not flow_path.is_dir():
                continue

            flow = self._load_flow(flow_path)
            if flow:
                flows[flow.id] = flow

        return flows

    def _load_flow(self, flow_path: Path) -> Optional[Flow]:
        """단일 Flow 로드"""
        meta_file = flow_path / self.META_FILENAME
        if not meta_file.exists():
            return None

        # 메타데이터 로드
        with meta_file.open('r', encoding='utf-8') as f:
            meta_dict = json.load(f)

        # Plans 로드
        plans = {}
        plans_dir = flow_path / self.PLANS_DIR
        if plans_dir.exists():
            for plan_file in plans_dir.glob('*.json'):
                with plan_file.open('r', encoding='utf-8') as f:
                    plan_dict = json.load(f)
                plan = Plan.model_validate(plan_dict)
                plans[plan.id] = plan

        meta_dict['plans'] = plans
        return Flow.model_validate(meta_dict)

    def save(self, flow: Flow) -> None:
        """Flow 저장"""
        flow_dir = self._flow_dir(flow.id)
        plans_dir = flow_dir / self.PLANS_DIR
        plans_dir.mkdir(parents=True, exist_ok=True)

        # 메타데이터 저장
        meta_dict = flow.model_dump(exclude={'plans'})
        meta_file = flow_dir / self.META_FILENAME
        self._atomic_write(meta_file, meta_dict)

        # Plans 저장
        current_plan_files = set()
        for plan in flow.plans.values():
            plan_file = self._plan_file(flow.id, plan)
            plan_file.parent.mkdir(exist_ok=True)
            current_plan_files.add(plan_file)
            self._atomic_write(plan_file, plan.model_dump())

        # 삭제된 Plan 파일 제거
        if plans_dir.exists():
            for plan_file in plans_dir.glob('*.json'):
                if plan_file not in current_plan_files:
                    plan_file.unlink()

    def save_all(self, flows: Dict[str, Flow]) -> None:
        """모든 Flow 저장"""
        for flow in flows.values():
            self.save(flow)

    def delete(self, flow_id: str) -> bool:
        """Flow 삭제"""
        flow_dir = self._flow_dir(flow_id)
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
            return True
        return False

    def _atomic_write(self, path: Path, data: dict) -> None:
        """원자적 파일 쓰기"""
        tmp_path = path.with_suffix('.tmp')
        with tmp_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        tmp_path.replace(path)

    def _load_legacy(self) -> Dict[str, Flow]:
        """레거시 flows.json 로드"""
        legacy_path = self._root().parent / 'flows.json'
        if not legacy_path.exists():
            return {}

        with legacy_path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        # 레거시는 단일 Flow만 지원
        if isinstance(data, dict) and 'id' in data:
            flow = Flow.model_validate(data)
            return {flow.id: flow}

        return {}
```

### 2. 마이그레이션 스크립트

```python
# python/ai_helpers_new/migrate_flows.py

import json
import shutil
from pathlib import Path
from datetime import datetime

from ai_helpers_new.models import Flow
from ai_helpers_new.infrastructure.json_flow_repository import JsonFlowRepository
from ai_helpers_new.infrastructure.project_context import ProjectContext

def migrate_flows(dry_run: bool = False):
    """레거시 flows.json을 새 구조로 마이그레이션"""

    print("🔄 Flow 마이그레이션 시작...")

    # 현재 프로젝트 컨텍스트
    context = ProjectContext.get_current()
    if not context:
        context = ProjectContext(root=Path.cwd())

    legacy_path = context.root / '.ai-brain' / 'flows.json'

    if not legacy_path.exists():
        print("✅ 레거시 flows.json이 없습니다. 마이그레이션 불필요.")
        return

    # 백업 생성
    backup_path = legacy_path.with_suffix(f'.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    if not dry_run:
        shutil.copy2(legacy_path, backup_path)
        print(f"📦 백업 생성: {backup_path}")

    # 레거시 데이터 로드
    with legacy_path.open('r', encoding='utf-8') as f:
        legacy_data = json.load(f)

    # Flow 객체로 변환
    flow = Flow.model_validate(legacy_data)
    print(f"📋 Flow 발견: {flow.name} (ID: {flow.id})")
    print(f"   - Plans: {len(flow.plans)}개")
    print(f"   - Tasks: {sum(len(p.tasks) for p in flow.plans.values())}개")

    if dry_run:
        print("\n🔍 Dry-run 모드 - 실제 변경사항 없음")
        print("새로운 구조:")
        new_root = context.root / '.ai-brain' / 'flows' / flow.id
        print(f"  {new_root}/")
        print(f"    flow_metadata.json")
        print(f"    plans/")
        for plan in flow.plans.values():
            safe_name = JsonFlowRepository()._sanitize_filename(plan.name)
            print(f"      {plan.id}_{safe_name}.json")
        return

    # 새 구조로 저장
    repo = JsonFlowRepository(context)
    repo.save(flow)

    # 레거시 파일 이름 변경
    legacy_path.rename(legacy_path.with_suffix('.migrated'))

    print("\n✅ 마이그레이션 완료!")
    print(f"   새 위치: {context.root / '.ai-brain' / 'flows' / flow.id}")

if __name__ == '__main__':
    import sys
    dry_run = '--dry-run' in sys.argv
    migrate_flows(dry_run)
```

### 3. Repository 통합

```python
# python/ai_helpers_new/infrastructure/flow_repository.py 수정

# 기존 FileFlowRepository 대신 JsonFlowRepository를 기본으로 사용
from .json_flow_repository import JsonFlowRepository

# Factory 패턴 또는 직접 사용
def create_flow_repository(context: Optional[ProjectContext] = None) -> FlowRepository:
    return JsonFlowRepository(context)
```

## 🛠️ Task별 실행 계획

### Task 1: JsonFlowRepository 구현
- **목표**: 새로운 폴더 기반 저장소 구현
- **예상 시간**: 1시간
- **상세 작업**:
  1. json_flow_repository.py 파일 생성
  2. 모든 메서드 구현 및 테스트
  3. 레거시 호환성 확인

### Task 2: 마이그레이션 스크립트 작성
- **목표**: 안전한 데이터 마이그레이션
- **예상 시간**: 30분
- **상세 작업**:
  1. migrate_flows.py 작성
  2. dry-run 모드 테스트
  3. 실제 마이그레이션 테스트

### Task 3: 기존 시스템 통합
- **목표**: 새 Repository를 기존 시스템에 연결
- **예상 시간**: 30분
- **상세 작업**:
  1. flow_repository.py 수정
  2. CachedFlowService 호환성 확인
  3. 통합 테스트

### Task 4: 테스트 및 문서화
- **목표**: 안정성 확보 및 사용 가이드 작성
- **예상 시간**: 30분
- **상세 작업**:
  1. 단위 테스트 작성
  2. 통합 테스트 실행
  3. 마이그레이션 가이드 문서 작성

## ⚠️ 위험 요소 및 대응 계획

| 위험 요소 | 발생 가능성 | 영향도 | 대응 방안 |
|----------|------------|-------|-----------|
| 데이터 손실 | 낮음 | 높음 | 자동 백업, dry-run 테스트 |
| 성능 저하 | 중간 | 중간 | 캐싱 유지, 인덱스 파일 추가 가능 |
| 호환성 문제 | 낮음 | 중간 | 레거시 읽기 지원, 점진적 마이그레이션 |

## ❓ 확인 필요 사항
1. 이 설계가 요구사항을 충족하나요?
2. 추가로 고려해야 할 사항이 있나요?
3. 구현 우선순위를 조정할 필요가 있나요?

**✅ 이 계획대로 진행해도 될까요?**
