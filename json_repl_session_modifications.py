# json_repl_session.py 수정 사항

## 새로운 load_helpers 함수
```python
def load_helpers():
    """헬퍼를 지연 로딩 - v2와 new 모두 지원"""
    global helpers, HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    # 1. 먼저 ai_helpers_new 시도 (우선순위)
    try:
        import sys
        import os
        # 프로젝트 루트 경로 추가
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        import ai_helpers_new as h

        # ai_helpers_v2와 호환되는 인터페이스 생성
        class AIHelpersWrapper:
            def __init__(self):
                self.h = h
                # v2 호환 메서드들
                for attr in dir(h):
                    if not attr.startswith('_'):
                        setattr(self, attr, getattr(h, attr))

        helpers = AIHelpersWrapper()
        HELPERS_AVAILABLE = True
        print("✅ AI Helpers NEW 로드 성공", file=sys.stderr)
        return True
    except ImportError as e:
        print(f"⚠️ AI Helpers NEW 로드 실패: {e}", file=sys.stderr)

    # 2. 실패하면 기존 ai_helpers_v2 시도
    try:
        from ai_helpers_v2 import AIHelpersV2
        helpers = AIHelpersV2()
        HELPERS_AVAILABLE = True
        print("✅ AI Helpers v2 로드 성공 (폴백)", file=sys.stderr)
        return True
    except ImportError as e:
        print(f"⚠️ AI Helpers v2 로드 실패: {e}", file=sys.stderr)
        return False
```

## 추가 필요 사항
1. repl_globals에 ai_helpers_new 추가
2. execute_code에서 경로 처리 개선
3. 에러 메시지 개선
