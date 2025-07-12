"""
자주 사용하는 헬퍼 함수 확장
helpers 모듈에 없는 유용한 함수들
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

class HelperResult:
    """helpers 스타일의 결과 객체"""
    def __init__(self, ok: bool, data: Any = None, error: str = None):
        self.ok = ok
        self.data = data
        self.error = error
        
    def get_data(self, default=None):
        """데이터 반환 (실패시 기본값)"""
        return self.data if self.ok else default

# 디렉토리 관련
def create_directory(path: str) -> HelperResult:
    """디렉토리 생성 (중첩 디렉토리 지원)"""
    try:
        os.makedirs(path, exist_ok=True)
        return HelperResult(True, f"Directory created: {path}")
    except Exception as e:
        return HelperResult(False, None, str(e))

def list_directory(path: str = ".") -> HelperResult:
    """디렉토리 내용 목록 조회"""
    try:
        items = os.listdir(path)
        files = []
        dirs = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
            else:
                files.append(item)
        
        data = {
            "files": sorted(files),
            "directories": sorted(dirs),
            "total": len(items)
        }
        return HelperResult(True, data)
    except Exception as e:
        return HelperResult(False, None, str(e))

def delete_directory(path: str) -> HelperResult:
    """디렉토리 삭제 (내용 포함)"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            return HelperResult(True, f"Directory deleted: {path}")
        else:
            return HelperResult(False, None, "Directory not found")
    except Exception as e:
        return HelperResult(False, None, str(e))

# 파일 관련
def file_exists(path: str) -> HelperResult:
    """파일 존재 여부 확인"""
    exists = os.path.exists(path)
    return HelperResult(True, exists)

def delete_file(path: str) -> HelperResult:
    """파일 삭제"""
    try:
        if os.path.exists(path):
            os.remove(path)
            return HelperResult(True, f"File deleted: {path}")
        else:
            return HelperResult(False, None, "File not found")
    except Exception as e:
        return HelperResult(False, None, str(e))

def copy_file(src: str, dst: str) -> HelperResult:
    """파일 복사"""
    try:
        # 대상 디렉토리가 없으면 생성
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
            
        shutil.copy2(src, dst)
        return HelperResult(True, f"File copied: {src} -> {dst}")
    except Exception as e:
        return HelperResult(False, None, str(e))

def move_file(src: str, dst: str) -> HelperResult:
    """파일 이동"""
    try:
        # 대상 디렉토리가 없으면 생성
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
            
        shutil.move(src, dst)
        return HelperResult(True, f"File moved: {src} -> {dst}")
    except Exception as e:
        return HelperResult(False, None, str(e))

def get_file_size(path: str) -> HelperResult:
    """파일 크기 반환 (bytes)"""
    try:
        if os.path.exists(path):
            size = os.path.getsize(path)
            return HelperResult(True, size)
        else:
            return HelperResult(False, None, "File not found")
    except Exception as e:
        return HelperResult(False, None, str(e))

# JSON 관련
def read_json(path: str, default: Any = None) -> HelperResult:
    """JSON 파일 읽기"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return HelperResult(True, data)
    except FileNotFoundError:
        return HelperResult(True, default if default is not None else {})
    except Exception as e:
        return HelperResult(False, None, str(e))

def write_json(path: str, data: Any, indent: int = 2) -> HelperResult:
    """JSON 파일 쓰기"""
    try:
        # 디렉토리가 없으면 생성
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return HelperResult(True, f"JSON saved: {path}")
    except Exception as e:
        return HelperResult(False, None, str(e))

# 명령어 실행
def run_command(cmd: str, timeout: int = 30, encoding: str = None) -> HelperResult:
    """명령어 실행 (인코딩 문제 해결)"""
    try:
        # Windows에서 인코딩 문제 해결
        if os.name == 'nt' and encoding is None:
            encoding = 'cp949'  # Windows 한글 인코딩
            
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            timeout=timeout,
            encoding=encoding,
            errors='replace'  # 디코딩 오류 시 대체 문자 사용
        )
        
        return HelperResult(
            result.returncode == 0,
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": cmd
            }
        )
    except subprocess.TimeoutExpired:
        return HelperResult(False, None, f"Command timed out after {timeout}s")
    except Exception as e:
        return HelperResult(False, None, str(e))

# 프로젝트 정보
def get_project_name() -> HelperResult:
    """현재 프로젝트명 반환"""
    return HelperResult(True, os.path.basename(os.getcwd()))

def get_project_path() -> HelperResult:
    """현재 프로젝트 경로 반환"""
    return HelperResult(True, os.getcwd())

def get_current_branch() -> HelperResult:
    """현재 Git 브랜치 반환"""
    result = run_command("git branch --show-current")
    if result.ok:
        branch = result.get_data({}).get("stdout", "").strip()
        return HelperResult(True, branch if branch else "main")
    else:
        return HelperResult(False, "main", "Not a git repository")

# 유틸리티
def get_timestamp(format: str = "%Y%m%d_%H%M%S") -> HelperResult:
    """현재 시간 문자열 반환"""
    from datetime import datetime
    return HelperResult(True, datetime.now().strftime(format))

def backup_file(path: str, backup_dir: str = "backups") -> HelperResult:
    """파일 백업"""
    try:
        if not os.path.exists(path):
            return HelperResult(False, None, "File not found")
            
        # 백업 디렉토리 생성
        os.makedirs(backup_dir, exist_ok=True)
        
        # 백업 파일명 생성
        timestamp = get_timestamp().get_data()
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        backup_path = os.path.join(backup_dir, f"{name}_{timestamp}{ext}")
        
        # 파일 복사
        shutil.copy2(path, backup_path)
        return HelperResult(True, backup_path)
        
    except Exception as e:
        return HelperResult(False, None, str(e))

# 텍스트 파일 관련
def append_to_file(path: str, content: str) -> HelperResult:
    """파일에 내용 추가"""
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
            if not content.endswith('\n'):
                f.write('\n')
        return HelperResult(True, f"Content appended to: {path}")
    except Exception as e:
        return HelperResult(False, None, str(e))

def read_lines(path: str, start: int = 0, count: int = None) -> HelperResult:
    """파일에서 특정 라인 읽기"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if count is None:
            selected = lines[start:]
        else:
            selected = lines[start:start + count]
            
        return HelperResult(True, selected)
    except Exception as e:
        return HelperResult(False, None, str(e))

# 헬퍼 함수 등록
def register_helpers():
    """모든 헬퍼 함수를 전역으로 등록"""
    import builtins
    
    if not hasattr(builtins, 'custom_helpers'):
        builtins.custom_helpers = {}
    
    helpers = {
        # 디렉토리
        'create_directory': create_directory,
        'list_directory': list_directory,
        'delete_directory': delete_directory,
        
        # 파일
        'file_exists': file_exists,
        'delete_file': delete_file,
        'copy_file': copy_file,
        'move_file': move_file,
        'get_file_size': get_file_size,
        'append_to_file': append_to_file,
        'read_lines': read_lines,
        'backup_file': backup_file,
        
        # JSON
        'read_json': read_json,
        'write_json': write_json,
        
        # 명령어
        'run_command': run_command,
        
        # 프로젝트
        'get_project_name': get_project_name,
        'get_project_path': get_project_path,
        'get_current_branch': get_current_branch,
        
        # 유틸리티
        'get_timestamp': get_timestamp,
    }
    
    builtins.custom_helpers.update(helpers)
    
    print(f"✅ {len(helpers)}개 헬퍼 함수 등록 완료!")
    return helpers

# 모듈 로드 시 자동 등록
if __name__ != "__main__":
    register_helpers()
