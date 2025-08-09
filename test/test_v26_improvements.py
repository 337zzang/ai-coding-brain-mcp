"""
유저 프리퍼런스 v2.6 개선사항 테스트
작성일: 2025-08-09
"""

import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'python'))

import ai_helpers_new as h
from datetime import datetime


def test_fuzzy_matching():
    """Fuzzy matching 테스트"""
    print("\n[TEST] Fuzzy Matching 테스트")
    print("-" * 50)
    
    # 테스트 파일 생성
    test_file = ".temp/test_fuzzy.py"
    os.makedirs(".temp", exist_ok=True)
    
    original_code = '''def hello():
    print("World")
    return True'''
    
    h.write(test_file, original_code)
    
    # 들여쓰기가 다른 코드로 교체 시도
    old_code = '''def hello():
        print("World")  # 들여쓰기 8칸
        return True'''
    
    new_code = '''def hello():
    print("Python")
    return True'''
    
    # Fuzzy matching으로 교체
    result = h.replace(test_file, old_code, new_code, fuzzy=True)
    
    if result['ok']:
        print("[OK] Fuzzy matching 성공!")
        # 결과 확인
        updated = h.read(test_file)
        if "Python" in updated['data']:
            print("[OK] 코드가 올바르게 교체됨")
        else:
            print("[FAIL] 교체 실패")
    else:
        print(f"❌ Fuzzy matching 실패: {result.get('error', 'Unknown error')}")
    
    return result['ok']


def test_search_imports():
    """search_imports 함수 테스트"""
    print("\n[TEST] search_imports 테스트")
    print("-" * 50)
    
    try:
        # search_imports 함수 호출
        result = h.search_imports("json")
        
        if result['ok']:
            print(f"✅ search_imports 성공: {len(result['data'])}개 발견")
            # 처음 3개만 출력
            for item in result['data'][:3]:
                print(f"  - {item['file']}:{item['line']}")
        else:
            print(f"❌ search_imports 실패: {result.get('error', 'Unknown')}")
        
        return result['ok']
    except AttributeError:
        print("[FAIL] search_imports 함수를 찾을 수 없음")
        return False


def test_get_statistics():
    """get_statistics 함수 테스트"""
    print("\n[TEST] get_statistics 테스트")
    print("-" * 50)
    
    try:
        # 통계 수집
        result = h.get_statistics(".")
        
        if result['ok']:
            stats = result['data']
            print("[OK] get_statistics 성공:")
            print(f"  - Python 파일: {stats.get('python_files', 0)}개")
            print(f"  - 총 라인: {stats.get('total_lines', 0)}줄")
            print(f"  - 함수: {stats.get('total_functions', 0)}개")
            print(f"  - 클래스: {stats.get('total_classes', 0)}개")
        else:
            print(f"❌ get_statistics 실패: {result.get('error', 'Unknown')}")
        
        return result['ok']
    except AttributeError:
        print("[FAIL] get_statistics 함수를 찾을 수 없음")
        return False


def test_cache_functions():
    """캐시 관련 함수 테스트"""
    print("\n[TEST] 캐시 함수 테스트")
    print("-" * 50)
    
    try:
        # 캐시 정보 조회
        cache_info = h.get_cache_info()
        
        if cache_info['ok']:
            print("[OK] get_cache_info 성공:")
            info = cache_info['data']
            print(f"  - 캐시된 함수: {info.get('cached_functions', 0)}개")
            
            # 캐시 초기화
            clear_result = h.clear_cache()
            if clear_result['ok']:
                print(f"✅ clear_cache 성공: {clear_result['data']['count']}개 초기화")
            else:
                print("[FAIL] clear_cache 실패")
                
            return True
        else:
            print(f"❌ get_cache_info 실패: {cache_info.get('error', 'Unknown')}")
            return False
            
    except AttributeError as e:
        print(f"❌ 캐시 함수를 찾을 수 없음: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("=" * 70)
    print("Test: User Preferences v2.6 Improvements")
    print(f"Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {
        'fuzzy_matching': test_fuzzy_matching(),
        'search_imports': test_search_imports(),
        'get_statistics': test_get_statistics(),
        'cache_functions': test_cache_functions()
    }
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\n전체: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
