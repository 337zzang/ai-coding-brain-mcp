#!/usr/bin/env python3
"""
개선된 plan, task, next 명령어 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 개선된 모듈 import
from commands.improved.plan_improved import cmd_plan
from commands.improved.task_improved import cmd_task
from commands.improved.next_improved import cmd_next

def test_workflow():
    """전체 워크플로우 테스트"""
    print("🧪 개선된 명령어 테스트 시작\n")
    
    # 1. 계획 생성
    print("=" * 50)
    print("1️⃣ 계획 생성 테스트")
    print("=" * 50)
    cmd_plan("할일 관리 시스템 개선", "plan, task, next 명령어 개선 및 테스트")
    
    # 2. 현재 계획 확인
    print("\n" + "=" * 50)
    print("2️⃣ 현재 계획 확인")
    print("=" * 50)
    cmd_plan()
    
    # 3. 작업 추가
    print("\n" + "=" * 50)
    print("3️⃣ 작업 추가 테스트")
    print("=" * 50)
    cmd_task("add", "phase-1", "ProjectContext와 dict 호환성 문제 해결", "모든 명령어가 두 형태 모두 지원하도록 수정")
    cmd_task("add", "phase-1", "Plan 객체와 dict 변환 로직 구현", "일관된 데이터 처리를 위한 변환 함수 작성")
    cmd_task("add", "phase-2", "개선된 명령어 구현", "plan_improved.py, task_improved.py, next_improved.py 작성")
    cmd_task("add", "phase-2", "MCP 도구 통합", "개선된 명령어를 MCP 도구와 연결")
    cmd_task("add", "phase-3", "통합 테스트", "전체 워크플로우 테스트")
    cmd_task("add", "phase-3", "문서화", "사용법 및 개선사항 문서화")
    
    # 4. 작업 목록 확인
    print("\n" + "=" * 50)
    print("4️⃣ 작업 목록 확인")
    print("=" * 50)
    cmd_task("list")
    
    # 5. 다음 작업 시작
    print("\n" + "=" * 50)
    print("5️⃣ 다음 작업 시작")
    print("=" * 50)
    cmd_next()
    
    # 6. 현재 작업 확인
    print("\n" + "=" * 50)
    print("6️⃣ 현재 작업 확인")
    print("=" * 50)
    cmd_task("current")
    
    # 7. 작업 완료
    print("\n" + "=" * 50)
    print("7️⃣ 작업 완료")
    print("=" * 50)
    # 현재 작업 ID를 가져와서 완료 처리
    from core.context_manager import get_context_manager
    context = get_context_manager().context
    current_task_id = None
    if hasattr(context, 'current_task'):
        current_task_id = context.current_task
    elif isinstance(context, dict):
        current_task_id = context.get('current_task')
    
    if current_task_id:
        cmd_task("done", current_task_id)
    
    # 8. 다음 작업으로 진행
    print("\n" + "=" * 50)
    print("8️⃣ 다음 작업으로 진행")
    print("=" * 50)
    cmd_next()
    
    # 9. 최종 상태 확인
    print("\n" + "=" * 50)
    print("9️⃣ 최종 상태 확인")
    print("=" * 50)
    cmd_task("list")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")
    print("=" * 50)


if __name__ == "__main__":
    # flow 명령으로 프로젝트 초기화
    from core.context_manager import get_context_manager
    
    # 프로젝트 컨텍스트 확인
    cm = get_context_manager()
    if not cm.context:
        print("⚠️ 프로젝트가 선택되지 않았습니다.")
        print("먼저 'flow ai-coding-brain-mcp'를 실행하세요.")
        sys.exit(1)
    
    # 테스트 실행
    test_workflow()
