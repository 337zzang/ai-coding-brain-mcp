
import sys
import os
sys.path.insert(0, 'python')

# 새로운 search 모듈 import
from ai_helpers_new.search import (
    is_binary_file,
    search_files_generator,
    SearchNamespace,
    search_code
)

# 네임스페이스 인스턴스
search = SearchNamespace()

# 테스트 1: 파일 검색
files = search.files("*.py", ".", max_depth=0)
print(f"Test 1 - Files found: {len(files)}")

# 테스트 2: 함수 시그니처 확인
import inspect
sig = inspect.signature(search_code)
params = list(sig.parameters.keys())
print(f"Test 2 - search_code parameters: {params}")

# 테스트 3: 간단한 검색 (use_regex 없이)
try:
    result = search.code("def", ".", max_results=2)
    if result['ok']:
        print(f"Test 3 - Code search: {len(result['data'])} matches")
    else:
        print(f"Test 3 - Error: {result.get('error')}")
except Exception as e:
    print(f"Test 3 - Exception: {e}")
