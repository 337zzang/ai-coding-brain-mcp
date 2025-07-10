#!/usr/bin/env python3
"""캐시 API 통합 테스트"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'python'))

def test_cache_api():
    print("=== Cache API Integration Test ===\n")
    
    try:
        # Import 테스트
        from core.context_manager import ContextManager, CacheAPI
        print("[OK] Import success: ContextManager, CacheAPI")
        
        # ContextManager 초기화
        cm = ContextManager()
        cm.initialize("test_project")
        print("[OK] ContextManager initialized")
        
        # CacheAPI 접근 테스트
        print("\n--- CacheAPI Basic Function Test ---")
        
        # 1. set/get 테스트
        cm.cache.set("test_key", "test_value")
        value = cm.cache.get("test_key")
        assert value == "test_value", f"Expected 'test_value', got {value}"
        print("[OK] Set/Get test passed")
        
        # 2. 존재 여부 확인
        exists = cm.cache.exists("test_key")
        assert exists == True, "Key should exist"
        print("[OK] Exists test passed")
        
        # 3. 기본값 테스트
        missing = cm.cache.get("missing_key", "default")
        assert missing == "default", f"Expected 'default', got {missing}"
        print("[OK] Default value test passed")
        
        # 4. 파일 의존성 테스트
        cm.cache.set_with_file_dependency("file_dep_key", {"data": "test"}, __file__)
        file_value = cm.cache.get("file_dep_key")
        assert file_value == {"data": "test"}, f"File dependency test failed"
        print("[OK] File dependency test passed")
        
        # 5. 무효화 테스트
        cm.cache.invalidate("test_key")
        after_invalidate = cm.cache.get("test_key", "not_found")
        assert after_invalidate == "not_found", "Key should be invalidated"
        print("[OK] Invalidation test passed")
        
        # 6. 통계 확인
        stats = cm.cache.get_stats()
        print(f"[OK] Cache stats: {stats}")
        
        # 7. 레거시 set_cache_with_dependencies 테스트
        cm.set_cache_with_dependencies("dep_test", {"value": 123}, [__file__])
        print("[OK] Legacy set_cache_with_dependencies test passed")
        
        # 8. 전체 클리어
        cm.cache.clear()
        after_clear = cm.cache.get("file_dep_key", "cleared")
        assert after_clear == "cleared", "Cache should be cleared"
        print("[OK] Cache clear test passed")
        
        print("\n[SUCCESS] All tests passed!")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except AssertionError as e:
        print(f"[ERROR] Test failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cache_api()
    sys.exit(0 if success else 1)
