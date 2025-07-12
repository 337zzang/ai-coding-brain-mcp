"""
통합 파일 작업 모듈 - 모든 파일 작업을 하나로 통합
중복 제거 및 성능 최적화
"""
from typing import Dict, List, Any, Optional, Union, Literal
from pathlib import Path
import shutil
import tempfile
import json
import yaml
import os
from datetime import datetime
from .helper_result import HelperResult
from .decorators import track_operation

# 파일 작업 타입 정의
FileOperation = Literal['read', 'write', 'append', 'create', 'delete', 'copy', 'move']
FileFormat = Literal['text', 'json', 'yaml', 'binary']


class UnifiedFileOperations:
    """통합 파일 작업 클래스"""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.backup_dir = Path.home() / '.ai-coding-brain' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def file_operation(self,
                      file_path: str,
                      operation: FileOperation,
                      content: Optional[Union[str, bytes, dict]] = None,
                      format: FileFormat = 'text',
                      encoding: Optional[str] = None,
                      backup: bool = False,
                      atomic: bool = True,
                      mode: Optional[str] = None) -> HelperResult:
        """
        통합 파일 작업 함수
        
        Args:
            file_path: 파일 경로
            operation: 작업 타입 ('read', 'write', 'append', 'create', 'delete', 'copy', 'move')
            content: 파일 내용 (write/append/create 시 사용)
            format: 파일 형식 ('text', 'json', 'yaml', 'binary')
            encoding: 인코딩 (기본: utf-8)
            backup: 백업 생성 여부
            atomic: 원자적 쓰기 여부
            mode: 파일 권한 모드
            
        Returns:
            HelperResult with operation result
        """
        try:
            path = Path(file_path).resolve()
            encoding = encoding or self.encoding
            
            # 백업 처리
            if backup and path.exists() and operation in ['write', 'append', 'delete']:
                self._create_backup(path)
            
            # 작업별 처리
            if operation == 'read':
                return self._read_file(path, format, encoding)
            elif operation == 'write':
                return self._write_file(path, content, format, encoding, atomic, mode)
            elif operation == 'append':
                return self._append_file(path, content, format, encoding)
            elif operation == 'create':
                return self._create_file(path, content, format, encoding, mode)
            elif operation == 'delete':
                return self._delete_file(path)
            elif operation == 'copy':
                if not content:
                    return HelperResult(False, error="Destination path required for copy")
                return self._copy_file(path, content)
            elif operation == 'move':
                if not content:
                    return HelperResult(False, error="Destination path required for move")
                return self._move_file(path, content)
            else:
                return HelperResult(False, error=f"Unknown operation: {operation}")
                
        except Exception as e:
            return HelperResult(False, error=f"File operation failed: {str(e)}")
    
    def _read_file(self, path: Path, format: FileFormat, encoding: str) -> HelperResult:
        """파일 읽기 구현"""
        if not path.exists():
            return HelperResult(False, error=f"File not found: {path}")
        
        try:
            if format == 'binary':
                with open(path, 'rb') as f:
                    content = f.read()
            elif format == 'json':
                with open(path, 'r', encoding=encoding) as f:
                    content = json.load(f)
            elif format == 'yaml':
                with open(path, 'r', encoding=encoding) as f:
                    content = yaml.safe_load(f)
            else:  # text
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
            
            return HelperResult(True, data={
                'content': content,
                'path': str(path),
                'size': path.stat().st_size,
                'modified': path.stat().st_mtime,
                'format': format
            })
            
        except UnicodeDecodeError:
            # 인코딩 오류 시 바이너리로 재시도
            if format == 'text':
                return self._read_file(path, 'binary', encoding)
            raise
    
    def _write_file(self, path: Path, content: Any, format: FileFormat,
                   encoding: str, atomic: bool, mode: Optional[str]) -> HelperResult:
        """파일 쓰기 구현"""
        try:
            # 부모 디렉토리 생성
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 내용 준비
            if format == 'json':
                content = json.dumps(content, ensure_ascii=False, indent=2)
            elif format == 'yaml':
                content = yaml.dump(content, allow_unicode=True, default_flow_style=False)
            
            # 원자적 쓰기
            if atomic:
                with tempfile.NamedTemporaryFile(mode='w' if format != 'binary' else 'wb',
                                               encoding=encoding if format != 'binary' else None,
                                               dir=path.parent,
                                               delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                # 원자적 이동
                shutil.move(tmp_path, str(path))
            else:
                # 일반 쓰기
                mode_str = 'wb' if format == 'binary' else 'w'
                with open(path, mode_str, encoding=encoding if format != 'binary' else None) as f:
                    f.write(content)
            
            # 권한 설정
            if mode:
                os.chmod(path, int(mode, 8))
            
            return HelperResult(True, data={
                'path': str(path),
                'size': len(content) if isinstance(content, (str, bytes)) else None,
                'format': format
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Write failed: {str(e)}")
    
    def _append_file(self, path: Path, content: Any, format: FileFormat,
                    encoding: str) -> HelperResult:
        """파일 추가 구현"""
        if not path.exists():
            return self._create_file(path, content, format, encoding, None)
        
        try:
            if format == 'json':
                # JSON 파일은 읽어서 수정 후 다시 쓰기
                existing = self._read_file(path, 'json', encoding)
                if existing.ok:
                    if isinstance(existing.data['content'], list) and isinstance(content, list):
                        existing.data['content'].extend(content)
                    elif isinstance(existing.data['content'], dict) and isinstance(content, dict):
                        existing.data['content'].update(content)
                    else:
                        return HelperResult(False, error="Cannot append incompatible JSON types")
                    
                    return self._write_file(path, existing.data['content'], 'json',
                                          encoding, True, None)
            else:
                # 텍스트/바이너리 추가
                mode = 'ab' if format == 'binary' else 'a'
                with open(path, mode, encoding=encoding if format != 'binary' else None) as f:
                    f.write(content)
                
                return HelperResult(True, data={
                    'path': str(path),
                    'appended': len(content) if isinstance(content, (str, bytes)) else None
                })
                
        except Exception as e:
            return HelperResult(False, error=f"Append failed: {str(e)}")
    
    def _create_file(self, path: Path, content: Any, format: FileFormat,
                    encoding: str, mode: Optional[str]) -> HelperResult:
        """파일 생성 구현"""
        if path.exists():
            return HelperResult(False, error=f"File already exists: {path}")
        
        return self._write_file(path, content or "", format, encoding, True, mode)
    
    def _delete_file(self, path: Path) -> HelperResult:
        """파일 삭제 구현"""
        if not path.exists():
            return HelperResult(False, error=f"File not found: {path}")
        
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            
            return HelperResult(True, data={
                'deleted': str(path),
                'type': 'file' if path.is_file() else 'directory'
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Delete failed: {str(e)}")
    
    def _copy_file(self, source: Path, dest: Union[str, Path]) -> HelperResult:
        """파일 복사 구현"""
        if not source.exists():
            return HelperResult(False, error=f"Source not found: {source}")
        
        try:
            dest_path = Path(dest)
            
            # 디렉토리로 복사하는 경우
            if dest_path.is_dir():
                dest_path = dest_path / source.name
            
            # 부모 디렉토리 생성
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source.is_file():
                shutil.copy2(source, dest_path)
            else:
                shutil.copytree(source, dest_path)
            
            return HelperResult(True, data={
                'source': str(source),
                'destination': str(dest_path),
                'size': source.stat().st_size if source.is_file() else None
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Copy failed: {str(e)}")
    
    def _move_file(self, source: Path, dest: Union[str, Path]) -> HelperResult:
        """파일 이동 구현"""
        if not source.exists():
            return HelperResult(False, error=f"Source not found: {source}")
        
        try:
            dest_path = Path(dest)
            
            # 디렉토리로 이동하는 경우
            if dest_path.is_dir():
                dest_path = dest_path / source.name
            
            # 부모 디렉토리 생성
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(dest_path))
            
            return HelperResult(True, data={
                'source': str(source),
                'destination': str(dest_path),
                'type': 'file' if source.is_file() else 'directory'
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Move failed: {str(e)}")
    
    def _create_backup(self, path: Path) -> Optional[Path]:
        """백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.name}.{timestamp}.bak"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(path, backup_path)
            return backup_path
            
        except Exception:
            return None
    
    # 편의 메서드들
    def read_lines(self, file_path: str, start: int = 0,
                   end: Optional[int] = None) -> HelperResult:
        """파일을 라인 단위로 읽기"""
        result = self.file_operation(file_path, 'read')
        if not result.ok:
            return result
        
        lines = result.data['content'].splitlines()
        selected_lines = lines[start:end]
        
        return HelperResult(True, data={
            'lines': selected_lines,
            'total_lines': len(lines),
            'start': start,
            'end': end or len(lines)
        })
    
    def file_info(self, file_path: str) -> HelperResult:
        """파일 정보 조회"""
        try:
            path = Path(file_path).resolve()
            if not path.exists():
                return HelperResult(False, error=f"File not found: {file_path}")
            
            stat = path.stat()
            
            info = {
                'path': str(path),
                'name': path.name,
                'size': stat.st_size,
                'size_human': self._human_size(stat.st_size),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'is_symlink': path.is_symlink(),
                'suffix': path.suffix,
                'parent': str(path.parent)
            }
            
            # 텍스트 파일인 경우 라인 수 추가
            if path.is_file() and path.suffix in ['.txt', '.py', '.js', '.json', '.yaml', '.md']:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        info['line_count'] = sum(1 for _ in f)
                except Exception:
                    info['line_count'] = None
            
            return HelperResult(True, data=info)
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to get file info: {str(e)}")
    
    def _human_size(self, size: int) -> str:
        """사람이 읽기 쉬운 크기 형식"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


# 전역 인스턴스
_file_ops = UnifiedFileOperations()


# 공개 API 함수들 (간단한 인터페이스)
def read_file(file_path: str, format: FileFormat = 'text', **kwargs) -> HelperResult:
    """파일 읽기"""
    return _file_ops.file_operation(file_path, 'read', format=format, **kwargs)


def write_file(file_path: str, content: Any, format: FileFormat = 'text', **kwargs) -> HelperResult:
    """파일 쓰기"""
    return _file_ops.file_operation(file_path, 'write', content=content, format=format, **kwargs)


def append_to_file(file_path: str, content: Any, format: FileFormat = 'text', **kwargs) -> HelperResult:
    """파일에 추가"""
    return _file_ops.file_operation(file_path, 'append', content=content, format=format, **kwargs)


def create_file(file_path: str, content: Any = "", format: FileFormat = 'text', **kwargs) -> HelperResult:
    """파일 생성"""
    return _file_ops.file_operation(file_path, 'create', content=content, format=format, **kwargs)


def delete_file(file_path: str, backup: bool = False) -> HelperResult:
    """파일 삭제"""
    return _file_ops.file_operation(file_path, 'delete', backup=backup)


def copy_file(source: str, destination: str) -> HelperResult:
    """파일 복사"""
    return _file_ops.file_operation(source, 'copy', content=destination)


def move_file(source: str, destination: str) -> HelperResult:
    """파일 이동"""
    return _file_ops.file_operation(source, 'move', content=destination)


def file_exists(file_path: str) -> bool:
    """파일 존재 여부 확인"""
    return Path(file_path).exists()


def get_file_info(file_path: str) -> HelperResult:
    """파일 정보 조회"""
    return _file_ops.file_info(file_path)


def read_lines(file_path: str, start: int = 0, end: Optional[int] = None) -> HelperResult:
    """파일을 라인 단위로 읽기"""
    return _file_ops.read_lines(file_path, start, end)


# JSON/YAML 편의 함수
def read_json(file_path: str) -> HelperResult:
    """JSON 파일 읽기"""
    return read_file(file_path, format='json')


def write_json(file_path: str, data: dict, **kwargs) -> HelperResult:
    """JSON 파일 쓰기"""
    return write_file(file_path, data, format='json', **kwargs)


def read_yaml(file_path: str) -> HelperResult:
    """YAML 파일 읽기"""
    return read_file(file_path, format='yaml')


def write_yaml(file_path: str, data: dict, **kwargs) -> HelperResult:
    """YAML 파일 쓰기"""
    return write_file(file_path, data, format='yaml', **kwargs)