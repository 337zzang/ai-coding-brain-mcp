"""
Command: Task - 작업 관리
WorkflowManager 중심 아키텍처 버전
"""
from typing import List, Optional
from core.workflow_manager import get_workflow_manager


def cmd_task(action: str = "list", args: Optional[List[str]] = None) -> None:
    """
    작업 관리 명령어 - WorkflowManager에 모든 로직 위임
    
    Args:
        action: 액션 (add, list, start, complete, phase)
        args: 액션별 인자
    """
    wm = get_workflow_manager()
    args = args or []
    
    if action == "add":
        # 인자 파싱: phase_name, title, [description]
        if len(args) < 2:
            print("❌ 사용법: /task add [phase] [제목] [설명(선택)]")
            return
        
        phase_name = args[0]
        title = args[1]
        description = args[2] if len(args) > 2 else None
        
        result = wm.add_task(
            phase_name=phase_name,
            title=title,
            description=description
        )
        
        if result['success']:
            print(f"✅ {result['message']}")
            print(f"   📌 Phase: {result['data']['phase_name']}")
            print(f"   📋 제목: {result['data']['title']}")
            if result['data']['description']:
                print(f"   📝 설명: {result['data']['description']}")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "list":
        tasks = wm.get_task_list()
        
        if not tasks:
            print("📋 등록된 작업이 없습니다")
            return
        
        print(f"📋 전체 작업 목록 ({len(tasks)}개):")
        
        current_phase = None
        for task in tasks:
            # Phase 구분
            if current_phase != task['phase_name']:
                current_phase = task['phase_name']
                print(f"\n📂 {current_phase}:")
            
            # 상태 아이콘
            status_icon = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in_progress" else "⏳"
            current_mark = " 👈" if task['is_current'] else ""
            
            print(f"   {status_icon} [{task['id'][:8]}...] {task['title']}{current_mark}")
            if task['description']:
                print(f"      └─ {task['description']}")
    
    elif action == "start":
        if not args:
            # 다음 작업 자동 시작
            result = wm.start_next_task()
        else:
            # 특정 작업 시작
            task_id = args[0]
            result = wm.start_task(task_id)
        
        if result['success']:
            print(f"✅ {result['message']}")
            task_data = result['data']
            print(f"   📋 작업: {task_data['title']}")
            print(f"   🚀 상태: {task_data['status']}")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "complete":
        # 인자 파싱: [task_id], [content]
        task_id = None
        content = None
        
        if args:
            # 첫 인자가 UUID 형식이면 task_id, 아니면 content
            if len(args[0]) > 30 and '-' in args[0]:
                task_id = args[0]
                content = args[1] if len(args) > 1 else None
            else:
                content = ' '.join(args)
        
        result = wm.complete_task(task_id=task_id, content=content)
        
        if result['success']:
            print(f"✅ {result['message']}")
            task_data = result['data']
            if task_data['content']:
                print(f"   📝 완료 내용: {task_data['content']}")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "phase":
        # Phase 추가
        if not args:
            print("❌ 사용법: /task phase [이름] [설명(선택)]")
            return
        
        name = args[0]
        description = args[1] if len(args) > 1 else None
        
        result = wm.add_phase(name=name, description=description)
        
        if result['success']:
            print(f"✅ {result['message']}")
            if result['data']['description']:
                print(f"   📝 설명: {result['data']['description']}")
        else:
            print(f"❌ {result['message']}")
    
    else:
        print(f"❌ 알 수 없는 액션: {action}")
        print("   사용 가능한 액션: add, list, start, complete, phase")
        
    # 현재 작업 표시
    current_task = wm.get_current_task()
    if current_task:
        print(f"\n🎯 현재 작업: {current_task.title}")
