#!/usr/bin/env python3
"""
Test Runner
모든 통합 테스트 실행 스크립트
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# 테스트 모듈 목록
TEST_MODULES = [
    "tests.events.test_event_bus",
    "tests.events.test_integration", 
    "tests.events.test_comprehensive_integration",
    "tests.events.test_scenarios",
    "tests.events.test_performance"
]

def run_test_module(module_name):
    """개별 테스트 모듈 실행"""
    print(f"\n{'=' * 60}")
    print(f"🧪 테스트 모듈: {module_name}")
    print(f"{'=' * 60}")

    start_time = time.time()

    try:
        # Python 모듈로 실행
        result = subprocess.run(
            [sys.executable, "-m", module_name],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        duration = time.time() - start_time

        # 결과 출력
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # 성공/실패 판단
        if result.returncode == 0:
            print(f"\n✅ 성공 (실행 시간: {duration:.2f}초)")
            return True, duration
        else:
            print(f"\n❌ 실패 (종료 코드: {result.returncode})")
            return False, duration

    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")
        return False, 0


def main():
    """메인 테스트 실행기"""
    print("🚀 통합 테스트 실행기")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 버전: {sys.version}")

    # 결과 추적
    results = []
    total_duration = 0

    # 각 테스트 모듈 실행
    for module in TEST_MODULES:
        success, duration = run_test_module(module)
        results.append((module, success, duration))
        total_duration += duration

    # 최종 요약
    print(f"\n{'=' * 60}")
    print("📊 테스트 실행 요약")
    print(f"{'=' * 60}")

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"\n총 테스트 모듈: {len(results)}개")
    print(f"✅ 성공: {passed}개")
    print(f"❌ 실패: {failed}개")
    print(f"⏱️ 총 실행 시간: {total_duration:.2f}초")

    # 상세 결과
    print("\n상세 결과:")
    for module, success, duration in results:
        status = "✅" if success else "❌"
        print(f"  {status} {module} ({duration:.2f}초)")

    # 최종 결과
    if failed == 0:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n😞 {failed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
