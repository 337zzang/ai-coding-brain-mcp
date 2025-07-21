"""
Flow Project v2 - Context Manager
AI 세션 간 완벽한 컨텍스트 복원을 위한 시스템
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime


class ContextManager:
    """세션 컨텍스트 관리자"""

    def __init__(self, flow_manager):
        self.fm = flow_manager
        self.context_path = self.fm._get_file_path('context.json')
        self.max_history_items = 50  # 각 리스트의 최대 아이템 수

    def save_context(self, additional_data: Dict = None) -> Dict:
        """현재 세션 컨텍스트 저장"""
        context = self._build_current_context()

        # 추가 데이터 병합
        if additional_data:
            self._merge_context(context, additional_data)

        # 크기 제한 적용
        self._trim_context(context)

        # 저장
        try:
            with open(self.context_path, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
            return {'ok': True, 'data': context}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def _build_current_context(self) -> Dict:
        """현재 상태에서 컨텍스트 구축"""
        # 기존 컨텍스트 로드 또는 새로 생성
        if os.path.exists(self.context_path):
            try:
                with open(self.context_path, 'r', encoding='utf-8') as f:
                    context = json.load(f)
            except:
                context = self._create_default_context()
        else:
            context = self._create_default_context()

        # 현재 상태 업데이트
        active_plan = self.fm.get_active_plan()
        if active_plan:
            context['memory']['active_plan_id'] = active_plan.id

            # 현재 작업 중인 태스크 찾기
            in_progress_tasks = [t for t in active_plan.tasks 
                               if t.status == 'in_progress']
            if in_progress_tasks:
                # 가장 최근 업데이트된 태스크
                current_task = max(in_progress_tasks, 
                                 key=lambda t: t.updated_at)
                context['memory']['active_task_id'] = current_task.id

        # 타임스탬프 업데이트
        context['updated_at'] = datetime.now().isoformat()

        return context

    def _create_default_context(self) -> Dict:
        """기본 컨텍스트 생성"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "memory": {
                "active_plan_id": "",
                "active_task_id": None,
                "recent_decisions": [],
                "open_files": [],
                "modified_files": [],
                "terminal_commands": [],
                "error_context": []
            },
            "conversation": {
                "last_topics": [],
                "key_insights": [],
                "user_preferences": {},
                "clarifications": []
            },
            "project": {
                "tech_stack": [],
                "architecture_decisions": [],
                "code_patterns": {},
                "naming_conventions": {}
            }
        }

    def load_context(self) -> Optional[Dict]:
        """저장된 컨텍스트 로드"""
        if not os.path.exists(self.context_path):
            return None

        try:
            with open(self.context_path, 'r', encoding='utf-8') as f:
                context = json.load(f)
            return context
        except Exception as e:
            print(f"컨텍스트 로드 실패: {e}")
            return None

    def add_decision(self, decision: str, rationale: str = ""):
        """중요 결정사항 추가"""
        context = self._build_current_context()

        decision_entry = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "rationale": rationale,
            "plan_id": context['memory'].get('active_plan_id'),
            "task_id": context['memory'].get('active_task_id')
        }

        context['memory']['recent_decisions'].append(decision_entry)
        self.save_context(context)

    def add_error_resolution(self, error: str, solution: str, 
                           file_path: str = None):
        """에러 해결 과정 기록"""
        context = self._build_current_context()

        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "solution": solution,
            "file_path": file_path,
            "success": True
        }

        context['memory']['error_context'].append(error_entry)
        self.save_context(context)

    def update_open_files(self, files: List[str]):
        """열린 파일 목록 업데이트"""
        context = self._build_current_context()
        context['memory']['open_files'] = files
        self.save_context(context)

    def add_terminal_command(self, command: str):
        """터미널 명령어 기록"""
        context = self._build_current_context()
        context['memory']['terminal_commands'].append({
            "timestamp": datetime.now().isoformat(),
            "command": command
        })
        self.save_context(context)

    def _merge_context(self, context: Dict, additional: Dict):
        """컨텍스트 병합"""
        for key, value in additional.items():
            if key in context and isinstance(context[key], dict) and isinstance(value, dict):
                context[key].update(value)
            else:
                context[key] = value

    def _trim_context(self, context: Dict):
        """컨텍스트 크기 제한"""
        # 각 리스트 필드를 최대 크기로 제한
        memory = context.get('memory', {})

        for field in ['recent_decisions', 'terminal_commands', 'error_context']:
            if field in memory and isinstance(memory[field], list):
                memory[field] = memory[field][-self.max_history_items:]

    def generate_session_summary(self) -> str:
        """세션 재개 시 표시할 요약 생성"""
        context = self.load_context()
        if not context:
            return "새로운 세션입니다."

        summary_parts = []

        # 1. 시간 정보
        last_update = context.get('updated_at', '')
        if last_update:
            try:
                last_time = datetime.fromisoformat(last_update)
                time_diff = datetime.now() - last_time

                if time_diff.days > 0:
                    time_str = f"{time_diff.days}일 전"
                elif time_diff.seconds > 3600:
                    time_str = f"{time_diff.seconds // 3600}시간 전"
                else:
                    time_str = f"{time_diff.seconds // 60}분 전"

                summary_parts.append(f"📅 마지막 작업: {time_str}")
            except:
                pass

        # 2. 활성 Plan/Task
        memory = context.get('memory', {})
        if memory.get('active_plan_id'):
            plan = self.fm.get_plan(memory['active_plan_id'])
            if plan:
                summary_parts.append(f"\n📋 활성 Plan: {plan.title}")
                summary_parts.append(f"   진행률: {plan.progress}%")

                if memory.get('active_task_id'):
                    task = plan.get_task(memory['active_task_id'])
                    if task:
                        summary_parts.append(f"   현재 작업: {task.title}")

        # 3. 최근 결정사항
        decisions = memory.get('recent_decisions', [])
        if decisions:
            summary_parts.append("\n💡 최근 결정사항:")
            for decision in decisions[-3:]:  # 최근 3개
                summary_parts.append(f"   • {decision['decision']}")

        # 4. 열린 파일
        open_files = memory.get('open_files', [])
        if open_files:
            summary_parts.append(f"\n📂 작업 중인 파일: {len(open_files)}개")
            for file in open_files[:5]:
                summary_parts.append(f"   • {file}")

        # 5. 해결한 에러
        errors = memory.get('error_context', [])
        if errors:
            resolved_count = sum(1 for e in errors if e.get('success'))
            summary_parts.append(f"\n✅ 해결한 오류: {resolved_count}개")

        # 6. 다음 작업 제안
        suggestions = self._generate_next_steps(context)
        if suggestions:
            summary_parts.append("\n🎯 다음 작업 제안:")
            for suggestion in suggestions:
                summary_parts.append(f"   → {suggestion}")

        return "\n".join(summary_parts)

    def _generate_next_steps(self, context: Dict) -> List[str]:
        """컨텍스트 기반 다음 작업 제안"""
        suggestions = []
        memory = context.get('memory', {})

        # 활성 태스크가 있으면
        if memory.get('active_task_id'):
            task_id = memory['active_task_id']
            plan_id = memory.get('active_plan_id')

            if plan_id and plan_id in self.fm.plans:
                plan = self.fm.plans[plan_id]
                task = plan.get_task(task_id)

                if task and task.status == 'in_progress':
                    suggestions.append(f"'{task.title}' 작업 계속하기")

                    # 의존성 체크
                    blocked_by = []
                    for dep_id in task.dependencies:
                        dep_task = plan.get_task(dep_id)
                        if dep_task and dep_task.status != 'completed':
                            blocked_by.append(dep_task.title)

                    if blocked_by:
                        suggestions.append(f"먼저 완료 필요: {', '.join(blocked_by)}")

        # 최근 에러가 있으면
        recent_errors = memory.get('error_context', [])
        if recent_errors and not recent_errors[-1].get('success'):
            suggestions.append("이전 오류 해결 재시도")

        return suggestions[:3]  # 최대 3개 제안
