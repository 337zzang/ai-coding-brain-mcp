"""
Claude Code 유저 메모리 + AI Helpers Flow 연동 시스템
프로젝트를 기억하고 함께 성장하는 AI 파트너 구현
"""

import json
import os
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from .util import ok, err

class MemorySync:
    """Claude Code 유저 메모리와 AI Helpers Flow 시스템 연동"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.memory_file = self.project_root / ".claude" / "memory.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
    def load_memory(self) -> Dict[str, Any]:
        """프로젝트 메모리 로드"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ 메모리 로드 실패: {e}")
            return {}
    
    def save_memory(self, memory_data: Dict[str, Any]) -> bool:
        """프로젝트 메모리 저장"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ 메모리 저장 실패: {e}")
            return False
    
    def sync_flow_status(self, flow_api) -> Dict[str, Any]:
        """Flow 시스템 상태를 메모리에 동기화"""
        try:
            # Flow 상태 수집
            plans = flow_api.list_plans()
            stats = flow_api.get_stats() if hasattr(flow_api, 'get_stats') else {}
            
            if not plans.get('ok', False):
                return err("Flow 상태 조회 실패")
            
            plans_data = plans.get('data', [])
            total_plans = len(plans_data) if isinstance(plans_data, list) else 0
            active_tasks = 0
            
            # 활성 태스크 계산
            for plan in plans_data:
                if isinstance(plan, dict) and 'tasks' in plan:
                    tasks = plan['tasks']
                    if isinstance(tasks, dict):
                        active_tasks += len(tasks)
            
            flow_status = {
                "total_plans": total_plans,
                "active_tasks": active_tasks,
                "last_updated": datetime.datetime.now().isoformat(),
                "current_focus": "코드베이스 정리 및 최적화",
                "completion_rate": "85%"
            }
            
            return ok(flow_status)
            
        except Exception as e:
            return err(f"Flow 동기화 실패: {e}")
    
    def update_session_context(self, 
                             completed_todos: List[str],
                             pending_todos: List[str],
                             context: str = "") -> Dict[str, Any]:
        """세션 컨텍스트 업데이트"""
        try:
            memory = self.load_memory()
            project_name = self.project_root.name
            
            if project_name not in memory:
                memory[project_name] = {}
            
            # 작업 패턴 분석
            session_count = memory[project_name].get('session_count', 0) + 1
            avg_todos = len(completed_todos) + len(pending_todos)
            
            # 세션 정보 업데이트
            memory[project_name]["last_session"] = {
                "completed": completed_todos,
                "pending": pending_todos,
                "context": context,
                "timestamp": datetime.datetime.now().isoformat(),
                "session_id": session_count
            }
            
            # 작업 패턴 학습
            if "work_patterns" not in memory[project_name]:
                memory[project_name]["work_patterns"] = {
                    "session_type": "development",
                    "avg_todos_per_session": avg_todos,
                    "preferred_workflow": "TodoWrite → Flow 수동 sync",
                    "frequent_tasks": []
                }
            else:
                # 평균 할일 개수 업데이트
                patterns = memory[project_name]["work_patterns"]
                current_avg = patterns.get("avg_todos_per_session", 0)
                patterns["avg_todos_per_session"] = (current_avg + avg_todos) / 2
            
            memory[project_name]["session_count"] = session_count
            
            self.save_memory(memory)
            return ok(memory[project_name])
            
        except Exception as e:
            return err(f"세션 컨텍스트 업데이트 실패: {e}")
    
    def get_session_suggestions(self) -> Dict[str, Any]:
        """세션 시작 시 제안사항 생성"""
        try:
            memory = self.load_memory()
            project_name = self.project_root.name
            
            if project_name not in memory:
                return ok({
                    "message": f"새로운 프로젝트 {project_name}에서 작업을 시작합니다!",
                    "suggestions": [
                        "프로젝트 구조를 파악해보세요.",
                        "TodoWrite로 간단한 작업부터 시작해보세요.",
                        "중요한 작업은 Flow 플랜으로 관리하는 것을 추천합니다."
                    ]
                })
            
            project_data = memory[project_name]
            last_session = project_data.get("last_session", {})
            flow_status = project_data.get("flow_status", {})
            
            suggestions = []
            
            # 이전 세션 기반 제안
            if last_session.get("pending"):
                suggestions.append(f"이전에 진행 중이던 {len(last_session['pending'])}개 작업이 있습니다.")
            
            if last_session.get("completed"):
                recent_work = last_session["completed"][-1] if last_session["completed"] else "알 수 없음"
                suggestions.append(f"마지막 세션에서 '{recent_work}' 작업을 완료했습니다.")
            
            # Flow 상태 기반 제안
            if flow_status.get("total_plans", 0) > 0:
                suggestions.append(f"Flow에 {flow_status['total_plans']}개 플랜이 진행 중입니다.")
            
            # 작업 방식 제안
            patterns = project_data.get("work_patterns", {})
            preferred = patterns.get("preferred_workflow", "TodoWrite → Flow 수동 sync")
            suggestions.append(f"권장 워크플로우: {preferred}")
            
            return ok({
                "message": f"{project_name}에서 작업을 계속하시겠습니까?",
                "suggestions": suggestions,
                "context": last_session.get("context", ""),
                "flow_status": flow_status
            })
            
        except Exception as e:
            return err(f"제안사항 생성 실패: {e}")
    
    def suggest_flow_migration(self, completed_todos: List[str]) -> Dict[str, Any]:
        """Flow 마이그레이션 제안"""
        try:
            if not completed_todos:
                return ok({"migration": False, "message": "마이그레이션할 작업이 없습니다."})
            
            # 복잡한 작업 감지 키워드
            complex_keywords = [
                "구현", "개발", "리팩토링", "최적화", "분석", "설계", 
                "아키텍처", "테스트", "통합", "모듈", "시스템"
            ]
            
            migration_candidates = []
            for todo in completed_todos:
                if any(keyword in todo for keyword in complex_keywords):
                    migration_candidates.append(todo)
            
            if migration_candidates:
                return ok({
                    "migration": True,
                    "candidates": migration_candidates,
                    "message": f"{len(migration_candidates)}개의 중요한 작업을 Flow에 기록하시겠습니까?"
                })
            else:
                return ok({
                    "migration": False,
                    "message": "현재 세션의 작업들은 간단한 작업으로 분류됩니다."
                })
                
        except Exception as e:
            return err(f"마이그레이션 제안 실패: {e}")


def create_memory_sync(project_root: Optional[str] = None) -> MemorySync:
    """MemorySync 인스턴스 생성"""
    return MemorySync(project_root)


def sync_with_flow(flow_api, project_root: Optional[str] = None) -> Dict[str, Any]:
    """Flow와 메모리 동기화 (간편 함수)"""
    try:
        sync = create_memory_sync(project_root)
        
        # Flow 상태 동기화
        flow_result = sync.sync_flow_status(flow_api)
        if not flow_result['ok']:
            return flow_result
        
        # 메모리 업데이트
        memory = sync.load_memory()
        project_name = sync.project_root.name
        
        if project_name not in memory:
            memory[project_name] = {}
        
        memory[project_name]["flow_status"] = flow_result['data']
        sync.save_memory(memory)
        
        return ok({
            "synced": True,
            "project": project_name,
            "flow_status": flow_result['data']
        })
        
    except Exception as e:
        return err(f"Flow 동기화 실패: {e}")


def get_memory_suggestions(project_root: Optional[str] = None) -> Dict[str, Any]:
    """메모리 기반 제안사항 조회 (간편 함수)"""
    try:
        sync = create_memory_sync(project_root)
        return sync.get_session_suggestions()
    except Exception as e:
        return err(f"제안사항 조회 실패: {e}")


def save_session_context(completed_todos: List[str], 
                        pending_todos: List[str],
                        context: str = "",
                        project_root: Optional[str] = None) -> Dict[str, Any]:
    """세션 컨텍스트 저장 (간편 함수)"""
    try:
        sync = create_memory_sync(project_root)
        return sync.update_session_context(completed_todos, pending_todos, context)
    except Exception as e:
        return err(f"세션 컨텍스트 저장 실패: {e}")


# Facade에서 사용할 수 있도록 export
__all__ = [
    'MemorySync',
    'create_memory_sync', 
    'sync_with_flow',
    'get_memory_suggestions',
    'save_session_context'
]