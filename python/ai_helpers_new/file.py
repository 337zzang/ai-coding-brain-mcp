"""
AI Helpers File Module
파일 읽기/쓰기를 위한 단순하고 실용적인 함수들
"""
from pathlib import Path
import json
import shutil
from .util import ok, err
from typing import Any, Dict


def read(path: str, encoding: str = 'utf-8', offset: int = 0, length: int = None) -> Dict[str, Any]:
    """파일을 읽어서 내용 반환 (부분 읽기 지원)

    Args:
        path: 파일 경로
        encoding: 파일 인코딩 (기본: utf-8)
        offset: 시작 라인 번호 (0-based, 음수는 끝에서부터)
        length: 읽을 라인 수 (None이면 끝까지)

    Returns:
        성공: {'ok': True, 'data': 내용, 'path': 경로, 'lines': 줄수, 'size': 크기}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        p = Path(path)
        if not p.exists():
            return err(f"File not found: {path}", path=path)

        # 전체 읽기 (기존 동작)
        if offset == 0 and length is None:
            content = p.read_text(encoding=encoding)
            stat = p.stat()
            return ok(
                content,
                path=str(p.absolute()),
                lines=content.count('\n') + 1,
                size=stat.st_size,
                encoding=encoding
            )

        # 부분 읽기
        lines = []
        total_lines = 0

        with open(p, 'r', encoding=encoding) as f:
            # offset < 0: 마지막 N줄 읽기
            if offset < 0:
                from collections import deque
                lines = deque(maxlen=abs(offset))
                for line in f:
                    lines.append(line.rstrip('\n'))
                    total_lines += 1
                lines = list(lines)
                if length is not None:
                    lines = lines[:length]
            else:
                # offset >= 0: 특정 위치부터 읽기
                # offset까지 스킵
                for i in range(offset):
                    if f.readline() == '':
                        break
                    total_lines += 1

                # length만큼 읽기
                if length is None:
                    for line in f:
                        lines.append(line.rstrip('\n'))
                        total_lines += 1
                else:
                    for i in range(length):
                        line = f.readline()
                        if line == '':
                            break
                        lines.append(line.rstrip('\n'))
                        total_lines += 1

        content = '\n'.join(lines)
        stat = p.stat()

        return ok(
            content,
            path=str(p.absolute()),
            lines=len(lines),
            total_lines=total_lines + offset if offset >= 0 else total_lines,
            size=stat.st_size,
            encoding=encoding,
            offset=offset,
            length=length
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

def list_directory(path: str = ".") -> Dict[str, Any]:
    """디렉토리 내용 조회

    Args:
        path: 조회할 디렉토리 경로

    Returns:
        {'ok': True, 'data': ['file1', 'dir1/', ...]}
        {'ok': False, 'error': '에러 메시지'}
    """
    import os
    from pathlib import Path

    try:
        p = Path(path).resolve()
        if not p.exists():
            return err(f"경로가 존재하지 않습니다: {path}")

        if not p.is_dir():
            return err(f"디렉토리가 아닙니다: {path}")

        items = []
        for item in sorted(os.listdir(p)):
            item_path = p / item
            if item_path.is_dir():
                items.append(f"[DIR] {item}")
            else:
                items.append(f"[FILE] {item}")

        return ok(items, count=len(items), path=str(p))

    except PermissionError:
        return err(f"권한이 없습니다: {path}")
    except Exception as e:
        return err(f"디렉토리 조회 실패: {str(e)}")


def get_file_info(path: str) -> Dict[str, Any]:
    """info 함수의 별칭 (Desktop Commander 호환성)

    Returns:
        성공: {'ok': True, 'data': {'size': 크기, 'lines': 줄수, ...}}
        실패: {'ok': False, 'error': 에러메시지}
    """
    return info(path)


def create_directory(path: str, parents: bool = True, exist_ok: bool = True) -> Dict[str, Any]:
    """디렉토리 생성

    Args:
        path: 생성할 디렉토리 경로
        parents: True면 부모 디렉토리도 자동 생성
        exist_ok: True면 이미 존재해도 에러 없음

    Returns:
        성공: {'ok': True, 'data': {'created': bool, 'path': str}}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        p = Path(path)
        already_exists = p.exists()

        if already_exists and p.is_file():
            return err(f"Path exists as file: {path}", path=str(p.absolute()))

        p.mkdir(parents=parents, exist_ok=exist_ok)

        return ok({
            'created': not already_exists,
            'already_existed': already_exists,
            'is_absolute': p.is_absolute(),
            'parent': str(p.parent)
        }, path=str(p.absolute()))

    except Exception as e:
        return err(f"Failed to create directory: {str(e)}", path=path)
