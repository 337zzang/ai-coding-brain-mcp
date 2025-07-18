"""
AI Helpers v2 - LLM Operations
LLM 관련 작업 (ask_o3 등)
"""
import os
from typing import Dict, Any, Optional, List
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
def ask_o3(question: str, 
          context: Optional[str] = None,
          api_key: Optional[str] = None,
          reasoning_effort: str = "high",  # o3-high thinking
          max_completion_tokens: int = 10000,  # 충분한 토큰
          use_tools: bool = False) -> Dict[str, Any]:
    """
    OpenAI o3 모델을 사용하여 고급 추론 작업 수행

    Args:
        question: 질문 또는 작업 설명
        context: 추가 컨텍스트 (코드, 문서, 데이터 등)
        api_key: OpenAI API 키 (없으면 환경변수 사용)
        reasoning_effort: 추론 강도 ("low", "medium", "high")
        max_completion_tokens: 최대 완성 토큰 수
        use_tools: 도구 사용 여부 (웹 검색, Python 등)

    Returns:
        Dict containing:
            - success: bool
            - answer: str (모델의 답변)
            - reasoning_effort: str (사용된 추론 강도)
            - thinking_time: float (추론 시간)
            - usage: dict (토큰 사용량 및 비용)
            - timestamp: str
    """
    try:
        import time
        start_time = time.time()

        # API 키 확인
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY가 설정되지 않았습니다.",
                "timestamp": datetime.now().isoformat()
            }

        # OpenAI 클라이언트 설정
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except ImportError:
            return {
                "success": False,
                "error": "openai 패키지가 설치되지 않았습니다. pip install openai",
                "timestamp": datetime.now().isoformat()
            }

        # 메시지 구성
        messages = []

        # o3 모델은 developer 메시지 사용 (system 대신)
        if context:
            messages.append({
                "role": "developer",
                "content": f"다음 컨텍스트를 참고하여 답변해주세요:\n\n{context}"
            })

        messages.append({
            "role": "user",
            "content": question
        })

        # o3 모델 호출 파라미터
        completion_params = {
            "model": "o3",  # o3 기본 모델
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
            "reasoning_effort": reasoning_effort  # low, medium, high
        }

        # 도구 사용 설정 (선택적)
        if use_tools:
            completion_params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "code_interpreter",
                        "description": "Python 코드를 실행하여 데이터 분석 및 계산 수행"
                    }
                },
                {
                    "type": "function", 
                    "function": {
                        "name": "web_search",
                        "description": "웹에서 최신 정보 검색"
                    }
                }
            ]

        # API 호출
        print(f"🤔 o3 모델 호출 중... (reasoning_effort: {reasoning_effort})")
        response = client.chat.completions.create(**completion_params)

        # 응답 처리
        answer = response.choices[0].message.content
        thinking_time = time.time() - start_time

        # 사용량 및 비용 계산
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        # o3 가격: $2/1M input, $8/1M output
        input_cost = (input_tokens * 2) / 1_000_000
        output_cost = (output_tokens * 8) / 1_000_000
        total_cost = input_cost + output_cost

        # reasoning_tokens 확인 (있는 경우)
        reasoning_tokens = getattr(usage, 'reasoning_tokens', 0)

        return {
            "success": True,
            "answer": answer,
            "reasoning_effort": reasoning_effort,
            "thinking_time": f"{thinking_time:.2f}초",
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens,
                "reasoning_tokens": reasoning_tokens,
                "input_cost": f"${input_cost:.6f}",
                "output_cost": f"${output_cost:.6f}",
                "total_cost": f"${total_cost:.6f}"
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "reasoning_effort": reasoning_effort,
            "timestamp": datetime.now().isoformat()
        }

def prepare_o3_context(topic: str, files: Optional[List[str]] = None) -> str:
    """
    o3를 위한 간단한 컨텍스트 준비 함수

    Args:
        topic: 주제 또는 문제 설명
        files: 포함할 파일 경로 리스트 (선택)

    Returns:
        구조화된 컨텍스트 문자열
    """
    context_parts = []

    # 프로젝트 정보 (helpers가 있는 경우)
    try:
        from . import get_current_project
        project_info = get_current_project()
        if project_info:
            context_parts.append(f"프로젝트: {project_info}")
    except:
        pass

    context_parts.append(f"주제: {topic}\n")

    # 파일 내용 포함
    if files:
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 파일이 너무 길면 일부만 포함
                    if len(content) > 3000:
                        content = content[:3000] + "\n... (생략)"

                    context_parts.append(f"--- {file_path} ---")
                    context_parts.append(content)
                    context_parts.append("")
                except Exception as e:
                    context_parts.append(f"--- {file_path} ---")
                    context_parts.append(f"읽기 오류: {e}")
                    context_parts.append("")

    return "\n".join(context_parts)

def analyze_code(code: str, question: str = "이 코드를 분석해주세요") -> Dict[str, Any]:
    """코드 분석 요청"""
    return ask_o3(question, context=code)