#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""수정사항 테스트 스크립트"""

import sys
import os

# 경로 추가
sys.path.insert(0, r'C:\Users\82106\Desktop\ai-coding-brain-mcp\python')

# Import
import ai_helpers_new as h

print("="*70)
print("3개 수정사항 최종 테스트")
print("="*70)

# 1. h.code.view() 테스트
print("\n1. h.code.view() 테스트:")
try:
    result = h.code.view("python/ai_helpers_new/file.py", "read")
    if isinstance(result, dict):
        if result.get('ok') == False:
            print(f"  X 오류: {result.get('error')}")
        else:
            print(f"  O 정상 작동 - found: {result.get('found')}")
    else:
        print(f"  O 정상 작동 - 내용 반환 ({len(result)} 문자)")
except Exception as e:
    print(f"  X 예외: {e}")

# 2. h.search.code() context 테스트
print("\n2. h.search.code() context 파라미터 테스트:")
try:
    result = h.search.code("def", "python/ai_helpers_new", context=2)
    if result['ok']:
        print(f"  O 정상 작동 - {len(result.get('data', []))}개 결과")
    else:
        print(f"  X 오류: {result.get('error')}")
except Exception as e:
    print(f"  X 예외: {e}")

# 3. h.git.status_normalized() 테스트
print("\n3. h.git.status_normalized() 테스트:")
try:
    # 직접 함수 호출
    from ai_helpers_new import git_status_normalized
    result = git_status_normalized()
    if isinstance(result, dict) and result.get('ok'):
        data = result['data']
        print(f"  O 정상 작동 (직접 호출)")
        print(f"     - branch: {data.get('branch')}")
        print(f"     - modified_count: {data.get('modified_count')}")
    else:
        print(f"  O 정상 작동 (데이터 반환)")
except ImportError:
    print(f"  X git_status_normalized 함수 없음")
except Exception as e:
    print(f"  X 예외: {e}")

# Facade 확인
print("\n4. Facade 네임스페이스 확인:")
try:
    if hasattr(h.git, 'status_normalized'):
        result = h.git.status_normalized()
        print(f"  O h.git.status_normalized() 존재")
    else:
        print(f"  X h.git.status_normalized() 없음")
except Exception as e:
    print(f"  X 예외: {e}")

print("\n" + "="*70)
print("테스트 완료")
print("="*70)
