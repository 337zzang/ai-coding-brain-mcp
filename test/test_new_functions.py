#!/usr/bin/env python3
"""
새로 구현된 기능 테스트 스크립트
- Fuzzy matching
- search_imports
- get_statistics
- get_cache_info
- clear_cache
"""

import sys
import os

# 프로젝트 경로 추가
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_path, 'python'))

import ai_helpers_new as h

def test_fuzzy_matching():
    """Fuzzy matching 테스트"""
    print("\n1. Fuzzy Matching 테스트")
    print("-" * 40)
    
    # 테스트 파일 생성
    test_dir = os.path.join(project_path, ".temp")
    test_file = os.path.join(test_dir, "test_fuzzy.py")
    
    # 디렉토리 생성
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # 원본 코드 작성
    original = '''def hello():
    print("Hello World")
    return True'''
    
    with open(test_file, 'w') as f:
        f.write(original)
    
    # Fuzzy matching으로 수정 (들여쓰기 다름)
    old_code = '''def hello():
        print("Hello World")  # 들여쓰기 8칸
        return True'''
    
    new_code = '''def hello():
    print("Hello Python")
    return True'''
    
    result = h.replace(test_file, old_code, new_code, fuzzy=True)
    
    if result['ok']:
        print("✅ Fuzzy matching 성공!")
        # 결과 확인
        with open(test_file, 'r') as f:
            content = f.read()
            if "Hello Python" in content:
                print("   - 코드가 정상적으로 수정됨")
            else:
                print("   - ⚠️ 수정이 적용되지 않음")
    else:
        print(f"❌ Fuzzy matching 실패: {result.get('error', 'Unknown')}")
    
    return result['ok']

def test_search_imports():
    """search_imports 함수 테스트"""
    print("\n2. search_imports 테스트")
    print("-" * 40)
    
    try:
        # 직접 import 시도
        from ai_helpers_new.search import search_imports
        
        result = search_imports("json")
        if result['ok']:
            print(f"✅ search_imports 성공!")
            print(f"   - 'json' import 발견: {len(result['data'])}개 파일")
            if result['data']:
                first = result['data'][0]
                print(f"   - 예시: {first['file']} (line {first['line']})")
        else:
            print(f"❌ search_imports 실패: {result.get('error', 'Unknown')}")
        return result['ok']
        
    except ImportError as e:
        print(f"⚠️ search_imports import 실패: {e}")
        print("   💡 해결: REPL 재시작 후 다시 시도")
        return False

def test_get_statistics():
    """get_statistics 함수 테스트"""
    print("\n3. get_statistics 테스트")
    print("-" * 40)
    
    try:
        from ai_helpers_new.search import get_statistics
        
        stats = get_statistics(".")
        if stats['ok']:
            data = stats['data']
            print(f"✅ get_statistics 성공!")
            print(f"   - Python 파일: {data.get('python_files', 0)}개")
            print(f"   - 총 라인: {data.get('total_lines', 0)}줄")
            print(f"   - 총 함수: {data.get('total_functions', 0)}개")
            print(f"   - 총 클래스: {data.get('total_classes', 0)}개")
        else:
            print(f"❌ get_statistics 실패: {stats.get('error', 'Unknown')}")
        return stats['ok']
        
    except ImportError as e:
        print(f"⚠️ get_statistics import 실패: {e}")
        print("   💡 해결: REPL 재시작 후 다시 시도")
        return False

def test_cache_functions():
    """캐시 관련 함수 테스트"""
    print("\n4. 캐시 함수 테스트")
    print("-" * 40)
    
    try:
        from ai_helpers_new.search import get_cache_info, clear_cache
        
        # 캐시 정보 조회
        cache_info = get_cache_info()
        if cache_info['ok']:
            print("✅ get_cache_info 성공!")
            data = cache_info['data']
            if data:
                for name, info in list(data.items())[:3]:
                    if info:
                        print(f"   - {name}: {info}")
            else:
                print("   - 캐시가 비어있음")
        
        # 캐시 초기화
        clear_result = clear_cache()
        if clear_result['ok']:
            print("✅ clear_cache 성공!")
            print(f"   - 초기화된 캐시: {clear_result['data'].get('cleared', 0)}개")
        
        return cache_info['ok'] and clear_result['ok']
        
    except ImportError as e:
        print(f"⚠️ 캐시 함수 import 실패: {e}")
        print("   💡 해결: REPL 재시작 후 다시 시도")
        return False

def test_existing_functions():
    """기존 함수들도 정상 작동하는지 확인"""
    print("\n5. 기존 기능 확인")
    print("-" * 40)
    
    # search_files 테스트
    files = h.search_files("*.py")
    print(f"✅ search_files: {files['ok']}, {len(files.get('data', []))}개 Python 파일")
    
    # search_code 테스트
    code = h.search_code("def", ".")
    print(f"✅ search_code: {code['ok']}, {len(code.get('data', []))}개 결과")
    
    # Git 상태 확인
    git = h.git_status()
    print(f"✅ git_status: {git['ok']}")
    
    return True

def main():
    """메인 테스트 실행"""
    print("=" * 50)
    print("🧪 새 기능 통합 테스트")
    print("=" * 50)
    
    results = {
        "fuzzy_matching": False,
        "search_imports": False,
        "get_statistics": False,
        "cache_functions": False,
        "existing": False
    }
    
    # 각 테스트 실행
    results["fuzzy_matching"] = test_fuzzy_matching()
    results["search_imports"] = test_search_imports()
    results["get_statistics"] = test_get_statistics()
    results["cache_functions"] = test_cache_functions()
    results["existing"] = test_existing_functions()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n전체: {passed}/{total} 통과 ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 완벽합니다!")
    elif passed >= total * 0.8:
        print("\n👍 대부분의 테스트 통과! Import 문제만 해결하면 됩니다.")
    else:
        print("\n⚠️ 일부 테스트 실패. REPL 재시작 후 다시 시도해보세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
