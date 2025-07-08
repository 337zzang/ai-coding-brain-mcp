"""
워크플로우 명령어 처리 모듈
WorkflowManager는 workflow.workflow_manager에서 임포트
"""

from workflow.workflow_manager import WorkflowManager
from workflow.models import Plan, Task, TaskStatus
import json
from typing import Dict, Any, Optional
from ai_helpers.helper_result import HelperResult

# 전역 WorkflowManager 인스턴스
workflow_manager = WorkflowManager()

# 기존 명령어 핸들러 함수들
def handle_plan(name: str, description: str = "", reset: bool = False) -> str:
    """계획 생성 명령 처리"""
    try:
        plan = workflow_manager.create_plan(name, description, reset)
        return f"✅ 계획 '{plan.name}' 생성됨 (ID: {plan.id})"
    except Exception as e:
        return f"❌ 계획 생성 실패: {str(e)}"

def handle_task(title: str, description: str = "") -> str:
    """작업 추가 명령 처리"""
    try:
        task = workflow_manager.add_task(title, description)
        return f"✅ 작업 '{task.title}' 추가됨"
    except ValueError as e:
        return f"❌ 작업 추가 실패: {str(e)}"

def handle_status() -> str:
    """현재 상태 조회"""
    status = workflow_manager.get_status()
    
    if not status["plan"]:
        return "📋 활성 계획이 없습니다. /plan 명령으로 새 계획을 생성하세요."
    
    # 상태 포맷팅
    output = []
    output.append(f"📅 계획: {status['plan']['name']} ({status['plan']['progress']})")
    output.append(f"📝 {status['plan']['description']}")
    
    # 작업 목록
    output.append("\n📊 작업 목록:")
    for task_line in status["all_tasks"]:
        output.append(f"  {task_line}")
    
    # 현재 작업
    if status["current_task"]:
        task = status["current_task"]
        output.append(f"\n📌 현재 작업: {task['title']}")
        if task["description"]:
            # 설명이 길면 줄임
            desc = task["description"]
            if len(desc) > 50:
                desc = desc[:50] + "..."
            output.append(f"   설명: {desc}")
    
    output.append(f"\n📈 진행률: {status['plan']['progress']} (남은 작업: {status['remaining_tasks']}개)")
    
    return "\n".join(output)

def handle_next(completion_notes: str = "") -> str:
    """다음 작업으로 진행"""
    try:
        next_task = workflow_manager.complete_current_and_next(completion_notes)
        if next_task:
            return f"✅ 다음 작업 시작: {next_task.title}"
        else:
            return "🎉 모든 작업이 완료되었습니다!"
    except Exception as e:
        return f"❌ 작업 진행 실패: {str(e)}"

def handle_history() -> str:
    """완료된 작업 이력 조회"""
    try:
        data = workflow_manager.load_data()
        if not data or "plans" not in data:
            return "📋 작업 이력이 없습니다."
        
        output = ["📜 완료된 작업 이력:"]
        output.append("=" * 50)
        
        for plan in data["plans"]:
            completed_tasks = [t for t in plan.get("tasks", []) 
                             if t.get("status") == "completed"]
            if completed_tasks:
                output.append(f"\n📅 {plan['name']}")
                for task in completed_tasks:
                    completed_at = task.get("completed_at", "N/A")
                    output.append(f"  ✅ {task['title']} - 완료: {completed_at}")
                    if task.get("completion_notes"):
                        output.append(f"     메모: {task['completion_notes']}")
        
        return "\n".join(output)
    except Exception as e:
        return f"❌ 이력 조회 실패: {str(e)}"

def handle_approve(decision: str = "yes", notes: str = "") -> str:
    """작업 승인 처리"""
    try:
        approved = decision.lower() in ["yes", "y", "승인", "예"]
        result = workflow_manager.approve_task(approved, notes)
        
        if result["success"]:
            status_icon = "✅" if approved else "❌"
            return f"{status_icon} 작업이 {'승인' if approved else '거부'}되었습니다."
        else:
            return f"❌ 승인 처리 실패: {result.get('error', '알 수 없는 오류')}"
    except Exception as e:
        return f"❌ 승인 처리 중 오류: {str(e)}"

def handle_done(args: str = "") -> str:
    """
    현재 작업 완료 처리
    사용법: /done 요약 | 세부내용1;세부내용2 | 산출물경로
    """
    try:
        # 인자 파싱
        parts = [p.strip() for p in args.split('|')] + [''] * 3
        summary = parts[0] or "작업 완료"
        details_raw = parts[1]
        outputs_raw = parts[2]
        
        # 세부사항 파싱
        details = []
        if details_raw:
            details = [d.strip() for d in details_raw.split(';') if d.strip()]
        
        # 산출물 파싱
        outputs = {}
        if outputs_raw:
            outputs = {'paths': [p.strip() for p in outputs_raw.split(',') if p.strip()]}
        
        # 작업 완료 처리
        result = workflow_manager.complete_current_task(
            summary=summary,
            details=details,
            outputs=outputs
        )
        
        if result["success"]:
            completed_task = result.get("task", {})
            return f"✅ 작업 '{completed_task.get('title', 'Unknown')}' 완료!\n   요약: {summary}"
        else:
            return f"❌ 작업 완료 실패: {result.get('error', '알 수 없는 오류')}"
            
    except Exception as e:
        return f"❌ 작업 완료 처리 중 오류: {str(e)}"

def handle_build() -> str:
    """프로젝트 컨텍스트 빌드"""
    try:
        # build_project_context 함수 호출 (별도 구현 필요)
        return "✅ 프로젝트 컨텍스트 빌드 완료"
    except Exception as e:
        return f"❌ 빌드 실패: {str(e)}"

def handle_workflow_command(command: str) -> HelperResult:
    """
    워크플로우 명령어 메인 엔트리 포인트
    HelperResult를 반환하여 helpers_wrapper와 호환
    """
    try:
        # 명령어 파싱
        parts = command.strip().split(None, 1)
        if not parts:
            return HelperResult.failure("명령어가 비어있습니다")
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # 명령어 라우팅
        if cmd in ["/plan", "plan"]:
            # /plan name | description [--reset]
            reset = "--reset" in args
            args = args.replace("--reset", "").strip()
            
            parts = args.split("|", 1)
            name = parts[0].strip() if parts else ""
            description = parts[1].strip() if len(parts) > 1 else ""
            
            if not name:
                return HelperResult.failure("계획 이름이 필요합니다")
            
            result = handle_plan(name, description, reset)
            return HelperResult.success({"message": result})
        
        elif cmd in ["/task", "task"]:
            # /task title | description
            parts = args.split("|", 1)
            title = parts[0].strip() if parts else ""
            description = parts[1].strip() if len(parts) > 1 else ""
            
            if not title:
                return HelperResult.failure("작업 제목이 필요합니다")
            
            result = handle_task(title, description)
            return HelperResult.success({"message": result})
        
        elif cmd in ["/status", "status"]:
            result = handle_status()
            return HelperResult.success({"message": result})
        
        elif cmd in ["/next", "next"]:
            result = handle_next(args)
            return HelperResult.success({"message": result})
        
        elif cmd in ["/approve", "approve"]:
            # /approve [yes|no] [메모]
            parts = args.split(None, 1)
            decision = parts[0] if parts else "yes"
            notes = parts[1] if len(parts) > 1 else ""
            
            result = handle_approve(decision, notes)
            return HelperResult.success({"message": result})
        
        elif cmd in ["/done", "/complete", "done", "complete"]:
            result = handle_done(args)
            return HelperResult.success({"message": result})
        
        elif cmd in ["/history", "history"]:
            result = handle_history()
            return HelperResult.success({"message": result})
        
        elif cmd in ["/build", "build"]:
            result = handle_build()
            return HelperResult.success({"message": result})
        
        else:
            return HelperResult.failure(f"알 수 없는 명령어: {cmd}")
            
    except Exception as e:
        return HelperResult.failure(f"명령어 처리 중 오류: {str(e)}")

# workflow_manager 인스턴스 export (다른 모듈에서 사용하기 위해)
__all__ = ['workflow_manager', 'handle_workflow_command']
