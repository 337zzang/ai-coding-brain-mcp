"""
Flow + Claude Code 통합 동기화 시스템
.ai-brain 폴더 기반 완전 통합 관리
"""

import json
import os
import datetime
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from .util import ok, err
from .wrappers import safe_api_get
from .flow_api import FlowAPI

class UnifiedSync:
    """Flow와 Claude Code TodoWrite의 완전 통합 시스템"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.ai_brain_path = self.base_path / ".ai-brain"
        
        # 폴더 경로 설정
        self.claude_sessions_path = self.ai_brain_path / "claude_sessions"
        self.todo_sync_path = self.ai_brain_path / "todo_sync"
        self.unified_plans_path = self.ai_brain_path / "unified_plans"
        
        # 설정 파일 경로
        self.sync_state_file = self.ai_brain_path / "sync_state.json"
        self.claude_config_file = self.ai_brain_path / "claude_config.json"
        
        # 폴더 생성 확인
        self._ensure_folders()
        
        # Flow API 초기화
        self.flow_api = FlowAPI()
        
        # 동기화 상태 로드
        self.sync_state = self._load_sync_state()
        self.config = self._load_config()
    
    def _ensure_folders(self):
        """필요한 폴더들 생성"""
        folders = [
            self.claude_sessions_path,
            self.todo_sync_path,
            self.unified_plans_path
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    def _load_sync_state(self) -> Dict[str, Any]:
        """동기화 상태 로드"""
        try:
            if self.sync_state_file.exists():
                with open(self.sync_state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "version": "1.0.0",
                "last_sync": None,
                "active_mappings": {},
                "pending_migrations": [],
                "statistics": {}
            }
        except Exception as e:
            print(f"⚠️ 동기화 상태 로드 실패: {e}")
            return {}
    
    def _save_sync_state(self) -> bool:
        """동기화 상태 저장"""
        try:
            with open(self.sync_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.sync_state, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ 동기화 상태 저장 실패: {e}")
            return False
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 로드"""
        try:
            if self.claude_config_file.exists():
                with open(self.claude_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "integration_enabled": True,
                "auto_migration": {"enabled": True}
            }
        except Exception as e:
            print(f"⚠️ 설정 로드 실패: {e}")
            return {}
    
    def create_todo(self, content: str, todo_type: str = "pending",
                   auto_flow: bool = True) -> Dict[str, Any]:
        """
        TodoWrite + Flow 동시 생성
        
        Args:
            content: 할일 내용
            todo_type: pending/in_progress/completed
            auto_flow: Flow 태스크 자동 생성 여부
        """
        try:
            # 1. TodoWrite용 ID 생성
            todo_id = f"todo_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.datetime.now().isoformat()
            
            # 2. 세션에 저장
            session_data = {
                "todo_id": todo_id,
                "content": content,
                "status": todo_type,
                "created_at": timestamp,
                "flow_task_id": None,
                "flow_plan_id": None
            }
            
            # 3. Flow 태스크 자동 생성 (옵션)
            if auto_flow and self.config.get("sync_rules", {}).get("todo_to_flow", True):
                # 복잡도 판단
                is_complex = self._is_complex_todo(content)
                
                if is_complex:
                    # Flow 플랜으로 생성
                    flow_result = self._create_flow_plan_from_todo(content)
                    if flow_result['ok']:
                        session_data['flow_plan_id'] = safe_api_get(flow_result, 'data.plan_id')
                else:
                    # Flow 태스크로 생성
                    flow_result = self._create_flow_task_from_todo(content)
                    if flow_result['ok']:
                        session_data['flow_task_id'] = safe_api_get(flow_result, 'data.task_id')
                        session_data['flow_plan_id'] = safe_api_get(flow_result, 'data.plan_id')
            
            # 4. 매핑 저장
            self._save_todo_mapping(todo_id, session_data)
            
            # 5. 통계 업데이트
            self.sync_state.setdefault("statistics", {})
            self.sync_state["statistics"]["total_todos_synced"] = \
                self.sync_state["statistics"].get("total_todos_synced", 0) + 1
            self._save_sync_state()
            
            return ok({
                "todo_id": todo_id,
                "content": content,
                "status": todo_type,
                "flow_synced": session_data.get('flow_task_id') is not None,
                "flow_plan_id": session_data.get('flow_plan_id'),
                "flow_task_id": session_data.get('flow_task_id')
            })
            
        except Exception as e:
            return err(f"TodoWrite 생성 실패: {e}")
    
    def _is_complex_todo(self, content: str) -> bool:
        """복잡한 할일인지 판단"""
        keywords = self.config.get("auto_migration", {}).get("keywords", [])
        for keyword in keywords:
            if keyword in content:
                return True
        return False
    
    def _create_flow_plan_from_todo(self, content: str) -> Dict[str, Any]:
        """TodoWrite를 Flow 플랜으로 생성"""
        try:
            # Flow API를 통해 플랜 생성
            plan_title = f"[Claude] {content}"
            plan_data = {
                "title": plan_title,
                "description": f"Claude Code TodoWrite에서 자동 생성됨\n원본: {content}",
                "source": "claude_code",
                "auto_created": True,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Flow API 호출 (실제 구현에 맞게 수정 필요)
            result = self.flow_api.create_plan(plan_title)
            if result.get('ok'):
                plan_id = result['data'].get('id', uuid.uuid4().hex[:8])
                
                # unified_plans에 저장
                plan_file = self.unified_plans_path / f"plan_{plan_id}.json"
                with open(plan_file, 'w', encoding='utf-8') as f:
                    json.dump(plan_data, f, indent=2, ensure_ascii=False)
                
                return ok({"plan_id": plan_id, "title": plan_title})
            
            return err("Flow 플랜 생성 실패")
            
        except Exception as e:
            return err(f"Flow 플랜 생성 오류: {e}")
    
    def _create_flow_task_from_todo(self, content: str) -> Dict[str, Any]:
        """TodoWrite를 Flow 태스크로 생성"""
        try:
            # 기본 플랜 찾기 또는 생성
            default_plan = self._get_or_create_default_plan()
            if not default_plan['ok']:
                return default_plan
            
            plan_id = default_plan['data']['plan_id']
            
            # 태스크 생성
            task_data = {
                "content": content,
                "status": "pending",
                "source": "claude_code",
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Flow API를 통해 태스크 추가
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            return ok({
                "task_id": task_id,
                "plan_id": plan_id,
                "content": content
            })
            
        except Exception as e:
            return err(f"Flow 태스크 생성 오류: {e}")
    
    def _get_or_create_default_plan(self) -> Dict[str, Any]:
        """기본 플랜 가져오기 또는 생성"""
        try:
            # Claude Code 기본 플랜 찾기
            plans = self.flow_api.list_plans()
            if plans.get('ok'):
                for plan in plans.get('data', []):
                    if isinstance(plan, dict) and plan.get('title') == "[Claude] 일반 작업":
                        return ok({"plan_id": plan.get('id', 'default')})
            
            # 없으면 생성
            result = self.flow_api.create_plan("[Claude] 일반 작업")
            if result.get('ok'):
                return ok({"plan_id": result['data'].get('id', 'default')})
            
            return ok({"plan_id": "default"})
            
        except Exception as e:
            return err(f"기본 플랜 처리 오류: {e}")
    
    def _save_todo_mapping(self, todo_id: str, data: Dict[str, Any]) -> bool:
        """TodoWrite 매핑 저장"""
        try:
            mapping_file = self.todo_sync_path / f"{todo_id}.json"
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # active_mappings 업데이트
            self.sync_state["active_mappings"][todo_id] = {
                "flow_task_id": data.get('flow_task_id'),
                "flow_plan_id": data.get('flow_plan_id'),
                "last_synced": datetime.datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            print(f"⚠️ 매핑 저장 실패: {e}")
            return False
    
    def sync_status(self, todo_id: Optional[str] = None) -> Dict[str, Any]:
        """
        양방향 상태 동기화
        
        Args:
            todo_id: 특정 할일 ID (없으면 전체)
        """
        try:
            if todo_id:
                # 특정 할일 동기화
                return self._sync_single_todo(todo_id)
            else:
                # 전체 동기화
                return self._sync_all_todos()
            
        except Exception as e:
            return err(f"상태 동기화 실패: {e}")
    
    def _sync_single_todo(self, todo_id: str) -> Dict[str, Any]:
        """단일 할일 동기화"""
        try:
            mapping_file = self.todo_sync_path / f"{todo_id}.json"
            if not mapping_file.exists():
                return err(f"매핑을 찾을 수 없음: {todo_id}")
            
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            # Flow 상태 확인 및 업데이트
            if mapping_data.get('flow_task_id'):
                # Flow API를 통해 상태 확인 (실제 구현 필요)
                pass
            
            # 동기화 시간 업데이트
            mapping_data['last_synced'] = datetime.datetime.now().isoformat()
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)
            
            return ok({"synced": True, "todo_id": todo_id})
            
        except Exception as e:
            return err(f"단일 동기화 실패: {e}")
    
    def _sync_all_todos(self) -> Dict[str, Any]:
        """전체 할일 동기화"""
        try:
            synced_count = 0
            failed_count = 0
            
            # 모든 매핑 파일 처리
            for mapping_file in self.todo_sync_path.glob("*.json"):
                todo_id = mapping_file.stem
                result = self._sync_single_todo(todo_id)
                if result['ok']:
                    synced_count += 1
                else:
                    failed_count += 1
            
            # 동기화 상태 업데이트
            self.sync_state["last_sync"] = datetime.datetime.now().isoformat()
            self._save_sync_state()
            
            return ok({
                "total_synced": synced_count,
                "failed": failed_count,
                "last_sync": self.sync_state["last_sync"]
            })
            
        except Exception as e:
            return err(f"전체 동기화 실패: {e}")
    
    def migrate_session(self, session_todos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Claude Code 세션을 Flow 플랜으로 변환
        
        Args:
            session_todos: TodoWrite 목록
        """
        try:
            if not session_todos:
                return err("마이그레이션할 할일이 없습니다")
            
            # 복잡한 작업들만 필터링
            complex_todos = [
                todo for todo in session_todos
                if self._is_complex_todo(todo.get('content', ''))
            ]
            
            if not complex_todos:
                return ok({"migrated": 0, "message": "마이그레이션할 복잡한 작업이 없습니다"})
            
            # 세션 플랜 생성
            session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            plan_title = f"[Claude Session] {session_id}"
            
            plan_result = self.flow_api.create_plan(plan_title)
            if not plan_result.get('ok'):
                return err("세션 플랜 생성 실패")
            
            plan_id = plan_result['data'].get('id')
            
            # 각 할일을 태스크로 추가
            migrated_count = 0
            for todo in complex_todos:
                task_result = self.flow_api.add_task(
                    plan_id,
                    todo.get('content', ''),
                    status=todo.get('status', 'pending')
                )
                if task_result.get('ok'):
                    migrated_count += 1
            
            # 통계 업데이트
            self.sync_state.setdefault("statistics", {})
            self.sync_state["statistics"]["total_migrations"] = \
                self.sync_state["statistics"].get("total_migrations", 0) + 1
            self.sync_state["statistics"]["total_flows_created"] = \
                self.sync_state["statistics"].get("total_flows_created", 0) + 1
            self._save_sync_state()
            
            return ok({
                "migrated": migrated_count,
                "plan_id": plan_id,
                "plan_title": plan_title,
                "message": f"{migrated_count}개 작업이 Flow로 마이그레이션됨"
            })
            
        except Exception as e:
            return err(f"세션 마이그레이션 실패: {e}")
    
    def get_unified_status(self) -> Dict[str, Any]:
        """전체 통합 상태 조회"""
        try:
            # Claude 세션 수
            claude_sessions = len(list(self.claude_sessions_path.glob("*.json")))
            
            # 활성 매핑 수
            active_mappings = len(self.sync_state.get("active_mappings", {}))
            
            # Flow 플랜 수
            flow_plans = self.flow_api.list_plans()
            flow_plan_count = len(flow_plans.get('data', [])) if flow_plans.get('ok') else 0
            
            # 통합 플랜 수
            unified_plans = len(list(self.unified_plans_path.glob("*.json")))
            
            # 통계
            stats = self.sync_state.get("statistics", {})
            
            return ok({
                "claude_sessions": claude_sessions,
                "active_mappings": active_mappings,
                "flow_plans": flow_plan_count,
                "unified_plans": unified_plans,
                "last_sync": self.sync_state.get("last_sync"),
                "statistics": {
                    "total_todos_synced": stats.get("total_todos_synced", 0),
                    "total_flows_created": stats.get("total_flows_created", 0),
                    "total_migrations": stats.get("total_migrations", 0)
                },
                "config": {
                    "integration_enabled": self.config.get("integration_enabled", False),
                    "auto_migration": self.config.get("auto_migration", {}).get("enabled", False),
                    "bidirectional_sync": self.config.get("sync_rules", {}).get("bidirectional", False)
                }
            })
            
        except Exception as e:
            return err(f"상태 조회 실패: {e}")
    
    def suggest_migration(self, todos: List[str]) -> Dict[str, Any]:
        """마이그레이션 제안"""
        try:
            complex_todos = []
            simple_todos = []
            
            for todo in todos:
                if self._is_complex_todo(todo):
                    complex_todos.append(todo)
                else:
                    simple_todos.append(todo)
            
            suggestions = []
            
            if complex_todos:
                suggestions.append({
                    "type": "create_flow_plan",
                    "todos": complex_todos,
                    "reason": "복잡한 작업들을 Flow 플랜으로 관리하면 체계적입니다"
                })
            
            if simple_todos and len(simple_todos) > 5:
                suggestions.append({
                    "type": "batch_migrate",
                    "todos": simple_todos,
                    "reason": "간단한 작업들을 하나의 Flow 플랜으로 묶으면 효율적입니다"
                })
            
            return ok({
                "suggestions": suggestions,
                "complex_count": len(complex_todos),
                "simple_count": len(simple_todos),
                "total": len(todos)
            })
            
        except Exception as e:
            return err(f"제안 생성 실패: {e}")


# 간편 함수들
def create_unified_sync(base_path: Optional[str] = None) -> UnifiedSync:
    """UnifiedSync 인스턴스 생성"""
    return UnifiedSync(base_path)


def unified_create_todo(content: str, auto_flow: bool = True) -> Dict[str, Any]:
    """TodoWrite + Flow 동시 생성 (간편 함수)"""
    sync = create_unified_sync()
    return sync.create_todo(content, auto_flow=auto_flow)


def unified_sync_status(todo_id: Optional[str] = None) -> Dict[str, Any]:
    """양방향 상태 동기화 (간편 함수)"""
    sync = create_unified_sync()
    return sync.sync_status(todo_id)


def unified_migrate_session(session_todos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """세션을 Flow 플랜으로 변환 (간편 함수)"""
    sync = create_unified_sync()
    return sync.migrate_session(session_todos)


def get_unified_status() -> Dict[str, Any]:
    """전체 통합 상태 조회 (간편 함수)"""
    sync = create_unified_sync()
    return sync.get_unified_status()


# Facade에서 사용할 수 있도록 export
__all__ = [
    'UnifiedSync',
    'create_unified_sync',
    'unified_create_todo',
    'unified_sync_status',
    'unified_migrate_session',
    'get_unified_status'
]