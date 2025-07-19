"""
AI Helpers File Module
파일 읽기/쓰기를 위한 단순하고 실용적인 함수들
"""
from pathlib import Path
import json
import shutil
from ai_helpers_new.util import ok, err
from typing import Any, Dict


def read(path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """파일을 읽어서 내용 반환

    Returns:
        성공: {'ok': True, 'data': 내용, 'path': 경로, 'lines': 줄수, 'size': 크기}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        p = Path(path)
        if not p.exists():
            return err(f"File not found: {path}", path=path)

        content = p.read_text(encoding=encoding)
        stat = p.stat()

        return ok(
            content,
            path=str(p.absolute()),
            lines=content.count('\n') + 1,
            size=stat.st_size,
            encoding=encoding
        )
    except Exception as e:
        return err(str(e), path=path)


def write(path: str, content: str, encoding: str = 'utf-8', backup: bool = False) -> Dict[str, Any]:
    """파일에 내용 쓰기

    Returns:
        성공: {'ok': True, 'data': 쓴 바이트 수, 'path': 경로}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        p = Path(path)

        # 백업 옵션
        if backup and p.exists():
            backup_path = f"{p}.backup"
            shutil.copy2(p, backup_path)

        # 디렉토리 생성
        p.parent.mkdir(parents=True, exist_ok=True)

        # 파일 쓰기
        p.write_text(content, encoding=encoding)

        return ok(
            len(content),
            path=str(p.absolute()),
            lines=content.count('\n') + 1
        )
    except Exception as e:
        return err(str(e), path=path)


def append(path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """파일에 내용 추가

    Returns:
        성공: {'ok': True, 'data': 추가한 바이트 수, 'path': 경로}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        p = Path(path)

        # 파일이 없으면 새로 생성
        if not p.exists():
            return write(path, content, encoding)

        # 기존 내용에 추가
        with open(p, 'a', encoding=encoding) as f:
            f.write(content)

        return ok(
            len(content),
            path=str(p.absolute()),
            appended=True
        )
    except Exception as e:
        return err(str(e), path=path)


def read_json(path: str) -> Dict[str, Any]:
    """JSON 파일 읽기

    Returns:
        성공: {'ok': True, 'data': 파싱된 객체}
        실패: {'ok': False, 'error': 에러메시지}
    """
    result = read(path)
    if not result['ok']:
        return result

    try:
        data = json.loads(result['data'])
        return ok(data, path=path)
    except json.JSONDecodeError as e:
        return err(f"Invalid JSON: {e}", path=path)


def write_json(path: str, data: Any, indent: int = 2) -> Dict[str, Any]:
    """객체를 JSON으로 저장

    Returns:
        성공: {'ok': True, 'data': 쓴 바이트 수}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return write(path, content)
    except Exception as e:
        return err(f"JSON encoding error: {e}", path=path)


def exists(path: str) -> Dict[str, Any]:
    """파일 존재 여부 확인

    Returns:
        Dict with keys:
        - ok: bool - 작업 성공 여부
        - data: bool - 파일 존재 여부
        - path: str - 확인한 경로
    """
    try:
        result = Path(path).exists()
        return ok(result, path=str(path))
    except Exception as e:
        return err(f"Failed to check existence: {str(e)}")


def info(path: str) -> Dict[str, Any]:
    """파일 정보 조회

    Returns:
        성공: {'ok': True, 'data': {'size': 크기, 'lines': 줄수, ...}}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        p = Path(path)
        if not p.exists():
            return err(f"File not found: {path}", path=path)

        stat = p.stat()

        # 텍스트 파일인 경우 줄 수 계산
        lines = None
        if p.suffix in ['.py', '.txt', '.md', '.json', '.js', '.ts']:
            try:
                content = p.read_text()
                lines = content.count('\n') + 1
            except:
                pass

        return ok({
            'size': stat.st_size,
            'lines': lines,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_file': p.is_file(),
            'is_dir': p.is_dir(),
            'suffix': p.suffix,
            'name': p.name
        }, path=str(p.absolute()))

    except Exception as e:
        return err(str(e), path=path)
