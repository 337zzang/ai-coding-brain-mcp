"""통합 path_utils 테스트"""
import sys
sys.path.insert(0, 'python')
from path_utils_unified import *
import os

print("=== path_utils 통합 테스트 ===\n")

# 1. Desktop 경로 테스트
desktop = get_desktop_path()
print(f"1. Desktop 경로: {desktop}")
print(f"   존재 여부: {desktop.exists()}")

# 2. 프로젝트 루트 테스트
print("\n2. 프로젝트 루트 테스트:")
# 환경변수 없이
root1 = get_project_root()
print(f"   현재 디렉토리 기준: {root1}")

# 프로젝트명 지정
root2 = get_project_root("test_project")
print(f"   프로젝트명 지정: {root2}")

# 환경변수 설정 테스트
os.environ['FLOW_PROJECT_ROOT'] = 'C:\\TestRoot'
root3 = get_project_root("test_project")
print(f"   환경변수 사용: {root3}")
del os.environ['FLOW_PROJECT_ROOT']

# 3. 경로 함수 테스트
print("\n3. 경로 함수 테스트:")
paths = {
    "memory_dir": get_memory_dir(),
    "context_path": get_context_path(),
    "workflow_path": get_workflow_path(),
    "cache_dir": get_cache_dir(),
    "backup_dir": get_backup_dir(),
}

for name, path in paths.items():
    print(f"   {name}: {path}")

# 4. 호환성 테스트
print("\n4. 호환성 함수:")
mem_path = get_memory_path("test.json")
print(f"   get_memory_path('test.json'): {mem_path}")

print("\n✅ 테스트 완료!")
