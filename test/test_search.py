"""
search.py 모듈 테스트
"""
import unittest
import os
import sys
import tempfile
import shutil

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.ai_helpers.search import (
    scan_directory_dict,
    search_files_advanced,
    search_code_content
)


class TestSearchFunctions(unittest.TestCase):
    """검색 함수들 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        
        # 테스트 파일들 생성
        self.test_files = {
            'test1.py': 'def hello():\n    return "Hello"\n',
            'test2.txt': 'This is a test file\nWith multiple lines\n',
            'subdir/test3.py': 'class TestClass:\n    pass\n',
            'subdir/test4.md': '# Test Markdown\n\nContent here\n'
        }
        
        # 파일 생성
        for path, content in self.test_files.items():
            full_path = os.path.join(self.test_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.test_dir)
    
    def test_scan_directory_dict(self):
        """scan_directory_dict 함수 테스트"""
        result = scan_directory_dict(self.test_dir)
        
        # 기본 구조 확인
        self.assertIn('files', result)
        self.assertIn('directories', result)
        self.assertIn('stats', result)
        
        # 파일이 리스트 형태인지 확인 (새로운 형식)
        self.assertIsInstance(result['files'], list)
        self.assertIsInstance(result['directories'], list)
        
        # 파일 개수 확인
        self.assertEqual(len(result['files']), 2)  # test1.py, test2.txt
        self.assertEqual(len(result['directories']), 1)  # subdir
        
        # 파일 구조 확인
        if result['files']:
            file_info = result['files'][0]
            self.assertIn('name', file_info)
            self.assertIn('path', file_info)
            self.assertIn('size', file_info)
    
    def test_search_files_advanced(self):
        """search_files_advanced 함수 테스트"""
        # .py 파일 검색
        result = search_files_advanced(self.test_dir, "*.py")
        
        self.assertIn('results', result)
        py_files = result['results']
        self.assertEqual(len(py_files), 2)  # test1.py, test3.py
        
        # 파일명에 test가 포함된 파일 검색
        result = search_files_advanced(self.test_dir, "*test*")
        self.assertEqual(len(result['results']), 4)  # 모든 테스트 파일
    
    def test_search_code_content(self):
        """search_code_content 함수 테스트"""
        # 'def' 키워드 검색
        result = search_code_content(self.test_dir, "def", "*.py")
        
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)  # test1.py만 해당
        
        # 'class' 키워드 검색
        result = search_code_content(self.test_dir, "class", "*.py")
        self.assertEqual(len(result['results']), 1)  # test3.py만 해당


if __name__ == '__main__':
    unittest.main()
