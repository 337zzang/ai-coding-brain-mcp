"""
통합 헬퍼 함수 테스트
리팩토링된 모듈들의 기능 검증
"""
import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ai_helpers import (
    # File operations
    read_file, write_file, create_file, delete_file,
    read_json, write_json, get_file_info,
    # Search operations
    search_files, search_code, find_function, find_class,
    scan_directory, grep,
    # Code operations
    parse_code, replace_function, get_code_snippet,
    # Git operations
    git_status, is_git_repository
)


class TestUnifiedFileOperations(unittest.TestCase):
    """파일 작업 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.txt")
    
    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_file_crud_operations(self):
        """파일 CRUD 작업 테스트"""
        # Create
        result = create_file(self.test_file, "Hello, World!")
        self.assertTrue(result.ok)
        
        # Read
        result = read_file(self.test_file)
        self.assertTrue(result.ok)
        self.assertEqual(result.data['content'], "Hello, World!")
        
        # Update
        result = write_file(self.test_file, "Updated content")
        self.assertTrue(result.ok)
        
        # Delete
        result = delete_file(self.test_file)
        self.assertTrue(result.ok)
        self.assertFalse(os.path.exists(self.test_file))
    
    def test_json_operations(self):
        """JSON 파일 작업 테스트"""
        json_file = os.path.join(self.test_dir, "test.json")
        test_data = {"name": "test", "value": 123, "items": ["a", "b", "c"]}
        
        # Write JSON
        result = write_json(json_file, test_data)
        self.assertTrue(result.ok)
        
        # Read JSON
        result = read_json(json_file)
        self.assertTrue(result.ok)
        self.assertEqual(result.data['content'], test_data)
    
    def test_file_info(self):
        """파일 정보 조회 테스트"""
        create_file(self.test_file, "Test content\nLine 2\nLine 3")
        
        result = get_file_info(self.test_file)
        self.assertTrue(result.ok)
        self.assertEqual(result.data['name'], "test.txt")
        self.assertEqual(result.data['line_count'], 3)
        self.assertIn('size_human', result.data)


class TestUnifiedSearchOperations(unittest.TestCase):
    """검색 작업 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        
        # 테스트 파일 생성
        self.py_file = os.path.join(self.test_dir, "test.py")
        with open(self.py_file, 'w') as f:
            f.write('''
def hello_world():
    """Test function"""
    print("Hello, World!")

class TestClass:
    def test_method(self):
        pass
''')
    
    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_search_files(self):
        """파일 검색 테스트"""
        result = search_files(self.test_dir, "*.py")
        self.assertTrue(result.ok)
        self.assertEqual(result.data['count'], 1)
    
    def test_search_code(self):
        """코드 검색 테스트"""
        result = search_code(self.test_dir, "hello", "*.py")
        self.assertTrue(result.ok)
        self.assertGreater(result.data['total_matches'], 0)
    
    def test_find_function(self):
        """함수 찾기 테스트"""
        result = find_function(self.test_dir, "hello_world")
        self.assertTrue(result.ok)
        self.assertEqual(result.data['count'], 1)
    
    def test_find_class(self):
        """클래스 찾기 테스트"""
        result = find_class(self.test_dir, "TestClass")
        self.assertTrue(result.ok)
        self.assertEqual(result.data['count'], 1)
    
    def test_scan_directory(self):
        """디렉토리 스캔 테스트"""
        result = scan_directory(self.test_dir)
        self.assertTrue(result.ok)
        self.assertIn('tree', result.data)
        self.assertIn('files', result.data)


class TestUnifiedCodeOperations(unittest.TestCase):
    """코드 작업 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.py_file = os.path.join(self.test_dir, "test_code.py")
        
        with open(self.py_file, 'w') as f:
            f.write('''
def old_function():
    """Old function"""
    return "old"

class MyClass:
    def old_method(self):
        return "old method"
''')
    
    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_parse_code(self):
        """코드 파싱 테스트"""
        result = parse_code(self.py_file)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data['functions']), 1)
        self.assertEqual(len(result.data['classes']), 1)
        self.assertEqual(result.data['functions'][0]['name'], 'old_function')
    
    def test_get_code_snippet(self):
        """코드 스니펫 가져오기 테스트"""
        result = get_code_snippet(self.py_file, "old_function", "function")
        self.assertTrue(result.ok)
        self.assertIn('snippet', result.data)
        self.assertIn('old_function', result.data['snippet'])


class TestGitOperations(unittest.TestCase):
    """Git 작업 테스트"""
    
    def test_git_status(self):
        """Git 상태 확인 테스트"""
        # 현재 디렉토리가 git 저장소인 경우만 테스트
        if is_git_repository():
            result = git_status()
            self.assertTrue(result.ok)
            self.assertIn('modified', result.data)
            self.assertIn('untracked', result.data)


class TestBackwardCompatibility(unittest.TestCase):
    """하위 호환성 테스트"""
    
    def test_legacy_aliases(self):
        """레거시 별칭 테스트"""
        from ai_helpers import (
            search_files_advanced,
            search_code_content,
            scan_directory_dict
        )
        
        # 별칭이 제대로 작동하는지 확인
        self.assertTrue(callable(search_files_advanced))
        self.assertTrue(callable(search_code_content))
        self.assertTrue(callable(scan_directory_dict))


if __name__ == '__main__':
    unittest.main()