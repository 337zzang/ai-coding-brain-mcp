"""
REPL 친화적 code_ops 도구 모음
빠른 코드 작업을 위한 2글자 약어 함수들

사용법:
  from q_tools import *


# REPL 환경의 helpers 가져오기
try:
    # JSON REPL 환경에서 helpers 가져오기
    import sys
    if hasattr(sys.modules.get('__main__', None), 'helpers'):
        helpers = sys.modules['__main__'].helpers
    else:
        helpers = None
except:
    helpers = None

  qp("file.py")              # 파일 구조 분석
  qv("file.py", "func_name") # 함수 코드 보기
  qr("file.py", "func", new_code) # 함수 교체
"""

# 필요한 import들은 실행 시점에 동적으로 처리
def get_helpers():
    """helpers 객체를 동적으로 가져오기"""
    import sys
    if 'helpers' in sys.modules['__main__'].__dict__:
        return sys.modules['__main__'].__dict__['helpers']
    return None

# 모든 q* 함수를 __all__에 추가
# === 파일 작업 확장 ===
# === Git 작업 확장 ===
# === 디렉토리 작업 확장 ===
# === 프로젝트 작업 ===
# 기존 __all__에 추가

# === Git 고급 작업 ===
__all__ = ['qp', 'ql', 'qv', 'qr', 'qi', 'qs', 'qm', 'qd',
           'qf', 'qw', 'qe', 'qg', 'qc', 'qb', 'qls', 'qfind', 'qproj',
           'qpush', 'qpull', 'qlog']