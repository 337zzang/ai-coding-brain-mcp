"""
AI Coding Brain 테스트 설정
"""
import sys
import os
import pytest
from typing import Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_path = os.path.join(project_root, 'python')
if python_path not in sys.path:
    sys.path.insert(0, python_path)

@pytest.fixture
def temp_project_dir(tmp_path):
    """임시 프로젝트 디렉토리 생성"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # 기본 구조 생성
    (project_dir / ".cache").mkdir()
    (project_dir / "src").mkdir()
    
    return project_dir

@pytest.fixture
def mock_context():
    """테스트용 컨텍스트"""
    return {
        'project_name': 'test_project',
        'project_root': '/test/path',
        'cache_dir': '/test/path/.cache',
        'analyzed_files': {},
        'tasks': {'pending': [], 'completed': []},
        'current_plan': None
    }

@pytest.fixture
def sample_python_file(tmp_path):
    """샘플 Python 파일 생성"""
    file_path = tmp_path / "sample.py"
    content = """
def hello_world():
    """샘플 함수"""
    print("Hello, World!")
    
class SampleClass:
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
"""
    file_path.write_text(content)
    return file_path
