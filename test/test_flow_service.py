"""
Flow Service 테스트
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from flow_service import FlowService, ProjectStatus
from path_utils import get_project_root, ensure_project_directory
from atomic_io import atomic_write, safe_read
from helper_result import HelperResult

class TestFlowService:
    """FlowService 테스트"""
    
    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 픽스처"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def flow_service(self, temp_dir, monkeypatch):
        """FlowService 인스턴스 픽스처"""
        monkeypatch.setenv('FLOW_PROJECT_ROOT', temp_dir)
        return FlowService()
    
    def test_switch_project(self, flow_service):
        """프로젝트 전환 테스트"""
        # Given
        project_name = "test_project"
        
        # When
        status = flow_service.switch_project(project_name)
        
        # Then
        assert isinstance(status, ProjectStatus)
        assert status.name == project_name
        assert project_name in status.path
        assert os.path.exists(status.path)
    
    def test_project_directory_creation(self, temp_dir, monkeypatch):
        """프로젝트 디렉토리 생성 테스트"""
        # Given
        monkeypatch.setenv('FLOW_PROJECT_ROOT', temp_dir)
        project_name = "new_project"
        
        # When
        project_path = ensure_project_directory(project_name)
        
        # Then
        assert project_path.exists()
        assert (project_path / 'memory').exists()
        assert (project_path / 'test').exists()
        assert (project_path / 'docs').exists()


class TestAtomicIO:
    """원자적 I/O 테스트"""
    
    def test_atomic_write_json(self, tmp_path):
        """JSON 원자적 쓰기 테스트"""
        # Given
        filepath = tmp_path / "test.json"
        data = {"test": "data", "number": 42}
        
        # When
        result = atomic_write(str(filepath), data, mode='json')
        
        # Then
        assert result is True
        assert filepath.exists()
        loaded = safe_read(str(filepath), mode='json')
        assert loaded == data
    
    def test_safe_read_default(self, tmp_path):
        """존재하지 않는 파일 읽기 테스트"""
        # Given
        filepath = tmp_path / "nonexistent.json"
        default = {"default": "value"}
        
        # When
        result = safe_read(str(filepath), default=default)
        
        # Then
        assert result == default
    
    def test_concurrent_write(self, tmp_path):
        """동시 쓰기 테스트"""
        import threading
        
        filepath = tmp_path / "concurrent.json"
        results = []
        
        def write_data(value):
            result = atomic_write(str(filepath), {"value": value})
            results.append(result)
        
        # 10개 스레드로 동시 쓰기
        threads = []
        for i in range(10):
            t = threading.Thread(target=write_data, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 모든 쓰기가 성공해야 함
        assert all(results)
        # 파일이 정상적으로 읽혀야 함
        data = safe_read(str(filepath))
        assert 'value' in data


class TestHelperResult:
    """HelperResult 테스트"""
    
    def test_success_result(self):
        """성공 결과 테스트"""
        # Given
        data = {"key": "value"}
        
        # When
        result = HelperResult.success(data)
        
        # Then
        assert result.ok is True
        assert result.data == data
        assert result.error is None
        assert bool(result) is True
    
    def test_failure_result(self):
        """실패 결과 테스트"""
        # Given
        error_msg = "Test error"
        
        # When
        result = HelperResult.failure(error_msg)
        
        # Then
        assert result.ok is False
        assert result.data is None
        assert result.error == error_msg
        assert bool(result) is False
    
    def test_from_exception(self):
        """예외로부터 결과 생성 테스트"""
        # Given
        exc = ValueError("Invalid value")
        
        # When
        result = HelperResult.from_exception(exc)
        
        # Then
        assert result.ok is False
        assert "ValueError" in result.error
        assert "Invalid value" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
