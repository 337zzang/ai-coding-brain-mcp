
# 테스트 코드 예시
def test_new_cache_structure():
    """새로운 캐시 구조 테스트"""
    import json
    import os
    
    # 1. 새 컨텍스트 생성 테스트
    from claude_code_ai_brain_v7 import UnifiedContextManager
    manager = UnifiedContextManager()
    
    test_context = manager._create_new_context()
    print("✅ 새 컨텍스트 구조:")
    print(f"   최상위 키: {list(test_context.keys())}")
    
    # 2. cache 키가 없는지 확인
    assert 'cache' not in test_context, "cache 키가 있으면 안됨!"
    assert 'work_tracking' in test_context, "work_tracking이 최상위에 있어야 함"
    assert 'analyzed_files' in test_context, "analyzed_files가 최상위에 있어야 함"
    
    # 3. 캐시 파일 경로 확인
    manager.project_name = "test_project"
    manager.memory_root = "./test_memory"
    
    paths = manager._get_cache_file_paths()
    print("\n✅ 캐시 파일 경로:")
    for name, path in paths.items():
        print(f"   {name}: {path}")
    
    print("\n✅ 모든 테스트 통과!")

# 테스트 실행
# test_new_cache_structure()
