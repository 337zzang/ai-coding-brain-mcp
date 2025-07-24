"""Flow와 Context 통합을 위한 래퍼 함수들"""
import os
from typing import Dict, Any, Optional
from .context_integration import get_context_integration

def record_flow_action(flow_id: str, action_type: str, details: Dict[str, Any]):
    """Flow 작업을 Context에 기록"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            context = get_context_integration()
            context.record_flow_action(flow_id, action_type, details)
        except Exception as e:
            print(f"Context 기록 실패: {e}")

def record_task_action(flow_id: str, task_id: str, action_type: str, details: Dict[str, Any]):
    """Task 작업을 Context에 기록"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            enhanced_details = {
                "task_id": task_id,
                **details
            }
            record_flow_action(flow_id, f"task_{action_type}", enhanced_details)
        except Exception as e:
            print(f"Task Context 기록 실패: {e}")

def record_plan_action(flow_id: str, plan_id: str, action_type: str, details: Dict[str, Any]):
    """Plan 작업을 Context에 기록"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            enhanced_details = {
                "plan_id": plan_id,
                **details
            }
            record_flow_action(flow_id, f"plan_{action_type}", enhanced_details)
        except Exception as e:
            print(f"Plan Context 기록 실패: {e}")

def record_doc_creation(doc_path: str, doc_type: str, related_to: Optional[Dict[str, str]] = None):
    """문서 생성을 Context에 기록"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            context = get_context_integration()
            details = {
                "doc_type": doc_type,
                "action": "created"
            }
            if related_to:
                details["related_to"] = related_to

            context.record_doc_action(doc_path, "created", details)

            # 관련 문서가 있으면 참조 관계도 기록
            if related_to and "doc_path" in related_to:
                context.record_doc_reference(doc_path, related_to["doc_path"], "derived_from")
        except Exception as e:
            print(f"문서 생성 Context 기록 실패: {e}")

def record_doc_update(doc_path: str, update_type: str, summary: str):
    """문서 수정을 Context에 기록"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            context = get_context_integration()
            details = {
                "update_type": update_type,
                "summary": summary
            }
            context.record_doc_action(doc_path, "updated", details)
        except Exception as e:
            print(f"문서 수정 Context 기록 실패: {e}")

def get_related_docs(doc_path: str, limit: int = 5):
    """관련 문서 추천"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            context = get_context_integration()
            return context.get_related_docs(doc_path, limit)
        except Exception as e:
            print(f"관련 문서 조회 실패: {e}")
    return []

def get_flow_context_summary(flow_id: str) -> Dict[str, Any]:
    """특정 Flow의 Context 요약"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            context = get_context_integration()
            context_file = os.path.join(context.contexts_dir, f"flow_{flow_id}", "context.json")

            if os.path.exists(context_file):
                import json
                with open(context_file, 'r') as f:
                    flow_context = json.load(f)

                return {
                    "total_actions": len(flow_context.get("actions", [])),
                    "statistics": flow_context.get("statistics", {}),
                    "recent_actions": flow_context.get("actions", [])[-10:]  # 최근 10개
                }
        except Exception as e:
            print(f"Flow Context 요약 조회 실패: {e}")

    return {"total_actions": 0, "statistics": {}, "recent_actions": []}

def get_docs_context_summary() -> Dict[str, Any]:
    """문서 Context 요약"""
    if os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
        try:
            context = get_context_integration()
            return context.get_context_summary()["documents"]
        except Exception as e:
            print(f"문서 Context 요약 조회 실패: {e}")

    return {"total_count": 0, "categories": {}, "recent_activities": 0}

# FlowManagerUnified에서 쉽게 사용할 수 있는 데코레이터
def with_context(action_type: str):
    """Context 기록을 위한 데코레이터"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            # 성공 시 Context 기록
            if result and result.get('ok'):
                try:
                    flow_id = getattr(self, 'current_flow_id', None)
                    if flow_id and os.environ.get('CONTEXT_SYSTEM', 'off') == 'on':
                        details = {
                            "args": str(args)[:100],  # 너무 길지 않게
                            "result": str(result.get('data', ''))[:100]
                        }
                        record_flow_action(flow_id, action_type, details)
                except:
                    pass  # Context 기록 실패는 무시

            return result
        return wrapper
    return decorator
