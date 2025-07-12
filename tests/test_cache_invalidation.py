#!/usr/bin/env python3
"""
캐시 무효화 메커니즘 테스트
"""
import sys
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, '.')

from python.core.cache_manager import CacheManager, get_cache_manager
from python.core.context_manager import get_context_manager


def test_cache_manager():
    """CacheManager 단독 테스트"""
    print("🧪 CacheManager 테스트\n")
    
    # 임시 캐시 디렉토리
    cache_dir = Path("memory/test_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 캐시 매니저 생성
    cache = CacheManager(cache_dir)
    
    # 1. 기본 set/get 테스트
    print("1️⃣ 기본 캐시 작동 테스트:")
    cache.set("test_key", {"data": "test_value"})
    value = cache.get("test_key")
    print(f"   저장/조회: {'✅' if value and value['data'] == 'test_value' else '❌'}")
    
    # 2. 의존성 추가 테스트
    print("\n2️⃣ 파일 의존성 테스트:")
    test_file = Path("test_dependency.txt")
    test_file.write_text("initial content")
    
    # 캐시 설정 with 의존성
    cache.set("dep_test", {"value": "cached"}, dependencies=[test_file])
    print(f"   의존성 추가: ✅")
    
    # 파일 변경 전 캐시 확인
    value = cache.get("dep_test")
    print(f"   파일 변경 전: {'✅ 캐시 유효' if value else '❌ 캐시 없음'}")
    
    # 파일 변경
    time.sleep(0.1)  # 타임스탬프 차이 보장
    test_file.write_text("changed content")
    
    # 파일 변경 후 캐시 확인
    value = cache.get("dep_test")
    print(f"   파일 변경 후: {'✅ 캐시 무효화됨' if not value else '❌ 캐시 여전히 유효'}")
    
    # 3. 파일별 무효화 테스트
    print("\n3️⃣ 파일별 무효화 테스트:")
    cache.set("cache1", "value1", dependencies=[test_file])
    cache.set("cache2", "value2", dependencies=[test_file])
    cache.set("cache3", "value3")  # 의존성 없음
    
    # 파일 변경으로 무효화
    test_file.write_text("trigger invalidation")
    invalidated = cache.invalidate_by_file(test_file)
    print(f"   무효화된 캐시: {invalidated}")
    print(f"   예상: 2개, 실제: {len(invalidated)}개 {'✅' if len(invalidated) == 2 else '❌'}")
    
    # 4. 통계 확인
    print("\n4️⃣ 캐시 통계:")
    stats = cache.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 정리
    test_file.unlink(missing_ok=True)
    cache.clear_all()
    

def test_context_manager_integration():
    """ContextManager와 통합 테스트"""
    print("\n\n🧪 ContextManager 통합 테스트\n")
    
    # 컨텍스트 매니저 초기화
    ctx = get_context_manager()
    ctx.initialize("test_project")
    
    # 1. 캐시 매니저 초기화 확인
    print("1️⃣ 캐시 매니저 통합:")
    print(f"   캐시 매니저 활성화: {'✅' if ctx._cache_manager else '❌'}")
    
    # 2. 캐시와 함께 컨텍스트 업데이트
    print("\n2️⃣ 컨텍스트 캐시 테스트:")
    ctx.update_context("test_data", {"important": "value"})
    
    # 캐시에서 조회
    cached = ctx.get_value("test_data")
    print(f"   캐시 조회: {'✅' if cached and cached['important'] == 'value' else '❌'}")
    
    # 3. 파일 추적과 캐시 무효화
    print("\n3️⃣ 파일 추적 캐시 무효화:")
    test_file = Path("tracked_file.py")
    test_file.write_text("# test file")
    
    # 의존성과 함께 캐시 설정
    ctx.set_cache_with_dependencies(
        "file_cache", 
        {"content": "cached data"}, 
        [str(test_file)]
    )
    
    # 파일 추적 (캐시 무효화 트리거)
    print("   파일 추적 전 캐시 상태...")
    test_file.write_text("# modified")
    ctx.track_file_access(str(test_file))
    
    # 4. 캐시 통계
    print("\n4️⃣ 통합 캐시 통계:")
    stats = ctx.get_cache_statistics()
    for key, value in stats.items():
        if not key.startswith('_'):
            print(f"   {key}: {value}")
    
    # 정리
    test_file.unlink(missing_ok=True)
    

def main():
    """메인 테스트 실행"""
    print("🚀 캐시 무효화 메커니즘 테스트 시작\n")
    
    try:
        # CacheManager 단독 테스트
        test_cache_manager()
        
        # ContextManager 통합 테스트
        test_context_manager_integration()
        
        print("\n\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
