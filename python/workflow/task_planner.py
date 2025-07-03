"""
AI 기반 작업 실행 계획 생성기
Gemini 또는 GPT를 사용하여 작업에 대한 상세 실행 계획을 자동으로 생성
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class AITaskPlanner:
    """AI를 사용한 작업 실행 계획 생성"""
    
    def __init__(self, ai_provider: str = 'gemini'):
        """
        Args:
            ai_provider: 'gemini' 또는 'gpt' (기본값: gemini)
        """
        self.ai_provider = ai_provider
        self.api_key = self._get_api_key()
        
    def _get_api_key(self) -> Optional[str]:
        """환경 변수에서 API 키 가져오기"""
        if self.ai_provider == 'gemini':
            return os.environ.get('GEMINI_API_KEY')
        elif self.ai_provider == 'gpt':
            return os.environ.get('OPENAI_API_KEY')
        return None
    
    def generate_execution_plan(self, task_title: str, task_description: str, 
                              project_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        작업에 대한 실행 계획 생성
        
        Args:
            task_title: 작업 제목
            task_description: 작업 설명
            project_context: 프로젝트 컨텍스트 (선택)
            
        Returns:
            실행 계획 딕셔너리
        """
        # 프롬프트 생성
        prompt = self._create_planning_prompt(task_title, task_description, project_context)
        
        # AI API 호출 (실제 구현에서는 API 호출)
        # 현재는 시뮬레이션된 응답 반환
        if not self.api_key:
            # API 키가 없으면 기본 계획 생성
            return self._generate_default_plan(task_title, task_description)
        
        # TODO: 실제 AI API 호출 구현
        # response = self._call_ai_api(prompt)
        # return self._parse_ai_response(response)
        
        # 임시로 상세한 기본 계획 반환
        return self._generate_detailed_plan(task_title, task_description)
    
    def _create_planning_prompt(self, task_title: str, task_description: str, 
                               project_context: Optional[Dict] = None) -> str:
        """AI를 위한 프롬프트 생성"""
        prompt = f"""작업 실행 계획을 생성해주세요.

작업 제목: {task_title}
작업 설명: {task_description}

다음 형식으로 상세한 실행 계획을 작성해주세요:

1. 실행 단계 (steps):
   - 구체적이고 실행 가능한 단계들
   - 각 단계는 명확한 행동을 포함
   - 순서대로 나열

2. 예상 소요 시간 (estimated_time):
   - 전체 작업 완료까지의 예상 시간

3. 필요한 도구 (tools):
   - 작업 수행에 필요한 도구, 라이브러리, 기술 목록

4. 잠재적 위험 (risks):
   - 작업 중 발생할 수 있는 문제점
   - 주의해야 할 사항

5. 성공 기준 (success_criteria):
   - 작업이 성공적으로 완료되었다고 판단할 수 있는 기준
   - 검증 가능한 구체적인 기준

JSON 형식으로 응답해주세요."""
        
        if project_context:
            prompt += f"\n\n프로젝트 컨텍스트: {json.dumps(project_context, ensure_ascii=False, indent=2)}"
            
        return prompt
    
    def _generate_default_plan(self, task_title: str, task_description: str) -> Dict[str, Any]:
        """기본 실행 계획 생성 (API 키가 없을 때)"""
        return {
            'steps': [
                f"{task_title} 관련 현재 상태 분석",
                "필요한 변경사항 식별",
                "구현 또는 수정 작업 수행",
                "테스트 및 검증",
                "문서화 및 커밋"
            ],
            'estimated_time': "1-2시간",
            'tools': ["Python", "Git", "관련 라이브러리"],
            'risks': ["기존 기능 영향 가능성", "테스트 부족으로 인한 버그"],
            'success_criteria': [
                f"{task_title} 완료",
                "모든 테스트 통과",
                "문서 업데이트 완료"
            ]
        }
    
    def _generate_detailed_plan(self, task_title: str, task_description: str) -> Dict[str, Any]:
        """상세한 기본 계획 생성 (시뮬레이션)"""
        # 작업 제목에서 키워드 추출
        keywords = task_title.lower().split()
        
        steps = []
        tools = ["Python", "Git"]
        
        # 키워드 기반 단계 생성
        if any(word in keywords for word in ['오류', 'error', '버그', 'fix']):
            steps.extend([
                "현재 오류 상황 재현 및 분석",
                "오류 발생 원인 파악",
                "수정 방안 설계",
                "코드 수정 구현",
                "단위 테스트 작성",
                "통합 테스트 수행"
            ])
            tools.extend(["디버거", "로그 분석 도구"])
            
        elif any(word in keywords for word in ['구현', 'implement', '생성', 'create']):
            steps.extend([
                "요구사항 분석 및 설계",
                "인터페이스 정의",
                "핵심 로직 구현",
                "예외 처리 추가",
                "테스트 코드 작성",
                "문서화"
            ])
            tools.extend(["IDE", "테스트 프레임워크"])
            
        elif any(word in keywords for word in ['리팩토링', 'refactor', '개선']):
            steps.extend([
                "현재 코드 구조 분석",
                "개선점 식별",
                "리팩토링 계획 수립",
                "단계별 리팩토링 수행",
                "기능 동작 검증",
                "성능 비교 테스트"
            ])
            tools.extend(["코드 분석 도구", "프로파일러"])
            
        else:
            # 일반적인 작업
            steps = self._generate_default_plan(task_title, task_description)['steps']
        
        # 설명에 따른 추가 단계
        if '테스트' in task_description:
            steps.append("포괄적인 테스트 시나리오 실행")
        if '문서' in task_description:
            steps.append("README 및 관련 문서 업데이트")
        if 'API' in task_description:
            steps.append("API 엔드포인트 테스트")
            tools.append("API 테스트 도구")
            
        return {
            'steps': steps,
            'estimated_time': self._estimate_time(len(steps)),
            'tools': list(set(tools)),  # 중복 제거
            'risks': self._identify_risks(task_title, task_description),
            'success_criteria': self._define_success_criteria(task_title, task_description)
        }
    
    def _estimate_time(self, num_steps: int) -> str:
        """단계 수에 따른 시간 추정"""
        if num_steps <= 3:
            return "30분-1시간"
        elif num_steps <= 6:
            return "1-2시간"
        elif num_steps <= 10:
            return "2-4시간"
        else:
            return "4시간 이상"
    
    def _identify_risks(self, task_title: str, task_description: str) -> List[str]:
        """작업에 따른 위험 요소 식별"""
        risks = []
        
        combined_text = f"{task_title} {task_description}".lower()
        
        if '삭제' in combined_text or 'remove' in combined_text:
            risks.append("데이터 손실 가능성")
        if '변경' in combined_text or 'modify' in combined_text:
            risks.append("기존 기능 호환성 문제")
        if '마이그레이션' in combined_text:
            risks.append("데이터 무결성 손상 위험")
        if 'API' in combined_text:
            risks.append("외부 서비스 의존성")
        if '성능' in combined_text:
            risks.append("성능 저하 가능성")
            
        # 기본 위험 요소
        if not risks:
            risks = [
                "예상치 못한 부작용 발생 가능성",
                "테스트 커버리지 부족"
            ]
            
        return risks
    
    def _define_success_criteria(self, task_title: str, task_description: str) -> List[str]:
        """성공 기준 정의"""
        criteria = [
            f"{task_title} 요구사항 충족",
            "모든 관련 테스트 통과"
        ]
        
        combined_text = f"{task_title} {task_description}".lower()
        
        if '오류' in combined_text or 'error' in combined_text:
            criteria.append("오류 재현 불가능")
        if '성능' in combined_text:
            criteria.append("성능 지표 개선 확인")
        if 'API' in combined_text:
            criteria.append("API 응답 정상 확인")
        if '문서' in combined_text:
            criteria.append("문서 최신화 완료")
            
        criteria.append("코드 리뷰 통과")
        
        return criteria
    
    def update_task_with_plan(self, task: Any, plan: Dict[str, Any]) -> Any:
        """작업에 실행 계획 추가"""
        from workflow.models import ExecutionPlan
        
        task.execution_plan = ExecutionPlan(
            steps=plan['steps'],
            estimated_time=plan['estimated_time'],
            tools=plan['tools'],
            risks=plan['risks'],
            success_criteria=plan['success_criteria'],
            ai_provider=self.ai_provider
        )
        
        # 상태를 PENDING으로 변경 (승인 대기)
        from workflow.models import TaskStatus
        if task.status == TaskStatus.TODO:
            task.status = TaskStatus.PENDING
            
        return task


# 편의 함수
def generate_plan_for_task(task_title: str, task_description: str, 
                          ai_provider: str = 'gemini') -> Dict[str, Any]:
    """작업에 대한 실행 계획 생성 (편의 함수)"""
    planner = AITaskPlanner(ai_provider)
    return planner.generate_execution_plan(task_title, task_description)


# 예제 사용
if __name__ == "__main__":
    # 테스트
    planner = AITaskPlanner()
    
    test_task = "오류 보고 시스템 단순화"
    test_desc = "복잡한 오류 추적 시스템을 제거하고 즉시 보고 원칙 적용"
    
    plan = planner.generate_execution_plan(test_task, test_desc)
    
    print("생성된 실행 계획:")
    print(json.dumps(plan, indent=2, ensure_ascii=False))
