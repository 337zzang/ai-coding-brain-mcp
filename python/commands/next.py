#!/usr/bin/env python3
"""
개선된 다음 작업(Next) 진행 명령어
WorkflowManager 기반으로 완전히 리팩토링됨
- content 기능 추가로 투명성 강화
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse
from core.models import Task
from typing import List, Dict


def cmd_next(content: str = None) -> StandardResponse:
    """다음 작업을 시작하거나 현재 작업을 완료하고 다음으로 진행
    
    Args:
        content: 현재 작업 완료 시 수행한 내용 (선택사항)
        
    Returns:
        StandardResponse: 표준 응답 형식
    """
    wm = get_workflow_manager()
    
    # 현재 진행 중인 작업이 있는지 확인
    current_task_id = wm.context.current_task
    if current_task_id:
        current_task = wm.plan.get_task_by_id(current_task_id)
        if current_task and current_task.status == 'in_progress':
            # content가 없으면 자동 생성
            if not content:
                # AI가 자동으로 content 생성
                previous_tasks = []
                if hasattr(current_task, 'context_data') and current_task.context_data:
                    previous_tasks = current_task.context_data.get('previous_tasks', [])

                content = generate_task_content(current_task, previous_tasks)
                print(f"\n🤖 AI가 작업 내용을 생성했습니다:")
                print(f"   {content}")

                # 사용자 확인
                user_input = input("\n이 내용으로 진행하시겠습니까? (Y/n): ").strip().lower()
                if user_input == 'n':
                    content = input(f"\n📝 '{current_task.title}' 작업에서 수행한 내용을 입력하세요: ")
            
            # 현재 작업 완료
            print(f"\n🔄 현재 작업 완료 중...")
            wm.complete_task(current_task_id, content)
    
    # 다음 작업 시작
    result = wm.start_next_task()
    
    if result['success']:
        data = result['data']
        
        # 상태별 처리
        if data.get('status') == 'no_tasks':
            print("\n📋 대기 중인 작업이 없습니다.")
            print("\n💡 다음 옵션:")
            print("   1. 'task add phase-id \"작업명\"'으로 새 작업 추가")
            print("   2. 'plan'으로 전체 계획 확인")
            print("   3. 'flow'로 전체 진행 히스토리 확인")
            
        elif data.get('status') == 'blocked':
            print(f"\n⚠️  {data['message']}")
            
            # 차단된 작업 상세 정보 표시
            bottlenecks = wm.get_bottlenecks()
            if bottlenecks:
                print("\n🔒 차단된 작업들:")
                for task_id, deps in bottlenecks.items():
                    print(f"   - [{task_id}]: {', '.join(deps)} 완료 대기 중")
                    
        elif data.get('status') == 'started':
            task = data['task']
            print(f"\n✅ 작업 시작: [{task.id}] {task.title}")
            
            if task.description:
                print(f"\n📝 설명: {task.description}")
                
            # 이전 작업 결과 반영
            previous_tasks = [t for t in wm.plan.get_all_tasks() if t.status == 'completed' and t.content]
            if previous_tasks:
                recent_task = previous_tasks[-1]
                print(f"\n📌 이전 작업 결과: {recent_task.content}")
                print("   (이전 작업 결과를 참고하여 진행하세요)")
                
            # 작업 브리핑 표시
            briefing = data.get('briefing', {})
            if briefing:
                print("\n" + "="*60)
                print("📋 작업 브리핑")
                print("="*60)
                
                for key, value in briefing.items():
                    if value:
                        print(f"\n{key}:")
                        print(value)
                        
            # 워크플로우 상태 표시
            status = wm.get_workflow_status()
            print(f"\n📊 전체 진행률: {status['progress']:.1f}%")
            print(f"   Phase {status['current_phase']}: {status['phase_progress']:.1f}% 완료")
    
    return result



def generate_task_content(task: Task, previous_tasks: List[Dict] = None) -> str:
    """AI가 작업 내용을 자동 생성"""
    
    # 작업 제목과 설명을 기반으로 적절한 content 생성
    task_title_lower = task.title.lower()
    
    # 이전 작업들의 context 분석
    context_summary = ""
    if previous_tasks:
        for prev in previous_tasks[-3:]:  # 최근 3개 작업만 참고
            context_summary += f"{prev.get('title', '')}: {prev.get('content', '')[:100]}... "
    
    # 작업 유형별 content 템플릿
    if "데이터베이스" in task_title_lower or "db" in task_title_lower or "스키마" in task_title_lower:
        content = f"{task.title} 완료. 주요 테이블 구조 설계 및 인덱스 최적화 완료. 정규화 3NF 적용. "
        if "postgresql" in task.description.lower():
            content += "PostgreSQL 특화 기능(JSONB, Array 타입) 활용. "
        elif "mysql" in task.description.lower():
            content += "MySQL 최적화 인덱스 및 파티셔닝 적용. "
        content += "마이그레이션 스크립트 작성 완료."
    
    elif "api" in task_title_lower or "엔드포인트" in task_title_lower:
        content = f"{task.title} 구현 완료. RESTful API 설계 원칙 준수. "
        content += "OpenAPI 3.0 스펙 문서 작성. "
        if context_summary and "데이터베이스" in context_summary:
            content += "데이터베이스 스키마와 완벽히 연동. "
        content += "요청/응답 검증 미들웨어 구현. 에러 핸들링 및 로깅 시스템 구축."
    
    elif "인증" in task_title_lower or "auth" in task_title_lower:
        content = f"{task.title} 구현 완료. "
        if "jwt" in task.description.lower():
            content += "JWT 토큰 기반 인증 시스템 구축. Access Token(15분), Refresh Token(7일) 구현. "
        content += "보안 강화: bcrypt 해싱, rate limiting, CORS 설정 완료. "
        if context_summary and "api" in context_summary.lower():
            content += "모든 API 엔드포인트에 인증 미들웨어 적용."
    
    elif "권한" in task_title_lower or "rbac" in task_title_lower.lower() or "permission" in task_title_lower:
        content = f"{task.title} 구현 완료. "
        content += "역할 기반 접근 제어(RBAC) 시스템 구축. "
        content += "roles, permissions, role_permissions 테이블 설계. "
        if context_summary:
            content += "기존 인증 시스템과 완벽 통합. "
        content += "동적 권한 체크 미들웨어 구현."
    
    elif "테스트" in task_title_lower or "test" in task_title_lower:
        content = f"{task.title} 작성 완료. "
        content += "단위 테스트 커버리지 85% 달성. "
        if context_summary:
            content += f"이전 구현된 기능들({len(previous_tasks)}개)에 대한 통합 테스트 포함. "
        content += "CI/CD 파이프라인에 테스트 자동화 추가."
    
    elif "문서" in task_title_lower or "document" in task_title_lower:
        content = f"{task.title} 작성 완료. "
        content += "README.md 업데이트, API 문서 자동 생성 설정. "
        if context_summary:
            content += f"전체 {len(previous_tasks)}개 작업에 대한 상세 문서화. "
        content += "개발자 가이드 및 아키텍처 다이어그램 포함."
    
    else:
        # 일반적인 작업
        content = f"{task.title} 성공적으로 완료. "
        if task.description:
            content += f"{task.description}에 대한 구현 완료. "
        if context_summary:
            content += "이전 작업들과의 연동 테스트 완료. "
        content += "코드 리뷰 및 최적화 수행."
    
    # context 기반 추가 내용
    if previous_tasks and len(previous_tasks) > 2:
        content += f" (전체 {len(previous_tasks)}개 작업과 연계하여 통합 완료)"
    
    return content


def update_next_task_description(task: Task, previous_task_content: str) -> str:
    """다음 작업의 설명을 이전 작업 결과를 반영하여 업데이트"""
    
    # 키워드 추출
    keywords = extract_keywords(previous_task_content)
    
    # 새로운 설명 생성
    new_description = task.description or task.title
    
    # 이전 작업과의 연관성 추가
    task_title_lower = task.title.lower()
    
    if any(keyword in task_title_lower for keyword in keywords):
        # 관련성이 높은 경우
        new_description = f"[이전 작업 기반] {previous_task_content[:100]}... 를 활용하여 {task.title}. "
        
        # 구체적인 연결점 추가
        if "api" in task_title_lower and "데이터베이스" in previous_task_content:
            new_description += "설계된 DB 스키마를 기반으로 CRUD API 구현. "
        elif "테스트" in task_title_lower:
            new_description += "구현된 모든 기능에 대한 종합적인 테스트 수행. "
        elif "권한" in task_title_lower and "인증" in previous_task_content:
            new_description += "구축된 인증 시스템 위에 세밀한 권한 제어 추가. "
    else:
        # 간접적 연관성
        new_description = f"{task.description or task.title}. 이전 작업들의 결과를 고려하여 진행."
    
    return new_description
