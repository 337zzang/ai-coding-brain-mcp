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

    # 절대 경로는 그대로 반환 [배치테스트]
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


def list_directory(path: Union[str, Path] = '.', debug: bool = False) -> Dict[str, Any]:
    """구조화된 디렉토리 목록 반환

    Args:
        path: 디렉토리 경로 (기본값: 현재 디렉토리)

    Returns:
        {
            'ok': True,
            'data': {
                'path': str,           # 디렉토리 절대 경로
                'items': List[dict],   # 파일/폴더 목록
                'entries': List[dict], # items와 동일 (별칭)
                'count': int           # 총 항목 수
            }
        }

    Note:
        - 'items'와 'entries'는 동일한 데이터를 가리킴
        - 각 항목은 {name, type, size, modified, path} 포함
    """
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

        result = ok({
            'path': str(p),
            'items': items,
            'entries': items,  # 별칭: items와 동일, 하위 호환성
            'count': len(items)
        })

        # Debug 모드일 때 구조 정보 출력
        if debug:
            print(f"✅ list_directory('{path}') 성공")
            print(f"   경로: {result['data']['path']}")
            print(f"   항목 수: {result['data']['count']}")
            print(f"   사용 가능한 키: {list(result['data'].keys())}")
            print(f"   💡 TIP: 'items' 또는 'entries' 둘 다 사용 가능")

            if items:
                print(f"\n   첫 번째 항목 구조:")
                first = items[0]
                for key, value in first.items():
                    print(f"     - {key}: {type(value).__name__}")

        return result

    except Exception as e:
        return err(f"List directory failed: {e}")



def list_files(path: Union[str, Path] = '.') -> Dict[str, Any]:
    """디렉토리 내 파일 이름 목록만 반환 (단순화 버전)

    Args:
        path: 디렉토리 경로 (기본값: 현재 디렉토리)

    Returns:
        HelperResult with list of file names

    Example:
        >>> files = h.file.list_files(".")['data']
        >>> print(files)
        ['file1.py', 'file2.txt', ...]
    """
    result = list_directory(path)
    if not result['ok']:
        return result

    # list_directory의 반환 구조에서 파일 이름만 추출
    files = [
        item['name'] for item in result['data'].get('items', [])
        if item['type'] == 'file'
    ]
    return ok(files)


def list_dirs(path: Union[str, Path] = '.') -> Dict[str, Any]:
    """디렉토리 내 하위 디렉토리 이름 목록만 반환 (단순화 버전)

    Args:
        path: 디렉토리 경로 (기본값: 현재 디렉토리)

    Returns:
        HelperResult with list of directory names

    Example:
        >>> dirs = h.file.list_dirs(".")['data']
        >>> print(dirs)
        ['dir1', 'dir2', ...]
    """
    result = list_directory(path)
    if not result['ok']:
        return result

    # list_directory의 반환 구조에서 디렉토리 이름만 추출
    dirs = [
        item['name'] for item in result['data'].get('items', [])
        if item['type'] == 'directory'
    ]
    return ok(dirs)


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


def cleanup_backups(pattern: str = "*.backup.*",
                    directory: str = ".",
                    dry_run: bool = False) -> Dict[str, Any]:
    """
    백업 파일들을 정리하는 함수
    
    Args:
        pattern: 삭제할 파일 패턴 (기본값: *.backup.*)
        directory: 검색할 디렉토리 (기본값: 현재 디렉토리)
        dry_run: True일 경우 실제 삭제하지 않고 목록만 반환
        
    Returns:
        dict: {
            'ok': bool,
            'removed': 삭제된 파일 목록,
            'count': 삭제된 파일 수,
            'total_size': 삭제된 총 크기 (bytes),
            'dry_run': dry_run 여부
        }
    """
    import glob
    import os
    
    try:
        # 프로젝트 경로 해석
        base_path = resolve_project_path(directory)
        search_pattern = str(base_path / pattern)
        
        # 재귀적으로 백업 파일 찾기
        backup_files = []
        if '**' in pattern:
            # 재귀 패턴
            backup_files = glob.glob(search_pattern, recursive=True)
        else:
            # 단일 디렉토리
            backup_files = glob.glob(search_pattern)
            # 하위 디렉토리도 검색
            recursive_pattern = str(base_path / "**" / pattern)
            backup_files.extend(glob.glob(recursive_pattern, recursive=True))
        
        # 중복 제거
        backup_files = list(set(backup_files))
        
        # 파일 정보 수집
        removed_files = []
        total_size = 0
        errors = []
        
        for file_path in backup_files:
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                if not dry_run:
                    os.remove(file_path)
                    removed_files.append(file_path)
                else:
                    # dry_run 모드에서는 삭제하지 않고 목록만
                    removed_files.append(file_path)
                    
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
        
        result = {
            'ok': True,
            'removed': removed_files,
            'count': len(removed_files),
            'total_size': total_size,
            'dry_run': dry_run,
            'pattern': pattern,
            'directory': str(base_path)
        }
        
        if errors:
            result['errors'] = errors
            
        if dry_run:
            result['message'] = f"DRY RUN: {len(removed_files)} 파일 발견 (실제 삭제되지 않음)"
        else:
            result['message'] = f"{len(removed_files)} 파일 삭제됨"
            
        return result
        
    except Exception as e:
        return err(f"Cleanup backups failed: {e}")


def remove_backups(pattern: str = "*.backup.py",
                   directory: str = "python/ai_helpers_new") -> Dict[str, Any]:
    """
    AI Helpers 백업 파일 삭제 (간편 함수)
    
    Args:
        pattern: 삭제할 파일 패턴 (기본값: *.backup.py)
        directory: 대상 디렉토리 (기본값: python/ai_helpers_new)
        
    Returns:
        dict: cleanup_backups 결과
    """
    return cleanup_backups(pattern=pattern, directory=directory, dry_run=False)


# 기존 함수들과의 호환성 유지
def get_file_info(filepath):
    """info() 함수의 별칭"""
    return info(filepath)


def scan_directory(path='.', max_depth=None, format='tree'):
    """재귀적 디렉토리 스캔 (깊이 제한 포함)

    Args:
        path: 스캔할 경로
        max_depth: 최대 깊이 (None = 무제한)
        format: 반환 형식 ('tree'|'flat'|'list')
            - tree: {'path': str, 'structure': list[dict]} (기존)
            - flat: {path: {'type': str, 'size': int}, ...} (새로운)
            - list: [path1, path2, ...] (간단)

    Returns:
        HelperResult with scan data
    """
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

                        if item.is_dir() and not item.name.startswith('.'):
                            children = scan_recursive(item, current_depth + 1)
                            if children:
                                item_info['children'] = children

                        items.append(item_info)
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                pass

            return items

        structure = scan_recursive(p)

        # 형식별 반환
        if format == 'flat':
            # 평면 dict 형식으로 변환
            flat_result = {}

            def flatten(items, prefix=''):
                for item in items:
                    full_path = item['path'] if prefix == '' else f"{prefix}/{item['name']}"
                    flat_result[full_path] = {
                        'type': item['type'],
                        'size': item.get('size', 0)
                    }
                    if 'children' in item:
                        flatten(item['children'], full_path)

            flatten(structure)
            return ok(flat_result)

        elif format == 'list':
            # 단순 경로 리스트
            path_list = []

            def collect_paths(items):
                for item in items:
                    path_list.append(item['path'])
                    if 'children' in item:
                        collect_paths(item['children'])

            collect_paths(structure)
            return ok(path_list)

        else:  # format == 'tree' (기본)
            return ok({'path': str(p), 'structure': structure})

    except Exception as e:
        return err(f"Scan directory error: {str(e)}")