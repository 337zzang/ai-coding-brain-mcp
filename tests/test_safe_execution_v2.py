#!/usr/bin/env python3
"""
Enhanced Safe Execution v2 테스트 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from safe_execution_v2 import safe_exec, check_regex, benchmark_regex_safety

def test_fstring_safety():
    """f-string 안전성 테스트"""
    print("\n=== f-string Safety Tests ===")

    tests = [
        ("Valid f-string", 'name="Alice"; f"Hello {name}"'),
        ("Undefined variable", 'f"Hello {undefined_name}"'),
        ("Format error", 'value=42; f"{value:.2fx}"'),
    ]

    for name, code in tests:
        success, msg = safe_exec(f'result = {code}; print(result)')
        print(f"\n{name}: {'✅' if success else '❌'}")
        if msg:
            print(f"  {msg}")

def test_regex_safety():
    """정규식 안전성 테스트"""
    print("\n\n=== Regex Safety Tests ===")

    patterns = [
        ("Safe pattern", r"^[a-zA-Z0-9]+$"),
        ("ReDoS risk", r"(a+)+"),
        ("Invalid syntax", r"((test)"),
    ]

    for name, pattern in patterns:
        result = check_regex(pattern)
        print(f"\n{name}: {pattern}")
        print(f"  Valid: {result['valid']}")
        if result.get('warnings'):
            for w in result['warnings']:
                print(f"  ⚠️ {w}")
        if result.get('errors'):
            for e in result['errors']:
                print(f"  ❌ {e}")

def test_performance():
    """성능 벤치마크 테스트"""
    print("\n\n=== Performance Benchmark ===")

    pattern = r"(x+)*y"
    result = benchmark_regex_safety(pattern)

    print(f"\nPattern: {pattern}")
    if result.get('warnings'):
        for w in result['warnings']:
            print(f"  ⚠️ {w}")

    if result.get('performance'):
        print("  Performance test results:")
        for p in result['performance'][:3]:
            if 'time_ms' in p:
                print(f"    Length {p['input_length']}: {p['time_ms']:.3f}ms")

if __name__ == "__main__":
    print("Enhanced Safe Execution v2 - Test Suite")
    print("=" * 50)

    test_fstring_safety()
    test_regex_safety()
    test_performance()

    print("\n\n✅ All tests completed!")
