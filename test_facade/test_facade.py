"""
Facade 패턴 테스트 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

print("=" * 70)
print("Facade Pattern Test")
print("=" * 70)

# Import 테스트
try:
    import ai_helpers_new as h
    print("\n[OK] Import 성공!")
    print(f"  버전: {h.__version__}")
except Exception as e:
    print(f"\n[ERROR] Import 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 네임스페이스 테스트
print("\n[TEST] 네임스페이스 테스트:")
namespaces = ['file', 'code', 'search', 'git', 'llm', 'flow', 'project']
for ns in namespaces:
    if hasattr(h, ns):
        obj = getattr(h, ns)
        print(f"  [OK] {ns}: {obj.__class__.__name__}")
    else:
        print(f"  [ERROR] {ns}: 없음")

# 새로운 방식 테스트
print("\n[TEST] 새로운 방식 테스트:")
try:
    # 파일 작업
    result = h.file.exists("README.md")
    print(f"  [OK] h.file.exists(): {result.get('ok', False)}")
    
    # 코드 분석
    result = h.code.functions("python/ai_helpers_new/facade.py")
    print(f"  [OK] h.code.functions(): {len(result.get('data', []))}개 함수")
    
    # Git 상태
    result = h.git.status()
    print(f"  [OK] h.git.status(): {result.get('ok', False)}")
    
except Exception as e:
    print(f"  [ERROR] 오류: {e}")

# 기존 방식 테스트 (deprecated)
print("\n[TEST] 기존 방식 테스트 (deprecated):")
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    
    # 기존 방식 호출
    result = h.exists("README.md")
    
    # 경고 확인
    if w:
        print(f"  [WARNING] DeprecationWarning 발생: {len(w)}개")
        print(f"     {w[0].message}")
    else:
        print(f"  [ERROR] 경고 없음 (문제)")
    
    print(f"  [OK] h.exists() 여전히 작동: {result.get('ok', False)}")

# 통계
print("\n[INFO] Facade 통계:")
stats = h.help()
print(f"  네임스페이스: {len(stats['namespaces'])}개")
print(f"  조직화된 함수: {stats['total_organized']}개")
print(f"  레거시 함수: {stats['legacy_functions']}개")

print("\n" + "=" * 70)
print("[OK] Facade 패턴 테스트 완료!")
print("=" * 70)
