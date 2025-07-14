"""
LLM Helper - OpenAI o3 모델을 사용한 질의 헬퍼
간단하게 LLM에게 질문하고 답변을 받는 헬퍼 함수
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI 패키지가 설치되지 않았습니다. pip install openai 실행 필요")

logger = logging.getLogger(__name__)

class LLMHelper:
    """OpenAI o3 모델을 사용한 LLM 헬퍼"""
    
    def __init__(self):
        self.model = "o3"  # o3는 아직 사용 불가, gpt-4-turbo 사용
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if OPENAI_AVAILABLE and self.api_key:
            # OpenAI 클라이언트 초기화
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            if not self.api_key:
                logger.warning("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")
        
    def ask_o3(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        o3 스타일로 질문하고 답변받기 
        
        Args:
            question: 질문 내용
            context: 추가 컨텍스트 (코드, 문서 등)
            
        Returns:
            Dict containing:
                - success: bool
                - answer: str (모델의 답변)
                - model: str (사용된 모델)
                - timestamp: str
        """
        try:
            # 전체 프롬프트 구성
            full_prompt = self._build_prompt(question, context)
            
            # 실제 API 호출 또는 시뮬레이션
            if self.client and OPENAI_AVAILABLE:
                answer = self._call_openai_api(full_prompt)
            else:
                answer = self._simulate_o3_response(full_prompt)
            
            return {
                "success": True,
                "answer": answer,
                "model": self.model,
                "question": question,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
    
    def ask_for_code_review(self, code: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        코드 리뷰 요청
        
        Args:
            code: 리뷰할 코드
            focus_areas: 집중할 영역 (예: ["성능", "보안", "가독성"])
        """
        question = f"""
        다음 코드를 리뷰해주세요:
        
        ```python
        {code}
        ```
        
        {f"특히 다음 부분에 집중해주세요: {', '.join(focus_areas)}" if focus_areas else ""}
        """
        
        return self.ask_o3(question)
    
    def ask_for_design_help(self, problem: str, constraints: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        설계 도움 요청
        
        Args:
            problem: 해결하려는 문제
            constraints: 제약사항
        """
        question = f"""
        다음 문제에 대한 설계를 도와주세요:
        
        문제: {problem}
        
        {f"제약사항: {chr(10).join('- ' + c for c in constraints)}" if constraints else ""}
        
        다음을 포함해서 답변해주세요:
        1. 전체 아키텍처
        2. 주요 컴포넌트
        3. 구현 순서
        4. 주의사항
        """
        
        return self.ask_o3(question)
    
    def ask_for_error_solution(self, error_msg: str, code_context: Optional[str] = None) -> Dict[str, Any]:
        """
        에러 해결 방법 질문
        
        Args:
            error_msg: 에러 메시지
            code_context: 관련 코드
        """
        # 에러 메시지 구성
        question_parts = [
            "다음 에러를 해결하는 방법을 알려주세요:",
            "",
            f"에러: {error_msg}",
            ""
        ]

        if code_context:
            question_parts.extend([
                "관련 코드:",
                "```python",
                code_context,
                "```",
                ""
            ])

        question_parts.append("구체적인 해결 방법과 코드 예시를 제공해주세요.")
        question = "\n".join(question_parts)

        return self.ask_o3(question)
    def ask_for_optimization(self, code: str, optimization_type: str = "performance") -> Dict[str, Any]:
        """
        코드 최적화 제안 요청
        
        Args:
            code: 최적화할 코드
            optimization_type: "performance", "memory", "readability" 등
        """
        question = f"""
        다음 코드를 {optimization_type} 측면에서 최적화해주세요:
        
        ```python
        {code}
        ```
        
        최적화된 코드와 개선 사항을 설명해주세요.
        """
        
        return self.ask_o3(question)
    
    def _build_prompt(self, question: str, context: Optional[str]) -> str:
        """프롬프트 구성"""
        if context:
            return f"""
컨텍스트:
{context}

질문:
{question}
"""
        return question
    
    def _call_openai_api(self, prompt: str) -> str:
        """실제 OpenAI API 호출"""
        try:
            # o3 스타일 추론을 위한 시스템 프롬프트
            system_prompt = """You are an AI assistant with deep reasoning capabilities similar to o3.
Before answering, think step by step:
1. Understand the problem thoroughly
2. Break it down into components
3. Consider multiple approaches
4. Verify your reasoning
5. Provide a comprehensive answer

Be especially helpful with:
- Code review and optimization
- Design and architecture
- Error solving and debugging
- Step-by-step explanations"""

            # o3 모델은 max_completion_tokens 사용
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # 모델별 파라미터 설정
            if self.model == "o3":
                kwargs["max_completion_tokens"] = 2000
                # o3는 temperature 기본값(1)만 지원
            else:
                kwargs["max_tokens"] = 2000
                kwargs["temperature"] = 0.7
                
            response = self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            # 에러 발생 시 시뮬레이션으로 폴백
            return self._simulate_o3_response(prompt)
    
    def _simulate_o3_response(self, prompt: str) -> str:
        """o3 응답 시뮬레이션 (실제 구현 전)"""
        # TODO: 실제 OpenAI API 호출로 교체
        return f"""
[o3 모델 시뮬레이션 응답]

질문을 분석했습니다. 다음은 제안사항입니다:

1. 문제 이해: {prompt[:50]}...
2. 해결 방안: 단계별 접근이 필요합니다.
3. 구체적 코드: 실제 구현 시 제공됩니다.

참고: 이는 시뮬레이션입니다. 실제 o3 API 연결이 필요합니다.
"""


# 헬퍼 함수로 래핑
def ask_llm(question: str, context: Optional[str] = None, model: str = "gpt-4-turbo-preview") -> Dict[str, Any]:
    """
    LLM에게 질문하기 (간단한 인터페이스)
    
    사용 예:
        result = helpers.ask_llm("이 코드의 문제점은 무엇인가요?", context=code)
        print(result['answer'])
    """
    helper = LLMHelper()
    if model:
        helper.model = model
    return helper.ask_o3(question, context)


def ask_code_review(code: str, focus: Optional[List[str]] = None) -> Dict[str, Any]:
    """코드 리뷰 요청"""
    helper = LLMHelper()
    return helper.ask_for_code_review(code, focus)


def ask_design_help(problem: str, constraints: Optional[List[str]] = None) -> Dict[str, Any]:
    """설계 도움 요청"""
    helper = LLMHelper()
    return helper.ask_for_design_help(problem, constraints)


def ask_error_help(error: str, code: Optional[str] = None) -> Dict[str, Any]:
    """에러 해결 도움 요청"""
    helper = LLMHelper()
    return helper.ask_for_error_solution(error, code)


def ask_optimize_code(code: str, opt_type: str = "performance") -> Dict[str, Any]:
    """코드 최적화 요청"""
    helper = LLMHelper()
    return helper.ask_for_optimization(code, opt_type)
