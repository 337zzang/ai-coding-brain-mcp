"""
AI Helpers File Module - 개선 버전
데이터 무결성과 성능을 개선한 파일 입출력 모듈
"""
from pathlib import Path
import json
import shutil
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Union, Optional, List
from collections import deque
from itertools import islice
from .util import ok, err


def resolve_project_path(path: Union[str, Path]) -> Path:
    """
    프로젝트 경로 해결 - 순환 참조 제거 버전

    환경 변수 AI_PROJECT_BASE를 사용하거나 현재 디렉토리 기준
    """
    if isinstance(path, str):
        path = Path(path)

    # 절대 경로는 그대로 반환
    if path.is_absolute():
        return path

    # 환경 변수에서 프로젝트 경로 확인
    project_base = os.environ.get('AI_PROJECT_BASE')

    if project_base:
        return Path(project_base) / path
    else:
        # 현재 작업 디렉토리 기준
        return Path.cwd() / path


def write(filepath: Union[str, Path], 
          content: str, 
          backup: bool = False, 
          encoding: str = 'utf-8') -> Dict[str, Any]:
    """
    원자적 쓰기를 구현한 안전한 파일 쓰기

    데이터 무결성을 보장하기 위해 임시 파일에 먼저 쓰고
    성공 시에만 원본을 교체합니다.
    """
    try:
        p = resolve_project_path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)

        backup_path = None

        # 백업 처리 (타임스탬프 포함)
        if backup and p.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = p.with_name(f"{p.stem}.{timestamp}.backup{p.suffix}")
            shutil.copy2(p, backup_path)

        # 원자적 쓰기 - 임시 파일 사용
        temp_fd, temp_path = tempfile.mkstemp(
            dir=p.parent,
            prefix=f'.tmp_{p.name}_',
            text=True
        )

        try:
            # 임시 파일에 쓰기
            with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # 디스크에 강제 동기화

            # 원자적 교체
            if os.name == 'nt':  # Windows
                if p.exists():
                    os.replace(temp_path, str(p))
                else:
                    os.rename(temp_path, str(p))
            else:  # Unix/Linux/Mac
                os.rename(temp_path, str(p))  # 원자적 작업

            return ok({
                'path': str(p),
                'size': len(content),
                'backup': str(backup_path) if backup_path else None
            })

        except Exception as e:
            # 임시 파일 정리
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise

    except Exception as e:
        return err(f"Write failed: {e}")


def read(filepath: Union[str, Path],
         encoding: str = 'utf-8',
         offset: int = 0,
         length: Optional[int] = 1000) -> Dict[str, Any]:
    """
    효율적인 부분 읽기 구현

    - offset >= 0: 시작 부분부터 읽기 (islice 사용)
    - offset < 0: 끝 부분부터 읽기 (deque 사용)
    """
    try:
        p = resolve_project_path(filepath)

        if not p.exists():
            return err(f"File not found: {filepath}")

        # 작은 파일은 전체 읽기 (10KB 미만)
        file_size = p.stat().st_size
        if file_size < 1024 * 10:
            content = p.read_text(encoding=encoding, errors='replace')
            lines = content.splitlines()

            if offset < 0:  # 끝에서부터
                selected = lines[offset:] if abs(offset) <= len(lines) else lines
            else:
                end = offset + length if length else None
                selected = lines[offset:end]

            return ok('\n'.join(selected))

        # 큰 파일은 효율적 처리
        with open(p, 'r', encoding=encoding, errors='replace') as f:
            if offset < 0:
                # Tail 읽기 - deque 사용 (메모리 효율적)
                lines = deque(maxlen=abs(offset))
                for line in f:
                    lines.append(line.rstrip('\n'))
                content = '\n'.join(lines)
            else:
                # 정방향 읽기 - islice 사용 (I/O 효율적)
                if length:
                    lines = list(islice(f, offset, offset + length))
                else:
                    lines = list(islice(f, offset, None))
                content = ''.join(lines).rstrip('\n')

        return ok(content)

    except Exception as e:
        return err(f"Read failed: {e}")


def append(filepath: Union[str, Path],
           content: str,
           encoding: str = 'utf-8') -> Dict[str, Any]:
    """파일 끝에 내용 추가 (원자적 쓰기 적용)"""
    try:
        p = resolve_project_path(filepath)

        # 기존 내용 읽기
        existing_content = ""
        if p.exists():
            existing_content = p.read_text(encoding=encoding, errors='replace')
            if existing_content and not existing_content.endswith('\n'):
                existing_content += '\n'

        # 원자적 쓰기로 추가
        new_content = existing_content + content
        return write(filepath, new_content, backup=False, encoding=encoding)

    except Exception as e:
        return err(f"Append failed: {e}")


def info(filepath: Union[str, Path]) -> Dict[str, Any]:
    """메모리 효율적인 파일 정보 조회"""
    try:
        p = resolve_project_path(filepath)

        if not p.exists():
            return err(f"File not found: {filepath}")

        stat = p.stat()
        is_file = p.is_file()

        result = {
            'exists': True,
            'is_file': is_file,
            'is_directory': p.is_dir(),
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'path': str(p.absolute())
        }

        # 텍스트 파일인 경우만 라인 수 계산 (100MB 미만)
        if is_file and stat.st_size < 100 * 1024 * 1024:
            try:
                line_count = 0

                # 메모리 효율적인 라인 카운트
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_count, _ in enumerate(f, 1):
                        pass

                result.update({
                    'lines': line_count,
                    'lineCount': line_count,
                    'lastLine': line_count - 1 if line_count > 0 else 0,
                    'appendPosition': line_count
                })
            except:
                # 바이너리 파일이거나 읽기 실패
                pass

        return ok(result)

    except Exception as e:
        return err(f"Info failed: {e}")


def exists(filepath: Union[str, Path]) -> Dict[str, Any]:
    """파일/디렉토리 존재 여부 확인 (일관성 개선)"""
    try:
        p = resolve_project_path(filepath)  # 일관성을 위해 추가
        return ok({
            'exists': p.exists(),
            'path': str(p)
        })
    except Exception as e:
        return err(f"Exists check failed: {e}")


def list_directory(path: Union[str, Path] = '.') -> Dict[str, Any]:
    """구조화된 디렉토리 목록 반환"""
    try:
        p = resolve_project_path(path)

        if not p.exists():
            return err(f"Directory not found: {path}")

        if not p.is_dir():
            return err(f"Not a directory: {path}")

        items = []
        for item in sorted(p.iterdir()):
            try:
                stat = item.stat()
                items.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'path': str(item)
                })
            except (PermissionError, OSError):
                # 접근 권한이 없는 항목은 건너뜀
                continue

        return ok({
            'path': str(p),
            'items': items,
            'count': len(items)
        })

    except Exception as e:
        return err(f"List directory failed: {e}")


def create_directory(path: Union[str, Path]) -> Dict[str, Any]:
    """디렉토리 생성 (중첩 디렉토리 지원)"""
    try:
        p = resolve_project_path(path)
        p.mkdir(parents=True, exist_ok=True)
        return ok({'path': str(p), 'created': True})
    except Exception as e:
        return err(f"Create directory failed: {e}")


def read_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """JSON 파일 읽기"""
    try:
        result = read(filepath, length=None)  # 전체 읽기
        if not result['ok']:
            return result

        data = json.loads(result['data'])
        return ok(data)
    except json.JSONDecodeError as e:
        return err(f"Invalid JSON: {e}")
    except Exception as e:
        return err(f"Read JSON failed: {e}")


def write_json(filepath: Union[str, Path],
               data: Any,
               indent: int = 2,
               backup: bool = True) -> Dict[str, Any]:
    """원자적 JSON 쓰기"""
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return write(filepath, content, backup=backup)
    except Exception as e:
        return err(f"Write JSON failed: {e}")


# 기존 함수들과의 호환성 유지
def get_file_info(filepath):
    """info() 함수의 별칭"""
    return info(filepath)


def scan_directory(path='.', max_depth=None):
    """재귀적 디렉토리 스캔 (깊이 제한 포함)"""
    try:
        p = resolve_project_path(path)

        if not p.exists():
            return err(f"Directory not found: {path}")

        def scan_recursive(dir_path, current_depth=0):
            items = []

            if max_depth is not None and current_depth >= max_depth:
                return items

            try:
                for item in sorted(dir_path.iterdir()):
                    try:
                        stat = item.stat()
                        item_info = {
                            'name': item.name,
                            'type': 'directory' if item.is_dir() else 'file',
                            'size': stat.st_size,
                            'path': str(item.relative_to(p))
                        }

                        if item.is_dir():
                            children = scan_recursive(item, current_depth + 1)
                            if children:
                                item_info['children'] = children

                        items.append(item_info)
                    except (PermissionError, OSError):
                        continue
            except PermissionError:
                pass

            return items

        structure = scan_recursive(p)
        return ok({
            'path': str(p),
            'structure': structure
        })

    except Exception as e:
        return err(f"Scan directory failed: {e}")
