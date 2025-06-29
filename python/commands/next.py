#!/usr/bin/env python3
"""
개선된 다음 작업(Next) 진행 명령어
WorkflowManager 기반으로 완전히 리팩토링됨
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from typing import Dict, Any, Optional


def cmd_next(content: Optional[str] = None) -> None:
    """
    현재 작업을 완료하고 다음 작업으로 진행
    - 현재 작업 자동 완료 (content 저장)
    - 다음 작업 자동 시작
    - 하나의 명령으로 매끄러운 흐름 제공
    
    Args:
        content: 현재 작업의 완료 내용/요약 (선택사항)
    """
    wm = get_workflow_manager()
    context = wm.context
    
    # 1. 현재 작업이 있으면 자동 완료
    if context.current_task:
        print(f"🔄 현재 작업 완료 처리 중...")
        
        # 완료 내용이 없으면 기본 메시지
        if not content:
            content = "작업 완료 (자동 완료 처리됨)"
        
        result = wm.complete_task(content=content)
        if result['success']:
            task_data = result['data']
            print(f"✅ 작업 완료: [{task_data['task_id']}] {task_data['title']}")
            if task_data.get('content'):
                print(f"   📝 완료 내용: {task_data['content']}")
        else:
            print(f"⚠️ 작업 완료 실패: {result['message']}")
            # 완료 실패해도 다음 작업 시도 가능
    
    # 2. 다음 작업 시작
    print("\n🚀 다음 작업 시작...")
    result = wm.start_next_task()
    
    if result['success']:
        task_data = result['data']
        print(f"\n✨ 새 작업: [{task_data['id']}] {task_data['title']}")
        print(f"   📌 Phase: {task_data.get('phase_name', 'N/A')}")
        if task_data.get('description'):
            print(f"   📝 설명: {task_data['description']}")
        
        # 작업 브리핑
        print("\n💡 작업 진행 가이드:")
        print("   - 작업을 완료한 후 '/next [완료 내용]'를 입력하세요")
        print("   - 완료 내용은 선택사항입니다")
        
    else:
        print(f"\n🎉 {result['message']}")
        if "모든 작업이 완료" in result['message']:
            print("\n🏆 축하합니다! 현재 계획의 모든 작업을 완료했습니다.")
            print("   새로운 작업을 추가하려면 '/task add'를 사용하세요.")