"""
replace_block 함수 테스트 모음
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ai_helpers.code import replace_block


class TestReplaceBlock:
    """replace_block 함수 테스트"""
    
    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성 및 정리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_file(self, temp_dir):
        """테스트용 샘플 파일 생성"""
        file_path = os.path.join(temp_dir, "sample.py")
        content = '''
def old_function():
    """Original function"""
    return "old"

class TestClass:
    def method(self):
        """Original method"""
        return "method"
    
    @property
    def value(self):
        return self._value

@decorator
def decorated_func():
    """Decorated function"""
    return "decorated"
'''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_simple_function_replace(self, sample_file):
        """단순 함수 교체 테스트"""
        new_code = '''
def old_function():
    """Updated function"""
    return "new"
'''
        result = replace_block(sample_file, "old_function", new_code)
        
        assert result.ok is True
        assert "old_function" in result.data['message']
        assert result.data['method'] == 'AST'
        assert os.path.exists(result.data['backup_path'])
        
        # 변경 확인
        with open(sample_file, 'r') as f:
            content = f.read()
        assert "Updated function" in content
        assert "return \"new\"" in content or "return 'new'" in content
    
    def test_class_method_replace(self, sample_file):
        """클래스 메서드 교체 테스트"""
        new_code = '''
    def method(self):
        """Updated method"""
        return "updated"
'''
        result = replace_block(sample_file, "TestClass.method", new_code)
        
        assert result.ok is True
        assert result.data['method'] in ['AST', 'fallback']
        
        with open(sample_file, 'r') as f:
            content = f.read()
        assert "Updated method" in content
    
    def test_decorated_function_replace(self, sample_file):
        """데코레이터가 있는 함수 교체 테스트"""
        new_code = '''
@decorator
def decorated_func():
    """Updated decorated function"""
    return "updated_decorated"
'''
        result = replace_block(sample_file, "decorated_func", new_code)
        
        assert result.ok is True
        
        with open(sample_file, 'r') as f:
            content = f.read()
        assert "Updated decorated function" in content
    
    def test_nonexistent_function(self, sample_file):
        """존재하지 않는 함수 교체 시도"""
        result = replace_block(sample_file, "nonexistent_func", "def nonexistent_func(): pass")
        
        assert result.ok is False
        assert "찾을 수 없습니다" in result.error
        
        # 유사 항목이 제안되는지 확인
        if 'candidates' in result.data:
            assert len(result.data['candidates']) > 0
    
    def test_preserve_format_warning(self, sample_file, capsys):
        """포맷 보존 경고 테스트"""
        result = replace_block(
            sample_file, 
            "old_function", 
            "def old_function(): pass",
            preserve_format=True
        )
        
        assert result.ok is True
        # 경고 메시지가 로그에 기록되었는지는 _log 구현에 따라 다름
    
    def test_invalid_syntax(self, sample_file):
        """잘못된 문법의 새 코드"""
        invalid_code = '''
def old_function(
    # 잘못된 문법
    return "error"
'''
        result = replace_block(sample_file, "old_function", invalid_code)
        
        assert result.ok is False
        assert "유효하지 않음" in result.error or "SyntaxError" in result.error
    
    def test_file_lock(self, temp_dir):
        """파일 락 테스트 (동시 접근)"""
        file_path = os.path.join(temp_dir, "locked.py")
        with open(file_path, 'w') as f:
            f.write("def func(): pass")
        
        # 첫 번째 교체는 성공해야 함
        result1 = replace_block(file_path, "func", "def func(): return 1")
        assert result1.ok is True
        
        # 락 파일이 제대로 정리되었는지 확인
        lock_file = f"{file_path}.lock"
        assert not os.path.exists(lock_file)
    
    def test_backup_creation(self, sample_file):
        """백업 파일 생성 확인"""
        result = replace_block(sample_file, "old_function", "def old_function(): pass")
        
        assert result.ok is True
        assert 'backup_path' in result.data
        assert os.path.exists(result.data['backup_path'])
        
        # 백업 파일에 원본 내용이 있는지 확인
        with open(result.data['backup_path'], 'r') as f:
            backup_content = f.read()
        assert "Original function" in backup_content
    
    def test_compile_validation(self, temp_dir):
        """compile 검증 테스트"""
        file_path = os.path.join(temp_dir, "compile_test.py")
        with open(file_path, 'w') as f:
            f.write("def func(): return 'original'")
        
        # 정상적인 코드
        result = replace_block(file_path, "func", "def func(): return 'valid'")
        assert result.ok is True
        
        # compile은 성공하지만 실행 시 에러가 날 코드
        # (AST 파싱은 성공하지만 compile 단계에서 잡을 수 있는 에러)
        tricky_code = '''
def func():
    # 이 코드는 AST 파싱은 되지만 특정 상황에서 문제가 될 수 있음
    return "valid"
'''
        result = replace_block(file_path, "func", tricky_code)
        assert result.ok is True  # 일반적으로는 성공해야 함


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
