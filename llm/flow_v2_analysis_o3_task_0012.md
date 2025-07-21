# o3_task_0012 분석 결과

통합 목표
1. 현재 WorkflowManager 로직을 최대한 보존한다.  
2. Plan → Task 2-계층과 v2 파일구조를 추가한다.  
3. v1(workflow.json 에 tasks 배열만 존재)과 v2가 혼재돼도 동작한다.  
4. CLI(/flow 명령)·내부 API 모두 점진적으로 이전한다.

──────────────────────────────
1. 데이터 모델 확장
──────────────────────────────
(models.py ‑ 새 파일, dataclass 사용)

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Task:
    id: str
    title: str
    description: str = ''
    status: str = 'pending'
    plan_id: str = ''
    dependencies: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)

@dataclass
class Plan:
    id: str
    title: str
    objective: str
    status: str = 'in_progress'
    tasks: List[Task] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    created_at: str = ''
    updated_at: str = ''

전환 포인트
• v1 데이터는 Plan 하나(plan_legacy)에 래핑한다.  
• Task 구조체는 plan_id 필드를 갖고 v1 → v2 자동 채워 넣는다.

──────────────────────────────
2. workflow.json v2 스키마
──────────────────────────────
{
  "version": "2.0",
  "project_name": "...",
  "current_plan_id": "plan_001",
  "last_activity": "...",
  "metadata": { ... },
  "plans": [ { ...Plan... } ]
}

컨텍스트, 문서 디렉터리, 스냅샷 폴더는 설계서 그대로 만든다.

──────────────────────────────
3. WorkflowManager 리팩터링
──────────────────────────────

class WorkflowManager:
    def __init__(self, root='.ai-brain'):
        self.root = Path(root)
        self.workflow_path = self.root / 'workflow.json'
        self.snapshot_mgr = SnapshotManager(self.root)
        self._load()

    # ---------- public ----------
    # Plan Level
    def create_plan(self, title, objective, **kw):
        pid = self._new_id('plan')
        plan = Plan(id=pid, title=title, objective=objective, **kw)
        self.plans[pid] = plan
        self.current_plan_id = pid
        self._save()

    def switch_plan(self, pid):
        if pid not in self.plans:
            raise KeyError(f'Unknown plan {pid}')
        self.current_plan_id = pid
        self._save()

    # Task Level
    def add_task(self, title, description='', plan_id=None, **kw):
        plan_id = plan_id or self.current_plan_id
        tid = self._new_id('task')
        task = Task(id=tid, title=title, description=description,
                    plan_id=plan_id, **kw)
        self.plans[plan_id].tasks.append(task)
        self._save()

    # ---------- private ----------
    def _load(self):
        if not self.workflow_path.exists():
            self._bootstrap_empty()
            return
        data = json.load(open(self.workflow_path))
        if data.get('version') != '2.0':
            data = self._migrate_v1_to_v2(data)
        self._from_dict(data)

    def _save(self):
        data = self._to_dict()
        json.dump(data, open(self.workflow_path,'w'), indent=2, ensure_ascii=False)
        self.snapshot_mgr.take_snapshot(data)

    def _migrate_v1_to_v2(self, data):
        default_plan = {
            "id": "plan_legacy",
            "title": "Legacy Plan",
            "objective": "Auto-converted from v1",
            "status": "in_progress",
            "tasks": data.get("tasks", [])
        }
        return {
            "version": "2.0",
            "project_name": data.get("project_name","legacy-project"),
            "current_plan_id": "plan_legacy",
            "last_activity": datetime.utcnow().isoformat(),
            "metadata": {},
            "plans": [default_plan]
        }

• _from_dict / _to_dict: Plan/Task 객체 ↔ dict 직렬화  
• _new_id(prefix): plan_001 / task_014 식 ID 생성  

기존 메서드 호환
- add_task_v1, list_tasks_v1 등 Wrapper 제공해 /flow task ... 이전 명령이 그대로 동작하게 한다. Wrapper 내부에서 self.current_plan_id를 사용하도록 매핑.

──────────────────────────────
4. SnapshotManager & ContextManager
──────────────────────────────
class SnapshotManager:
    def __init__(self, root):
        self.path = Path(root) / 'snapshots'
        self.path.mkdir(parents=True, exist_ok=True)
    def take_snapshot(self, payload):
        ts = datetime.utcnow().isoformat()
        with open(self.path/f'{ts}.json','w') as fp:
            json.dump(payload, fp, indent=2)

class ContextManager:
    def __init__(self, root):
        self.file = Path(root) / 'context.json'
    def save(self, ctx:dict):
        json.dump(ctx, open(self.file,'w'), indent=2)
    def load(self):
        return json.load(open(self.file)) if self.file.exists() else {}

WorkflowManager는 대화 종료마다 ContextManager.save(...) 호출.

──────────────────────────────
5. /flow CLI 확장
──────────────────────────────
$ flow plan create "대규모 리팩터" --objective "..."
$ flow plan list
$ flow plan switch plan_002
$ flow task add "모듈 A 테스트 작성" -p plan_002
$ flow task ls            # 현재 활성 plan 기준
$ flow task ls -p plan_legacy

CLI 구현 요령
- click / argparse 서브커맨드에 plan, task 그룹 추가  
- 기존 /flow task add ... 은 내부적으로 현재 Plan에 위임

──────────────────────────────
6. 단계적 적용 로드맵
──────────────────────────────
Phase 0 (1일)  : dataclass, SnapshotManager 도입, v1 동작 불변  
Phase 1 (1~2일): v2 스키마 지원, 자동 마이그레이션 코드 추가  
Phase 2 (1일)  : Plan API & CLI 노출, Wrappers로 구 버전 호환  
Phase 3 (1일)  : context.json · documents/ 폴더 통합  
Phase 4 (반복): 테스트, 문서화, 코드정리

──────────────────────────────
7. 마이그레이션 스크립트(선택)
──────────────────────────────
python -m flow.upgrade ./project-path
→ workflow.json 로드 → _migrate_v1_to_v2() 적용 → 백업 후 overwrite  
별도 실행해도 되고 WorkflowManager __init__ 에서 자동 처리해도 된다.

──────────────────────────────
8. 테스트 전략
──────────────────────────────
• unit: _migrate_v1_to_v2, Plan/Task 직렬화, add_task, switch_plan  
• integration: CLI 명령 시 workflow.json·snapshots·context 생성 검증  
• backward compatibility: v1 파일 fixture에 add_task_v1 실행 → 파일 변형 없음을 확인

──────────────────────────────
9. 예상 이슈 & 해결
──────────────────────────────
- 기존 코드가 tasks 배열에 직접 접근하는 부분 → self.get_tasks() helper를 두고 내부 구현만 Plan 계층으로 변경  
- 파일 충돌(동시 실행) → save 단계에서 파일 락 or atomic-write(tmp → mv)  
- JSON 용량 증가 → snapshots 폴더 .gitignore, 오래된 스냅샷 자동 정리 옵션

이렇게 하면 기존 로직 대부분을 유지하면서도 Plan → Task 계층, 완전한 컨텍스트 복원, 문서·스냅샷 관리까지 v2 설계를 자연스럽게 흡수할 수 있다.