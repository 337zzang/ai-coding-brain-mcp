
# JSON REPL 세션 초기화 시 자동 실행 코드
# 이 파일을 json_repl_session.py의 초기화 부분에 추가하면 됨

def initialize_wrapped_helpers():
    """JSON REPL 세션 시작 시 helpers를 자동으로 래핑"""
    try:
        # helpers_wrapper 임포트
        from helpers_wrapper import HelpersWrapper
        
        # 전역 변수에서 helpers 찾기
        if 'helpers' in globals():
            # 이미 래핑되어 있는지 확인
            if not isinstance(globals()['helpers'], HelpersWrapper):
                # 원본 백업
                globals()['helpers_original'] = globals()['helpers']
                # 래퍼로 교체
                globals()['helpers'] = HelpersWrapper(globals()['helpers'])
                print("✅ helpers가 자동으로 래퍼 버전으로 초기화되었습니다!")
                print("   - helpers.메서드(): 표준화된 반환값")
                print("   - helpers_original.메서드(): 원본 반환값")
            else:
                print("ℹ️ helpers가 이미 래퍼 버전입니다.")
        return True
    except Exception as e:
        print(f"⚠️ helpers 자동 래핑 실패: {e}")
        print("   수동으로 실행: from python.auto_wrap_helpers import replace_helpers_with_wrapped; replace_helpers_with_wrapped()")
        return False

# REPL 세션에 추가할 초기화 코드
REPL_INIT_CODE = """
# Wrapped Helpers 자동 초기화
try:
from auto_wrap_helpers import auto_wrap_helpers
    auto_wrap_helpers()
except:
    pass
"""