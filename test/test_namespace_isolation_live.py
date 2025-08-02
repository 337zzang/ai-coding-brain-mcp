#!/usr/bin/env python3
"""네임스페이스 격리 구현 테스트"""

import sys
import os
import warnings

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=== 네임스페이스 격리 테스트 시작 ===\n")

# 1. json_repl_session 모듈 import
print("1. 모듈 import 테스트")
try:
    from json_repl_session import load_helpers
    print("   ✅ json_repl_session 모듈 import 성공")
except ImportError as e:
    print(f"   ❌ import 실패: {e}")
    sys.exit(1)

# 2. 헬퍼 로드
print("\n2. 헬퍼 로드 테스트")
if load_helpers():
    print("   ✅ 헬퍼 로드 성공")
else:
    print("   ❌ 헬퍼 로드 실패")
    sys.exit(1)

# 3. 새로운 방식 테스트
print("\n3. 새로운 방식 (h.*) 테스트")
try:
    # 전역에서 h 객체 가져오기
    import json_repl_session
    h = getattr(json_repl_session, 'h', None)

    if h is None:
        # globals()에서 직접 가져오기
        exec("global h", json_repl_session.__dict__)
        h = json_repl_session.__dict__.get('h')

    if h:
        print(f"   h 객체 타입: {type(h)}")
        print(f"   h.read 존재: {hasattr(h, 'read')}")

        # 실제 함수 호출 테스트
        if hasattr(h, 'exists'):
            result = h.exists('readme.md')
            print(f"   h.exists('readme.md') 결과: {result}")
            print("   ✅ 새로운 방식 정상 동작")
    else:
        print("   ❌ h 객체를 찾을 수 없음")
except Exception as e:
    print(f"   ❌ 오류 발생: {e}")

# 4. 레거시 호환성 테스트
print("\n4. 레거시 호환성 테스트")
warnings.filterwarnings('always', category=DeprecationWarning)

# 레거시 함수 가져오기
read_func = json_repl_session.__dict__.get('read')
if read_func:
    print("   read 함수 발견")

    # 경고 캡처
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            # 실제로는 파일 읽기를 시도하지 않고 함수 호출만 테스트
            if callable(read_func):
                print("   read 함수 호출 가능")
                # result = read_func('readme.md')  # 실제 파일 읽기는 생략
                print("   ✅ 레거시 함수 호출 가능")

            if w:
                print(f"   ⚠️  경고 발생: {len(w)}개")
                print(f"   경고 타입: {w[0].category.__name__}")
        except Exception as e:
            print(f"   오류: {e}")
else:
    print("   ❌ read 함수를 찾을 수 없음")

# 5. 보안 테스트
print("\n5. 보안 테스트 (덮어쓰기 방지)")
if h:
    try:
        h.read = "test"
        print("   ❌ 보안 실패: 함수 덮어쓰기 가능")
    except AttributeError as e:
        print("   ✅ 보안 성공: 함수 덮어쓰기 차단됨")
        print(f"   오류 메시지: {str(e)[:50]}...")

# 6. 전역 변수 상태 확인
print("\n6. 전역 변수 상태")
global_vars = [k for k in json_repl_session.__dict__.keys() 
               if not k.startswith('_') and k not in ['sys', 'os', 'json', 'io']]
print(f"   전역 변수 개수: {len(global_vars)}")
print(f"   주요 전역 변수: {global_vars[:10]}")

# LazyHelperProxy 관련 변수
proxy_vars = [k for k in global_vars if 'proxy' in k.lower() or 'lazy' in k.lower()]
helper_vars = [k for k in global_vars if k in ['h', 'helpers']]
print(f"   프록시 관련: {proxy_vars}")
print(f"   헬퍼 객체: {helper_vars}")

print("\n=== 테스트 완료 ===")
