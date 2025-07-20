#!/usr/bin/env python3
"""
helpers LLM 함수 자동 패치
이 파일을 실행하면 helpers에 ask_o3 등의 함수가 추가됩니다.
"""

def patch_helpers_llm():
    """helpers에 LLM 관련 함수들을 추가"""
    try:
        # ai_helpers_v2.llm_ops에서 함수들 임포트
        from ai_helpers_v2.llm_ops import (
            ask_o3, analyze_code, explain_error, generate_docstring,
            prepare_o3_context
        )

        # helpers 객체 찾기
        import sys
        main_module = sys.modules.get('__main__')
        if main_module and hasattr(main_module, 'helpers'):
            helpers = main_module.helpers

            # 메서드 바인딩
            import types
            helpers.ask_o3 = types.MethodType(ask_o3, helpers)
            helpers.analyze_code = types.MethodType(analyze_code, helpers)
            helpers.explain_error = types.MethodType(explain_error, helpers)
            helpers.generate_docstring = types.MethodType(generate_docstring, helpers)
            helpers.prepare_o3_context = types.MethodType(prepare_o3_context, helpers)

            print("✅ helpers에 다음 LLM 함수들이 추가되었습니다:")
            print("  - ask_o3: o3 모델에 질문")
            print("  - analyze_code: 코드 분석")
            print("  - explain_error: 에러 설명")
            print("  - generate_docstring: 문서화 생성")
            print("  - prepare_o3_context: 컨텍스트 준비")
            return True
        else:
            print("❌ helpers 객체를 찾을 수 없습니다")
            return False

    except ImportError as e:
        print(f"❌ LLM 모듈 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 패치 중 오류: {e}")
        return False

if __name__ == "__main__":
    patch_helpers_llm()
