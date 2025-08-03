"""
Enhanced Task Logger for AI Coding Brain
작업 과정을 jsonl 형식으로 기록하는 로거
"""

import json
import os
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .project import get_current_project



def normalize_task_name(name: str) -> str:
    """Task 이름을 안전한 파일명으로 변환

    Args:
        name: 원본 task 이름

    Returns:
        파일시스템에 안전한 이름
    """
    # 한글, 영문, 숫자는 유지, 나머지는 언더스코어로
    safe_name = re.sub(r'[^a-zA-Z0-9가-힣_-]', '_', name)
    # 연속된 언더스코어 제거
    safe_name = re.sub(r'_{2,}', '_', safe_name)
    # 앞뒤 언더스코어 제거
    safe_name = safe_name.strip('_')
    # 길이 제한 (30자)
    safe_name = safe_name[:30]
    # 빈 문자열 방지
    return safe_name or "task"


class EnhancedTaskLogger:
    """Task 작업 과정을 jsonl 파일로 기록하는 로거

    파일명 형식: {순서}.{task_name}.jsonl
    예: 1.task_auth_refactor.jsonl
    """

    def __init__(self, plan_id: str, task_number: int, task_name: str):
        """TaskLogger 초기화

        Args:
            plan_id: Plan ID (예: plan_20250725_001)
            task_number: Task 순서 번호 (1, 2, 3...)
            task_name: Task 이름 (예: task_auth_refactor)
        """
        self.plan_id = plan_id
        self.task_number = task_number
        self.task_name = task_name

        # 경로 설정 - 프로젝트 루트 기준
        project_info = get_current_project()
        if isinstance(project_info, dict) and 'path' in project_info:
            project_root = Path(project_info['path'])
        else:
            # 폴백: 현재 디렉토리 사용
            project_root = Path.cwd()

        self.plan_dir = project_root / ".ai-brain" / "flow" / "plans" / plan_id
        # 파일명 정규화 적용
        safe_name = normalize_task_name(task_name)
        self.log_file = self.plan_dir / f"{task_number}.{safe_name}.jsonl"

        # 디렉토리 생성
        self.plan_dir.mkdir(parents=True, exist_ok=True)

    def _log(self, event_type: str, **data) -> Dict[str, Any]:
        """기본 로깅 메서드

        Args:
            event_type: 이벤트 타입
            **data: 이벤트 데이터

        Returns:
            기록된 이벤트 딕셔너리
        """
        timestamp = datetime.now().isoformat()
        event = {
            # 새 필드명
            "timestamp": timestamp,
            "event_type": event_type,
            # 구 필드명도 유지 (호환성)
            "ts": timestamp,
            "type": event_type,
            # 데이터
            **data
        }

        # jsonl 파일에 추가
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

        return event

    def task_info(self, title: str, priority: str = "medium", 
                  estimate: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """Task 기본 정보 기록

        Args:
            title: Task 제목
            priority: 우선순위 (low/medium/high)
            estimate: 예상 소요시간
            description: 상세 설명
        """
        return self._log("TASK_INFO", 
                        title=title, 
                        priority=priority, 
                        estimate=estimate,
                        description=description)

    def design(self, content: str) -> Dict[str, Any]:
        """설계 내용 기록

        Args:
            content: 설계 내용 (마크다운 지원)
        """
        return self._log("DESIGN", content=content)

    def todo(self, items: List[str]) -> Dict[str, Any]:
        """TODO 목록 기록

        Args:
            items: TODO 항목 리스트
        """
        return self._log("TODO", items=items)

    def todo_update(self, completed: Optional[List[str]] = None, 
                   remaining: Optional[List[str]] = None,
                   new_items: Optional[List[str]] = None) -> Dict[str, Any]:
        """TODO 진행상황 업데이트

        Args:
            completed: 완료된 항목들
            remaining: 남은 항목들
            new_items: 새로 추가된 항목들
        """
        data = {}
        if completed is not None:
            data['completed'] = completed
        if remaining is not None:
            data['remaining'] = remaining  
        if new_items is not None:
            data['new_items'] = new_items

        return self._log("TODO_UPDATE", **data)

    def analyze(self, target: str, findings: str) -> Dict[str, Any]:
        """분석 결과 기록

        Args:
            target: 분석 대상 (파일명, 모듈명 등)
            findings: 분석 결과 요약
        """
        return self._log("ANALYZE", target=target, findings=findings)

    def decision(self, title: str, choice: str, reasoning: str) -> Dict[str, Any]:
        """의사결정 기록

        Args:
            title: 결정 사항
            choice: 선택한 옵션
            reasoning: 선택 이유
        """
        return self._log("DECISION", 
                        title=title, 
                        choice=choice, 
                        reasoning=reasoning)

    def code(self, action: str, file: str, summary: str = "", 
             changes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """코드 변경 기록

        Args:
            action: 작업 유형 (create/modify/delete)
            file: 대상 파일
            summary: 변경 요약
            changes: 상세 변경사항 (선택적)
        """
        data = {
            "action": action,
            "file": file,
            "summary": summary
        }
        if changes:
            data["changes"] = changes

        return self._log("CODE", **data)

    def context(self, key: str, value: Any) -> Dict[str, Any]:
        """중요 컨텍스트 저장

        Args:
            key: 컨텍스트 키
            value: 컨텍스트 값 (JSON 직렬화 가능해야 함)
        """
        return self._log("CONTEXT", key=key, value=value)

    def blocker(self, issue: str, severity: str = "low", 
                solution: Optional[str] = None) -> Dict[str, Any]:
        """블로커/이슈 기록

        Args:
            issue: 문제 설명
            severity: 심각도 (low/medium/high/critical)
            solution: 해결 방안 (있는 경우)
        """
        data = {
            "issue": issue,
            "severity": severity
        }
        if solution:
            data["solution"] = solution

        return self._log("BLOCKER", **data)

    def note(self, content: str) -> Dict[str, Any]:
        """일반 메모/노트 기록

        Args:
            content: 메모 내용
        """
        return self._log("NOTE", content=content)

    def complete(self, summary: str, next_steps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Task 완료 기록

        Args:
            summary: 완료 요약
            next_steps: 다음 단계 (있는 경우)
        """
        data = {"summary": summary}
        if next_steps:
            data["next_steps"] = next_steps

        # 기존 로직: TaskLogger에 기록
        result = self._log("COMPLETE", **data)

#         # 추가: FlowManager 자동 업데이트
#         try:
#             # Task 번호로 Task ID 찾아서 완료 처리
#             from .ultra_simple_flow_manager import UltraSimpleFlowManager
#             manager = UltraSimpleFlowManager()
#             plan = manager.get_plan(self.plan_id)

#             if plan:
#                 # Task 번호로 task_id 찾기
#                 for task_id, task in plan.tasks.items():
#                     # Task 제목이 "번호. " 형식으로 시작하는지 확인
#                     if task.title.startswith(f"{self.task_number}."):
#                         # Task 상태를 DONE으로 업데이트
#                         manager.update_task_status(self.plan_id, task_id, "done")
#                         break
#         except Exception as e:
#             # 실패해도 TaskLogger는 정상 동작
#             print(f"[TaskLogger] Flow 업데이트 실패 (무시됨): {e}")

        return result

    def get_events(self, 
                   n: Optional[int] = None,
                   filter_type: Optional[Union[str, List[str]]] = None,
                   limit: Optional[int] = None,
                   reverse: bool = False) -> List[Dict[str, Any]]:
        """로그 이벤트 읽기

        Args:
            n: (deprecated) limit을 사용하세요
            filter_type: 필터링할 이벤트 타입 (문자열 또는 리스트)
            limit: 반환할 최대 이벤트 수
            reverse: True면 오래된 순서로 (기본은 최신순)

        Returns:
            이벤트 리스트
        """
        if not self.log_file.exists():
            return []

        events = []

        # filter_type을 리스트로 변환
        if filter_type is not None:
            if isinstance(filter_type, str):
                filter_types = [filter_type]
            else:
                filter_types = filter_type
        else:
            filter_types = None

        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    # 타입 필터링
                    if filter_types is None or event.get('type') in filter_types:
                        events.append(event)

        # reverse 적용 (오래된 순서로)
        if reverse:
            events = events[::-1]

        # limit 적용 (n보다 우선)
        if limit is not None:
            events = events[:limit]
        elif n is not None:
            # deprecated n 파라미터 지원
            events = events[-n:] if not reverse else events[:n]

        return events

    def get_summary(self) -> Dict[str, Any]:
        """Task 요약 정보 반환"""
        events = self.get_events()
        if not events:
            return {"status": "not_started"}

        # 정보 추출
        task_info = next((e for e in events if e['type'] == 'TASK_INFO'), {})
        todos = next((e for e in events if e['type'] == 'TODO'), {})
        todo_updates = [e for e in events if e['type'] == 'TODO_UPDATE']
        last_context = next((e for e in reversed(events) if e['type'] == 'CONTEXT'), {})
        blockers = [e for e in events if e['type'] == 'BLOCKER']
        complete = next((e for e in events if e['type'] == 'COMPLETE'), None)

        # TODO 진행률 계산
        if todo_updates:
            last_update = todo_updates[-1]
            completed = len(last_update.get('completed', []))
            remaining = len(last_update.get('remaining', []))
            total = completed + remaining
            progress = {"completed": completed, "total": total}
        else:
            progress = {"completed": 0, "total": len(todos.get('items', []))}

        # event_count 계산
        event_count = {
            'total': len(events),
            'by_type': {}
        }

        # 타입별 카운트
        for event in events:
            event_type = event.get('type', 'UNKNOWN')
            event_count['by_type'][event_type] = event_count['by_type'].get(event_type, 0) + 1

        return {
            "task_info": task_info,
            "progress": progress,
            "last_context": last_context.get('value', 'No context'),
            "active_blockers": [b for b in blockers if 'resolved' not in b],
            "completed": complete is not None,
            "complete_summary": complete.get('summary') if complete else None,
            "event_count": event_count  # 추가
        }


# 헬퍼 함수들
def create_task_logger(plan_id: str, task_number: int, task_name: str) -> EnhancedTaskLogger:
    """TaskLogger 생성 헬퍼"""
    return EnhancedTaskLogger(plan_id, task_number, task_name)



def _find_task_jsonl_file(plan_dir: Path, task_num: int, task_id: str, task_title: str) -> Optional[Path]:
    """Task에 해당하는 .jsonl 파일 찾기"""
    # 다양한 파일명 패턴 시도
    # Task 제목을 안전한 파일명으로 변환
    safe_title = task_title.replace(' ', '_').replace('.', '').replace('/', '_')
    safe_title = ''.join(c for c in safe_title if c.isalnum() or c in ['_', '-'])

    patterns = [
        f"{task_num}.*.jsonl",                    # 1.task_name.jsonl
        f"{task_num}_{safe_title}.jsonl",         # 1_task_name.jsonl
        f"{task_num}.{safe_title}.jsonl",         # 1.task_name.jsonl
        f"task_{task_num}.jsonl",                 # task_1.jsonl
        f"*{task_id}*.jsonl",                     # 포함하는 패턴
    ]

    for pattern in patterns:
        matches = list(plan_dir.glob(pattern))
        if matches:
            return matches[0]

    # 특수 케이스 처리
    if task_num == 1:
        # 첫 번째 Task는 종종 다른 이름을 가짐
        special_patterns = [
            "1.flow_system_test.jsonl",
            "1.test*.jsonl"
        ]
        for pattern in special_patterns:
            matches = list(plan_dir.glob(pattern))
            if matches:
                return matches[0]

    return None

def display_plan_tasks(plan_id: str) -> None:
    """Plan의 모든 Task 표시 (개선된 버전 - 부분 매칭 지원)"""
    # 부분 매칭 지원 추가
    plans_dir = Path(".ai-brain/flow/plans")
    plan_dir = None

    if plans_dir.exists():
        # 모든 Plan 디렉토리 검색
        all_plan_dirs = [d for d in plans_dir.iterdir() if d.is_dir()]

        # 부분 매칭 시도
        matches = [d for d in all_plan_dirs if plan_id in d.name]

        if len(matches) == 1:
            # 단일 매칭 - 전체 ID로 변경
            plan_dir = matches[0]
            full_plan_id = matches[0].name
            if plan_id != full_plan_id:
                print(f"✅ Plan 부분 매칭: {plan_id} → {full_plan_id}")
                plan_id = full_plan_id  # 이후 로직을 위해 plan_id 업데이트
        elif len(matches) > 1:
            print(f"🔍 여러 Plan이 '{plan_id}'와 일치합니다:")
            for match in matches[:5]:
                print(f"  - {match.name}")
            print("\n정확한 Plan ID를 입력해주세요.")
            return

    # 매칭 실패하거나 plans_dir가 없으면 기존 방식 시도
    if plan_dir is None:
        plan_dir = Path(f".ai-brain/flow/plans/{plan_id}")

    if not plan_dir.exists():
        print(f"❌ Plan 디렉토리가 없습니다: {plan_id}")
        return

    # tasks.json 파일 읽기 (신규 추가)
    tasks_file = plan_dir / "tasks.json"
    if not tasks_file.exists():
        # .jsonl 파일만 있는 경우를 위한 폴백
        task_files = sorted([f for f in plan_dir.glob("*.jsonl")])
        if not task_files:
            print("📭 등록된 Task가 없습니다.")
            return
        else:
            # 기존 로직으로 폴백 (하위 호환성)
            _display_with_jsonl_only(plan_dir, task_files, plan_id)
            return

    # tasks.json에서 모든 Task 정보 읽기
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
    except Exception as e:
        print(f"❌ tasks.json 읽기 오류: {e}")
        return

    if not tasks_data:
        print("📭 등록된 Task가 없습니다.")
        return

    # 헤더 출력
    print(f"""
╔════════════════════════════════════════╗
║    📋 Plan Tasks: {plan_id[:30]}{'...' if len(plan_id) > 30 else ''}{'    ' * max(0, 30-len(plan_id[:30]))}║
╚════════════════════════════════════════╝
    """)

    # Task를 생성일 기준으로 정렬
    sorted_tasks = sorted(
        tasks_data.items(), 
        key=lambda x: x[1].get('created_at', '')
    )

    # 통계 변수
    total_count = len(sorted_tasks)
    done_count = sum(1 for _, t in sorted_tasks if t.get('status') == 'done')
    in_progress_count = sum(1 for _, t in sorted_tasks if t.get('status') == 'in_progress')
    todo_count = sum(1 for _, t in sorted_tasks if t.get('status') == 'todo')

    # 각 Task 처리
    for i, (task_id, task_info) in enumerate(sorted_tasks, 1):
        # 기본 정보 추출
        title = task_info.get('title', f'Task {i}')
        status = task_info.get('status', 'unknown')
        created_at = task_info.get('created_at', '')[:19]  # YYYY-MM-DD HH:MM:SS만

        # 상태별 아이콘
        status_icons = {
            'done': '✅',
            'in_progress': '🟨',
            'todo': '⬜',
            'blocked': '🔴',
            'unknown': '❓'
        }
        status_icon = status_icons.get(status, '❓')

        # .jsonl 파일 찾기
        jsonl_file = _find_task_jsonl_file(plan_dir, i, task_id, title)


        print(f"""
{status_icon} {i}. {title}
   ID: {task_id}
   상태: {status.upper()}
   생성: {created_at}""")

        if jsonl_file:
            # TaskLogger 정보가 있는 경우 - 상세 정보 표시
            try:
                # 파일명에서 task_name 추출
                parts = jsonl_file.stem.split('.', 1)
                if len(parts) == 2:
                    _, task_name = parts
                else:
                    task_name = jsonl_file.stem

                # TaskLogger로 요약 정보 가져오기
                logger = EnhancedTaskLogger(plan_id, i, task_name)
                summary = logger.get_summary()

                # Task 정보
                task_info_data = summary.get('task_info', {})
                progress = summary.get('progress', {})

                # 추가 정보 표시
                if task_info_data.get('priority'):
                    print(f"   우선순위: {task_info_data.get('priority', 'medium')}")
                if task_info_data.get('estimate'):
                    print(f"   예상시간: {task_info_data.get('estimate', '미정')}")

                print(f"   진행상황: {progress['completed']}/{progress['total']} TODO")

                if summary['last_context'] and summary['last_context'] != 'No context':
                    print(f"   현재상태: {summary['last_context']}")

                # 활성 블로커 표시
                if summary['active_blockers']:
                    blocker = summary['active_blockers'][-1]
                    print(f"   🚨 블로커: {blocker['issue']} ({blocker['severity']})")

                print(f"   TaskLogger: ✅ 작업 기록 있음")

            except Exception as e:
                print(f"   TaskLogger: ⚠️ 정보 읽기 오류")
                # 오류 로깅 제거 - 이미 print로 출력 중
        else:
            # TaskLogger 정보가 없는 경우 - 기본 정보만
            print(f"   TaskLogger: 📭 작업 미시작")
            if task_info.get('updated_at') and task_info['updated_at'] != task_info['created_at']:
                print(f"   수정: {task_info['updated_at'][:19]}")

    # 요약 통계
    print(f"""

📊 요약: 전체 {total_count}개 | ✅ 완료 {done_count}개 | 🟨 진행중 {in_progress_count}개 | ⬜ 대기 {todo_count}개

💡 Task 상세 보기: logger.get_events()
📝 Task 작업하기: logger = EnhancedTaskLogger(plan_id, task_num, task_name)
    """)



def _display_with_jsonl_only(plan_dir: Path, task_files: list, plan_id: str) -> None:
    """기존 방식으로 표시 (하위 호환성)"""
    print(f"""
╔════════════════════════════════════════╗
║    📋 Plan Tasks: {plan_id}            ║
╚════════════════════════════════════════╝
    """)

    for task_file in task_files:
        # 파일명에서 순서와 이름 추출
        parts = task_file.stem.split('.', 1)
        if len(parts) == 2:
            order, task_name = parts
        else:
            order, task_name = "?", task_file.stem

        # 로거로 요약 정보 가져오기
        logger = EnhancedTaskLogger(plan_id, order, task_name)
        summary = logger.get_summary()

        # 상태 아이콘
        if summary.get('completed'):
            status_icon = "✅"
        elif summary['progress']['completed'] > 0:
            status_icon = "🔄"
        else:
            status_icon = "📝"

        # Task 정보 표시
        task_info = summary.get('task_info', {})
        progress = summary['progress']

        print(f"""
{status_icon} {order}. {task_info.get('title', task_name)}
   우선순위: {task_info.get('priority', 'medium')}
   예상시간: {task_info.get('estimate', '미정')}
   진행상황: {progress['completed']}/{progress['total']} TODO
   현재상태: {summary['last_context']}""")

        # 활성 블로커 표시
        if summary['active_blockers']:
            blocker = summary['active_blockers'][-1]
            print(f"   🚨 블로커: {blocker['issue']} ({blocker['severity']})")

    print("""

💡 Task 상세 보기: logger.get_events()
📝 Task 작업하기: logger = EnhancedTaskLogger(plan_id, task_num, task_name)
    """)

# __all__ 정의
__all__ = [
    'EnhancedTaskLogger',
    'create_task_logger',
    'display_plan_tasks'
]
