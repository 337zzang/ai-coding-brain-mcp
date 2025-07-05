"""
Search Helpers 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from python.ai_helpers.search_helpers import (
    list_file_paths, grep_code, scan_dir
)


def test_list_file_paths():
    """list_file_paths 테스트"""
    print("\n🧪 Test: list_file_paths")

    # Python 파일만 검색
    result = list_file_paths('.', '*.py', max_results=5)
    assert result.ok, f"Failed: {result.error}"
    assert 'paths' in result.data
    assert isinstance(result.data['paths'], list)

    print(f"✅ Found {len(result.data['paths'])} Python files")
    for path in result.data['paths'][:3]:
        print(f"  - {path}")


def test_grep_code():
    """grep_code 테스트"""
    print("\n🧪 Test: grep_code")

    # 'def' 키워드 검색
    result = grep_code('.', r'def\s+\w+', '*.py', max_results=10, context_lines=1)
    assert result.ok, f"Failed: {result.error}"
    assert 'results' in result.data
    assert isinstance(result.data['results'], dict)

    total_matches = sum(len(matches) for matches in result.data['results'].values())
    print(f"✅ Found {total_matches} function definitions in {len(result.data['results'])} files")

    # 첫 번째 결과 표시
    for filepath, matches in list(result.data['results'].items())[:1]:
        print(f"\n  📄 {filepath}:")
        for match in matches[:2]:
            print(f"    L{match['line_number']}: {match['line']}")


def test_scan_dir():
    """scan_dir 테스트"""
    print("\n🧪 Test: scan_dir")

    # Dict 형식 테스트
    result = scan_dir('.', as_dict=True)
    assert result.ok, f"Failed: {result.error}"
    assert 'files' in result.data
    assert 'directories' in result.data

    print(f"✅ Dict format: {len(result.data['files'])} files, {len(result.data['directories'])} directories")

    # Path List 형식 테스트
    result = scan_dir('.', as_dict=False)
    assert result.ok, f"Failed: {result.error}"
    assert 'paths' in result.data

    print(f"✅ Path list format: {len(result.data['paths'])} files")


if __name__ == "__main__":
    print("🚀 Search Helpers 테스트 시작")
    print("="*50)

    try:
        test_list_file_paths()
        test_grep_code()
        test_scan_dir()

        print("\n✅ 모든 테스트 통과!")
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
