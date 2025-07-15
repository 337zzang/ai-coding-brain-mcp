"""
AI Helpers v2 - LLM Operations
LLM 관련 작업 (ask_o3 등)
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime
from .core import track_execution

# OpenAI 관련 설정
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 라이브러리가 설치되지 않았습니다. pip install openai")

@track_execution
def ask_o3(question: str, context: Optional[str] = None, 
           api_key: Optional[str] = None, model: str = "gpt-4") -> Dict[str, Any]:
    """
    o3 스타일로 질문하고 답변받기

    Args:
        question: 질문 내용
        context: 추가 컨텍스트 (코드, 문서 등)
        api_key: OpenAI API 키 (없으면 환경변수 사용)
        model: 사용할 모델 (기본: gpt-4)

    Returns:
        Dict containing:
            - success: bool
            - answer: str (모델의 답변)
            - model: str (사용된 모델)
            - timestamp: str
    """
    try:
        # API 키 확인
        api_key = api_key or os.getenv('OPENAI_API_KEY')

        # 프롬프트 구성
        full_prompt = _build_prompt(question, context)

        # 실제 API 호출 또는 시뮬레이션
        if api_key and OPENAI_AVAILABLE:
            answer = _call_openai_api(full_prompt, api_key, model)
        else:
            answer = _simulate_o3_response(full_prompt)

        return {
            "success": True,
            "answer": answer,
            "model": model,
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "simulated": not (api_key and OPENAI_AVAILABLE)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model,
            "question": question,
            "timestamp": datetime.now().isoformat()
        }

def _build_prompt(question: str, context: Optional[str] = None) -> str:
    """프롬프트 구성"""
    prompt = f"Question: {question}\n"

    if context:
        prompt = f"Context:\n{context}\n\n{prompt}"

    return prompt

def _call_openai_api(prompt: str, api_key: str, model: str = "gpt-4") -> str:
    """실제 OpenAI API 호출"""
    if not OPENAI_AVAILABLE:
        return _simulate_o3_response(prompt)

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ OpenAI API 오류: {e}")
        return _simulate_o3_response(prompt)

def _simulate_o3_response(prompt: str) -> str:
    """o3 응답 시뮬레이션 (API 키가 없을 때)"""
    # 질문 분석
    question_lower = prompt.lower()

    # 간단한 패턴 매칭
    if "코드" in question_lower or "code" in question_lower:
        return "코드 관련 질문이군요. API 키를 설정하면 더 정확한 답변을 받을 수 있습니다."
    elif "오류" in question_lower or "error" in question_lower:
        return "오류 해결을 도와드리겠습니다. 구체적인 오류 메시지와 코드를 제공해주세요."
    elif "설명" in question_lower or "explain" in question_lower:
        return "개념 설명이 필요하신가요? API 키를 설정하면 더 자세한 설명을 받을 수 있습니다."
    else:
        return f"'{prompt[:50]}...' 에 대한 답변입니다. (시뮬레이션 모드 - API 키 필요)"

# 추가 LLM 관련 함수들
@track_execution
def analyze_code(code: str, question: str = "이 코드를 분석해주세요") -> Dict[str, Any]:
    """코드 분석 요청"""
    return ask_o3(question, context=code)

@track_execution
def explain_error(error_message: str, code: Optional[str] = None) -> Dict[str, Any]:
    """오류 설명 요청"""
    question = f"다음 오류를 설명하고 해결 방법을 제안해주세요: {error_message}"
    return ask_o3(question, context=code)

@track_execution
def generate_docstring(function_code: str) -> Dict[str, Any]:
    """함수에 대한 docstring 생성"""
    question = "이 함수에 대한 Python docstring을 생성해주세요"
    return ask_o3(question, context=function_code)
