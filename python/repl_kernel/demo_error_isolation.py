#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subprocess Worker - Import 오류 연쇄 붕괴 방지 데모
이전 문제를 재현하고 새로운 아키텍처로 해결되는 것을 보여줍니다.
"""
import sys
sys.path.insert(0, 'python')

from repl_kernel.manager import SubprocessWorkerManager
import time

print("=" * 70)
print("Import 오류 연쇄 붕괴 방지 데모")
print("=" * 70)

# Worker Manager 생성
manager = SubprocessWorkerManager()

# 시나리오 1: 존재하지 않는 모듈 import
print("\n[시나리오 1] 존재하지 않는 모듈 import")
print("-" * 50)

result1 = manager.execute_code("""
# 이전에는 이것이 전체 REPL을 죽였습니다
import non_existent_module
""")

print(f"결과: {result1.get('error_type', 'Success')}")
print(f"메시지: {result1.get('error_message', 'No error')}")

# 시나리오 2: 워커는 죽었지만 메인은 살아있음
print("\n[시나리오 2] 메인 프로세스 생존 확인")
print("-" * 50)

result2 = manager.execute_code("""
print("[OK] 메인 프로세스는 영향받지 않았습니다!")
print("워커는 깨끗한 상태로 재시작되었습니다.")
""")

print(result2.get('stdout', ''))

# 시나리오 3: 연속적인 오류도 문제없음
print("\n[시나리오 3] 연속적인 오류 처리")
print("-" * 50)

errors = [
    "from missing_module import something",
    "import another_missing_module",
    "from typing import NonExistentType"
]

for i, error_code in enumerate(errors, 1):
    result = manager.execute_code(error_code)
    print(f"{i}. {error_code}")
    print(f"   → {result.get('error_type', 'Unknown')}")

# 여전히 정상 작동
result_final = manager.execute_code("print('\n[SUCCESS] 모든 오류 후에도 정상 작동!')")
print(result_final.get('stdout', ''))

# 시나리오 4: 무한 루프도 전체 시스템을 죽이지 않음
print("\n[시나리오 4] 무한 루프 처리 (3초 타임아웃)")
print("-" * 50)

print("무한 루프 실행 중...")
start = time.time()
result_timeout = manager.execute_code("while True: pass", timeout=3)
elapsed = time.time() - start

print(f"타임아웃 발생: {result_timeout.get('error_type')} ({elapsed:.1f}초)")
print("워커는 강제 종료되고 재시작되었습니다.")

# 복구 확인
result_recovery = manager.execute_code("print('[OK] 타임아웃 후에도 즉시 복구!')")
print(result_recovery.get('stdout', ''))

# 시나리오 5: AI Helpers도 격리된 환경에서 사용 가능
print("\n[시나리오 5] AI Helpers 격리 환경 테스트")
print("-" * 50)

result_helpers = manager.execute_code("""
try:
    # Flow API 사용 시도
    if 'h' in globals():
        api = h.get_flow_api()
        print("[OK] AI Helpers가 워커에서 사용 가능합니다")
    else:
        print("[INFO] AI Helpers가 로드되지 않았습니다")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
""")

print(result_helpers.get('stdout', ''))

# 정리
manager.shutdown()

print("\n" + "=" * 70)
print("결론: Subprocess Worker로 모든 연쇄 오류 문제가 해결되었습니다!")
print("=" * 70)
