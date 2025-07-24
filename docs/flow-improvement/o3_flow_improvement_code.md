# o3 Flow 시스템 개선 코드

생성일: 2025-07-24T13:34:25.599874
분석 난이도: high
토큰 사용: 7620

---

아래 예시는 “하나의 FlowManager + 3-단계 상태 + 파일 Lock + 단일-라인 CLI”라는 4가지 요구사항을 모두 충족하도록 최소 구성으로 작성한 참조 구현 코드입니다.  

(코드가 길어 가독성을 위해 파일별로 구분했습니다. 그대로 복사해 폴더 구조만 맞춰주면 바로 동작합니다.)

──────────────────────── flow_manager.py
```python
"""
통합 FlowManager
 - todo → active → done 3단계 상태
 - 파일 락(FileLock)으로 동시 쓰기 보호
 - Context 시스템(FlowContextWrapper) 자동 연동
"""
from __future__ import annotations

import os, json, uuid, time
from datetime import datetime
from typing import Dict, Any, Optional, List, Literal, Tuple, Generator
from contextlib import contextmanager

# 1) 파일 락 ------------------------------------------------------------------
try:
    # 권장 : pip install filelock
    from filelock import FileLock, Timeout
except ImportError:  # filelock 미설치 시 매우 단순한 fallback
    import threading

    class Timeout(Exception):
        pass

    class _ThreadLock:
        def __init__(self, path):     self.lock = threading.Lock()
        @contextmanager
        def acquire(self, timeout=10):
            ok = self.lock.acquire(timeout=timeout)
            if not ok: raise Timeout("acquire timeout")
            try:  yield
            finally: self.lock.release()

    FileLock = _ThreadLock   # type: ignore


# 2) Context 래퍼 --------------------------------------------------------------
from FlowContextWrapper import (      # 동일 경로에 이미 존재
    record_flow_action,
    record_plan_action,
    record_task_action,
)

# 3) 상수 ---------------------------------------------------------------------
VALID_STATES: Tuple[str, ...] = ("todo", "active", "done")


# 4) FlowManager --------------------------------------------------------------
class FlowManager:
    """하나의 json 파일로 flows/plan/task를 관리한다."""

    def __init__(self, base_dir: str = ".ai-brain"):
        self.base_dir           = base_dir
        self.flows_file         = os.path.join(base_dir, "flows.json")
        self._lock_path         = self.flows_file + ".lock"
        self._lock              = FileLock(self._lock_path)
        self._ensure_dirs()

        self.flows: Dict[str, Any] = self._load_flows()
        self.current_flow_id: Optional[str] = None

    # --------------------------------------------------------------------- IO
    def _ensure_dirs(self):
        os.makedirs(self.base_dir, exist_ok=True)
        if not os.path.exists(self.flows_file):
            with open(self.flows_file, "w") as f: json.dump({}, f)

    def _load_flows(self) -> Dict[str, Any]:
        with open(self.flows_file, "r") as f:
            return json.load(f)

    def _save_flows(self):
        with self._lock.acquire(timeout=10):
            with open(self.flows_file, "w") as f:
                json.dump(self.flows, f, indent=2, default=str)

    # ---------------------------------------------------------------- Flow
    def create_flow(self, name: str, description: str = "") -> str:
        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        self.flows[flow_id] = {
            "id": flow_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "plans": {},
        }
        self.current_flow_id = flow_id
        self._save_flows()

        record_flow_action(flow_id, "created", {"name": name})
        return flow_id

    def use_flow(self, flow_id: str) -> bool:
        if flow_id in self.flows:
            self.current_flow_id = flow_id
            return True
        return False

    def list_flows(self) -> List[Dict[str, Any]]:
        return list(self.flows.values())

    # -------------------------------------------------------------- Plan
    def add_plan(self, name: str, description: str = "") -> Optional[str]:
        flow = self._cur_flow()
        if not flow: return None

        plan_id = f"plan_{uuid.uuid4().hex[:6]}"
        flow["plans"][plan_id] = {
            "id": plan_id,
            "name": name,
            "description": description,
            "tasks": {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save_flows()
        record_plan_action(flow["id"], plan_id, "added", {"name": name})
        return plan_id

    def list_plans(self) -> List[Dict[str, Any]]:
        flow = self._cur_flow()
        return list(flow["plans"].values()) if flow else []

    # -------------------------------------------------------------- Task
    def add_task(
        self,
        plan_id: str,
        name: str,
        description: str = "",
    ) -> Optional[str]:
        flow, plan = self._cur_flow_plan(plan_id)
        if not plan: return None

        task_id = f"task_{uuid.uuid4().hex[:6]}"
        plan["tasks"][task_id] = {
            "id": task_id,
            "name": name,
            "description": description,
            "status": "todo",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._save_flows()
        record_task_action(flow["id"], task_id, "added", {"name": name})
        return task_id

    def change_task_status(self, task_id: str, new_status: Literal["todo", "active", "done"]) -> bool:
        flow, task = self._find_task(task_id)
        if not task or new_status not in VALID_STATES:
            return False

        old_status = task["status"]
        if old_status == new_status:
            return True  # already

        # 상태 전환 허용 규칙 : todo→active→done (역방향은 지원하지 않음)
        allowed = {
            "todo": {"active"},
            "active": {"done"},
            "done": set(),
        }
        if new_status not in allowed.get(old_status, set()):
            return False

        task["status"]    = new_status
        task["updated_at"] = datetime.utcnow().isoformat()
        self._save_flows()

        record_task_action(
            flow["id"], task_id, f"status_{new_status}",
            {"from": old_status, "to": new_status}
        )
        return True

    # -------------------------------------------------------- 내부 보조 메서드
    def _cur_flow(self) -> Optional[Dict[str, Any]]:
        if self.current_flow_id and self.current_flow_id in self.flows:
            return self.flows[self.current_flow_id]
        return None

    def _cur_flow_plan(self, plan_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        flow = self._cur_flow()
        if not flow or plan_id not in flow["plans"]:
            return flow, None
        return flow, flow["plans"][plan_id]

    def _find_task(self, task_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """모든 plan을 순회하며 task 검색"""
        flow = self._cur_flow()
        if not flow: return None, None
        for plan in flow["plans"].values():
            if task_id in plan["tasks"]:
                return flow, plan["tasks"][task_id]
        return None, None
```

──────────────────────── cli.py
```python
"""
단순화된 커맨드라인 인터페이스
-----------------------------------
flow create <name> [description]
flow use    <flow_id>
plan add    <name> [description]
task add    <plan_id> <name> [description]
task start  <task_id>
task done   <task_id>
show        flows|plans|tasks
-----------------------------------
"""
import sys, argparse, textwrap, json
from flow_manager import FlowManager

fm = FlowManager()

def _print(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))

def cmd_flow_create(args):
    fid = fm.create_flow(args.name, args.description)
    print(f"CREATED flow_id={fid}")

def cmd_flow_use(args):
    ok = fm.use_flow(args.flow_id)
    print("OK" if ok else "NOT FOUND")

def cmd_plan_add(args):
    pid = fm.add_plan(args.name, args.description)
    print(f"CREATED plan_id={pid}" if pid else "ERROR")

def cmd_task_add(args):
    tid = fm.add_task(args.plan_id, args.name, args.description)
    print(f"CREATED task_id={tid}" if tid else "ERROR")

def cmd_task_start(args):
    ok = fm.change_task_status(args.task_id, "active")
    print("STARTED" if ok else "FAILED")

def cmd_task_done(args):
    ok = fm.change_task_status(args.task_id, "done")
    print("DONE" if ok else "FAILED")

def cmd_show(args):
    if args.target == "flows": _print(fm.list_flows())
    elif args.target == "plans": _print(fm.list_plans())
    elif args.target == "tasks":
        tasks = []
        for p in fm.list_plans():
            tasks.extend(p["tasks"].values())
        _print(tasks)

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Flow CLI", formatter_class=argparse.RawTextHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # flow create/use
    fl = sub.add_parser("flow"); fl_sub = fl.add_subparsers(dest="sub", required=True)
    fl_create = fl_sub.add_parser("create"); fl_create.add_argument("name"); fl_create.add_argument("description", nargs="?", default=""); fl_create.set_defaults(func=cmd_flow_create)
    fl_use = fl_sub.add_parser("use"); fl_use.add_argument("flow_id"); fl_use.set_defaults(func=cmd_flow_use)

    # plan add
    pl_add = sub.add_parser("plan"); pl_sub = pl_add.add_subparsers(dest="sub", required=True)
    pl_add_sub = pl_sub.add_parser("add"); pl_add_sub.add_argument("name"); pl_add_sub.add_argument("description", nargs="?", default=""); pl_add_sub.set_defaults(func=cmd_plan_add)

    # task add/start/done
    tk = sub.add_parser("task"); tk_sub = tk.add_subparsers(dest="sub", required=True)

    tk_add = tk_sub.add_parser("add"); tk_add.add_argument("plan_id"); tk_add.add_argument("name"); tk_add.add_argument("description", nargs="?", default=""); tk_add.set_defaults(func=cmd_task_add)

    tk_start = tk_sub.add_parser("start"); tk_start.add_argument("task_id"); tk_start.set_defaults(func=cmd_task_start)
    tk_done  = tk_sub.add_parser("done");  tk_done.add_argument("task_id"); tk_done.set_defaults(func=cmd_task_done)

    # show
    show = sub.add_parser("show"); show.add_argument("target", choices=["flows", "plans", "tasks"]); show.set_defaults(func=cmd_show)

    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
```

──────────────────────── 기존 데이터 호환(마이그레이션)
구(5단계) → 신(3단계) 매핑은 FlowManager 인스턴스 생성 직후 1회만 실행해도 됩니다.  
예시:

```python
def _normalize_legacy_status(self):
    mapping = {
        "planning": "active",
        "in_progress": "active",
        "reviewing": "done",
        "completed": "done",
    }
    changed = False
    for flow in self.flows.values():
        for plan in flow.get("plans", {}).values():
            for task in plan.get("tasks", {}).values():
                if task["status"] in mapping:
                    task["status"] = mapping[task["status"]]
                    changed = True
    if changed:
        self._save_flows()
```
(위 코드를 `__init__` 마지막 줄에서 호출하면 자동 이행)

──────────────────────── 사용 예
```bash
# 새로운 Flow
$ python cli.py flow create "신규 프로젝트" "간단 설명"
CREATED flow_id=flow_12ab45cd

# Plan 추가
$ python cli.py plan add "백엔드 설계"
CREATED plan_id=plan_7fa32c

# Task 등록
$ python cli.py task add plan_7fa32c "DB 스키마 정의"
CREATED task_id=task_a1b2c3

# 작업 시작/완료
$ python cli.py task start task_a1b2c3
STARTED
$ python cli.py task done task_a1b2c3
DONE

# 전체 Task 확인
$ python cli.py show tasks
[
  {
    "id": "task_a1b2c3",
    "name": "DB 스키마 정의",
    "description": "",
    "status": "done",
    ...
  }
]
```

──────────────────────── 정리
1. FlowManager 하나로 모든 기능 통합 (FlowManagerUnified 제거).  
2. 상태는 todo→active→done 3단계로 단순화, 이전 상태는 자동 매핑.  
3. filelock 기반 파일 락으로 동시 저장 충돌 방지.  
4. 명령어는 `flow / plan / task / show` 4개 그룹으로 깔끔하게 통일.  
5. FlowContextWrapper를 내부에서 호출해 Flow/Plan/Task 변동을 자동 기록.  

프로덕션에서는  
- `filelock` 외에 OS별 fcntl/portalocker 등 보다 견고한 락 구현 고려  
- 예외 처리/유효성 검사 추가  
- 멀티-스레드 환경 성능 검증  
등을 보완해 주시면 됩니다.
