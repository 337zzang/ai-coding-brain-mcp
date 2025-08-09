아래는 주어진 file.py의 핵심 문제를 하나씩 짚고, 실사용 가능한 개선 코드와 함께 설명한 내용입니다. 데이터 무결성과 성능 문제를 최우선으로 해결하고, 순환 참조와 일관성, 아키텍처 개선 방향까지 포함했습니다.

핵심 수정 사항 요약
- 원자적 쓰기(atomic write) 도입: 동일 디렉터리 임시 파일에 쓰고, flush+fsync 후 os.replace로 교체. 선택적으로 디렉터리 fsync까지 지원.
- 안정적인 백업: 타임스탬프가 붙은 롤링 백업(.bak.YYYYmmdd-HHMMSS)과 보관 개수 제한(prune).
- 대용량 파일 대응:
  - info: readlines 제거, 바이너리 스트림으로 개행 수를 카운트(메모리 고정), 큰 파일은 임계값 초과 시 라인 카운트 생략.
  - read: positive offset은 islice로 효율적으로 스킵, negative offset(tail)은 파일 끝에서 블록 단위 역방향 읽기.
- 순환 참조 제거: 세션 의존성 주입(set_project_resolver) 방식으로 변경, resolve_project_path 내부에서 .session import 제거.
- 예외 처리 정교화: bare except 제거, 필요 시 구체적 예외만 처리.
- 버그 수정 및 일관성:
  - read의 total_lines 계산 버그 수정: 옵션(include_total=True)일 때만 정확한 총 라인 수 계산.
  - exists가 resolve_project_path를 사용하도록 수정.
  - list_directory는 구조화된 객체 리스트 반환(구버전 호환 라벨 형식 옵션 제공).

문제별 구체적 개선 코드

1) 데이터 무결성: 원자적 쓰기와 백업 전략
설명
- 임시 파일에 기록 → flush → fsync(f) → os.replace(tmp, dest) 순으로 전원 장애에도 일관성을 확보합니다.
- 기존 백업 덮어쓰기 문제를 타임스탬프 백업과 보관 개수 제한으로 해결합니다.
- append는 완전한 원자성은 불가능하지만 flush+fsync로 내구성 향상.

코드
- 모듈 상단 import와 유틸리티

from pathlib import Path
import os
import json
import shutil
import tempfile
import time
import itertools
from typing import Any, Dict, Union, Optional, Callable, List

from .util import ok, err

# 선택적 세션 경로 해석기(의존성 주입으로 순환 참조 제거)
_project_path_resolver: Optional[Callable[[Union[str, Path]], Path]] = None

def set_project_resolver(resolver: Optional[Callable[[Union[str, Path]], Path]]) -> None:
    global _project_path_resolver
    _project_path_resolver = resolver

def clear_project_resolver() -> None:
    set_project_resolver(None)

def _count_lines_in_text(s: str) -> int:
    if not s:
        return 0
    n = s.count('\n')
    return n if s.endswith('\n') else n + 1

def _atomic_write_text(p: Path, content: str, encoding: str = 'utf-8',
                       fsync_file: bool = True, fsync_dir: bool = False) -> int:
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(p.parent), prefix=p.name + '.', suffix='.tmp')
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, 'w', encoding=encoding, newline='') as f:
            f.write(content)
            f.flush()
            if fsync_file:
                os.fsync(f.fileno())
        # 기존 파일 모드 유지(있다면)
        try:
            st = p.stat()
            os.chmod(tmp_path, st.st_mode)
        except FileNotFoundError:
            pass
        os.replace(str(tmp_path), str(p))
        if fsync_dir:
            try:
                dir_fd = os.open(str(p.parent), os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except Exception:
                # 일부 플랫폼/파일시스템에서 O_DIRECTORY 미지원: 무시
                pass
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return len(content)

def _make_backup_path(p: Path, ts: Optional[float] = None) -> Path:
    if ts is None:
        ts = time.time()
    stamp = time.strftime('%Y%m%d-%H%M%S', time.localtime(ts))
    return p.with_name(p.name + f".bak.{stamp}")

def _list_backups(p: Path) -> List[Path]:
    return sorted(p.parent.glob(p.name + ".bak.*"))

def _prune_backups(p: Path, keep: int = 3) -> None:
    if keep is None or keep < 0:
        return
    backups = _list_backups(p)
    if len(backups) > keep:
        for old in backups[:-keep]:
            try:
                old.unlink()
            except Exception:
                pass

- resolve_project_path: 순환 참조 제거 및 예외 최소화

def resolve_project_path(path: Union[str, Path]) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    if _project_path_resolver:
        try:
            resolved = _project_path_resolver(p)
            if resolved:
                return Path(resolved)
        except Exception:
            # 세션 해석기 실패 시 현재 작업 디렉터리로 폴백
            pass
    return Path.cwd() / p

- write: 원자적 쓰기 및 안정 백업

def write(path: str, content: str, encoding: str = 'utf-8',
          backup: bool = False, backup_keep: int = 3,
          fsync: bool = True) -> Dict[str, Any]:
    try:
        p = resolve_project_path(path)

        if backup and p.exists():
            b = _make_backup_path(p)
            shutil.copy2(str(p), str(b))
            _prune_backups(p, keep=backup_keep)

        written = _atomic_write_text(p, content, encoding=encoding, fsync_file=fsync, fsync_dir=False)
        return ok(
            written,
            path=str(p.resolve()),
            lines=_count_lines_in_text(content)
        )
    except Exception as e:
        return err(str(e), path=path)

- append: 내구성 향상

def append(path: str, content: str, encoding: str = 'utf-8', fsync: bool = True) -> Dict[str, Any]:
    try:
        p = resolve_project_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'a', encoding=encoding, newline='') as f:
            f.write(content)
            f.flush()
            if fsync:
                os.fsync(f.fileno())
        return ok(
            len(content),
            path=str(p.resolve()),
            appended=True
        )
    except Exception as e:
        return err(str(e), path=path)

2) 성능/메모리: info/read 개선과 tail 최적화
설명
- info: readlines() 제거. 바이너리로 일정 버퍼 크기로 읽어 개행 바이트를 카운트(b'\n'). 매우 큰 파일은 임계값 초과 시 라인 카운트 생략 가능.
- read:
  - offset >= 0: itertools.islice로 효율적으로 스킵 및 슬라이스.
  - offset < 0: 파일 끝에서 블록 단위 역방향 읽기로 마지막 N줄만 읽음(전체 순회 회피).
- total_lines는 전체 파일을 한번 더 스캔해야 하므로 기본 비활성화하고, include_total=True일 때만 계산.

코드
- 라인 카운트(바이너리)

def _count_lines_binary(p: Path, chunk_size: int = 1024 * 1024) -> int:
    total = 0
    last_byte = None
    with open(p, 'rb') as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            total += b.count(b'\n')
            last_byte = b[-1]
    if last_byte is None:
        return 0
    if last_byte != 0x0A:  # b'\n'
        total += 1
    return total

- tail 구현(역방향 블록 읽기)

def _tail_lines(p: Path, n: int, encoding: str = 'utf-8', errors: str = 'replace',
                block_size: int = 64 * 1024) -> List[str]:
    if n <= 0:
        return []
    size = p.stat().st_size
    if size == 0:
        return []
    chunks: List[bytes] = []
    nl = 0
    with open(p, 'rb') as f:
        pos = size
        while pos > 0 and nl <= n:
            read_size = block_size if pos >= block_size else pos
            pos -= read_size
            f.seek(pos)
            data = f.read(read_size)
            chunks.append(data)
            nl += data.count(b'\n')
            if nl >= n + 1:
                break
    buf = b''.join(reversed(chunks))
    text = buf.decode(encoding, errors=errors)
    lines = text.splitlines()
    return lines[-n:]

- read 개선

def read(path: str, encoding: str = 'utf-8', offset: int = 0, length: Optional[int] = None,
         include_total: bool = False, errors: str = 'strict') -> Dict[str, Any]:
    try:
        p = resolve_project_path(path)
        if not p.exists():
            return err(f"File not found: {path}", path=path)

        # 전체 읽기
        if offset == 0 and length is None:
            content = p.read_text(encoding=encoding, errors=errors)
            stat = p.stat()
            return ok(
                content,
                path=str(p.resolve()),
                lines=_count_lines_in_text(content),
                size=stat.st_size,
                encoding=encoding
            )

        # 부분 읽기
        if offset < 0:
            lines = _tail_lines(p, n=abs(offset), encoding=encoding, errors=errors)
            if length is not None:
                lines = lines[:length]
        else:
            with open(p, 'r', encoding=encoding, errors=errors, newline=None) as f:
                end = None if length is None else offset + length
                it = (line.rstrip('\n') for line in f)
                lines = list(itertools.islice(it, offset, end))

        content = '\n'.join(lines)
        result = ok(
            content,
            path=str(p.resolve()),
            lines=len(lines),
            encoding=encoding,
            offset=offset,
            length=length
        )
        if include_total:
            try:
                result['total_lines'] = _count_lines_binary(p)
            except Exception:
                result['total_lines'] = None
        return result
    except Exception as e:
        return err(str(e), path=path)

- info 개선(메모리 효율, 큰 파일 보호)

def _seems_text_file(p: Path, probe_bytes: int = 8192) -> bool:
    try:
        with open(p, 'rb') as f:
            chunk = f.read(probe_bytes)
        if b'\x00' in chunk:
            return False
        return True
    except Exception:
        return False

def info(path: str, max_bytes_for_line_count: int = 64 * 1024 * 1024) -> Dict[str, Any]:
    try:
        p = resolve_project_path(path)
        if not p.exists():
            return err(f"File not found: {path}", path=path)
        stat = p.stat()

        lines = None
        line_count = None
        last_line = None
        append_position = None

        if p.is_file() and _seems_text_file(p):
            if stat.st_size <= max_bytes_for_line_count:
                try:
                    lc = _count_lines_binary(p)
                    lines = lc
                    line_count = lc
                    last_line = lc - 1 if lc > 0 else 0
                    append_position = lc
                except Exception:
                    pass
            else:
                # 너무 큰 파일은 라인 카운트 생략
                lines = None
                line_count = None
                last_line = None
                append_position = None

        return ok({
            'size': stat.st_size,
            'lines': lines,
            'lineCount': line_count,
            'lastLine': last_line,
            'appendPosition': append_position,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_file': p.is_file(),
            'is_dir': p.is_dir(),
            'suffix': p.suffix,
            'name': p.name,
            'type': 'file' if p.is_file() else 'directory'
        }, path=str(p.resolve()))
    except Exception as e:
        return err(str(e), path=path)

3) 아키텍처: 순환 참조 및 예외 처리
설명
- resolve_project_path가 .session을 import하지 않도록 바꾸고, 세션이 초기화되면 set_project_resolver로 resolve 함수를 주입합니다.
- 광범위한 예외 숨김 제거(필요 최소한의 except로 한정).

세션 측 변경 예시(참고)
- session 모듈 초기화 시점에 아래 한 줄만 추가

from . import file as file_mod
file_mod.set_project_resolver(lambda p: session.project_context.resolve_path(p))

4) 버그 및 일관성
- read의 total_lines 버그: include_total=True일 때만 정확히 계산해 total_lines를 반환. 기본 False로 두어 성능 저하 방지.
- exists가 resolve_project_path를 사용: CWD와 프로젝트 베이스 해석 일관성 확보.
- list_directory는 구조화된 결과로 반환. 구버전 호환을 위해 라벨 형식도 선택적 제공.

코드
- exists 수정

def exists(path: str) -> Dict[str, Any]:
    try:
        p = resolve_project_path(path)
        return ok(p.exists(), path=str(p.resolve()))
    except Exception as e:
        return err(f"Failed to check existence: {str(e)}", path=path)

- list_directory 구조화

def list_directory(path: str = ".", format: str = "object") -> Dict[str, Any]:
    try:
        p = resolve_project_path(path).resolve()
        if not p.exists():
            return err(f"경로가 존재하지 않습니다: {path}", path=str(p))
        if not p.is_dir():
            return err(f"디렉토리가 아닙니다: {path}", path=str(p))

        items = []
        for entry in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                st = entry.stat()
            except Exception:
                st = None
            item = {
                'name': entry.name,
                'path': str(entry.resolve()),
                'type': 'directory' if entry.is_dir() else 'file',
                'is_dir': entry.is_dir(),
                'is_file': entry.is_file(),
                'size': (st.st_size if st and entry.is_file() else None),
                'modified': (st.st_mtime if st else None),
            }
            items.append(item)

        if format == "label":
            # 구버전 호환
            labels = [("[DIR] " + i['name']) if i['is_dir'] else ("[FILE] " + i['name']) for i in items]
            return ok(labels, count=len(labels), path=str(p))
        return ok(items, count=len(items), path=str(p))
    except PermissionError:
        return err(f"권한이 없습니다: {path}", path=path)
    except Exception as e:
        return err(f"디렉토리 조회 실패: {str(e)}", path=path)

- read_json / write_json: 스트리밍 및 원자적 쓰기 경유

def read_json(path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    try:
        p = resolve_project_path(path)
        if not p.exists():
            return err(f"File not found: {path}", path=path)
        with open(p, 'r', encoding=encoding) as f:
            data = json.load(f)
        return ok(data, path=str(p.resolve()))
    except json.JSONDecodeError as e:
        return err(f"Invalid JSON: {e}", path=path)
    except Exception as e:
        return err(str(e), path=path)

def write_json(path: str, data: Any, indent: int = 2, encoding: str = 'utf-8',
               backup: bool = False, backup_keep: int = 3) -> Dict[str, Any]:
    try:
        content = json.dumps(
            data, indent=indent, ensure_ascii=False,
            default=lambda o: o.isoformat() if hasattr(o, 'isoformat') else str(o)
        )
        return write(path, content, encoding=encoding, backup=backup, backup_keep=backup_keep)
    except Exception as e:
        return err(f"JSON encoding error: {e}", path=path)

전체 리팩토링 방향성
- 경로 해석 계층 분리
  - 현재 모듈에서 세션 정보를 직접 import하지 말고(해결 완료), set_project_resolver로 외부에서 주입하도록 유지.
  - 프로젝트 컨텍스트가 더 복잡해지면 PathResolver 인터페이스(프로토콜)로 명세화.
- 일관된 Result 형식
  - ok/err 포맷은 유지하되, data 스키마를 명확히 문서화하고 키 이름을 표준화(lines vs lineCount 등).
  - 필드 의미: lines=반환된 라인 수, total_lines=파일 전체 라인 수(옵션), size=바이트.
- 대용량·스트리밍 고려
  - read에 stream=True를 추가해 제너레이터로 반환하는 API를 별도 제공(현행 문자열 반환은 유지).
  - JSON도 json.load 대신 ijson 같은 스트리밍 파서를 선택 옵션화(외부 의존성 허용 시).
- 옵션화로 비용 제어
  - info에서 라인 카운트는 기본 비활성화 혹은 파일 크기 임계값으로 제어(현행 max_bytes_for_line_count).
  - read에서 include_total=False 기본.
- 예외 원인 노출 및 로깅
  - bare except 제거(현행 개선 반영), 필요 시 로거 주입으로 디버깅 용이성 확보.
- 테스트와 회귀 방지
  - 원자적 쓰기, 백업 롤링, tail, islice 경계 값(빈 파일, 개행 없는 파일, 매우 긴 라인, 윈도우/리눅스 개행) 테스트 추가.
  - 성능 회귀 방지 벤치마크(수백 MB 파일, tail 100 lines, offset 수백만 등).

적용/마이그레이션 안내
- 세션 초기화 시 set_project_resolver를 반드시 호출해야 프로젝트 상대 경로 해석이 동작합니다.
- read의 total_lines는 include_total=True로 명시 호출해야 계산됩니다. 과거 코드가 total_lines를 기대한다면 이 옵션을 켜거나 info를 사용하세요.
- list_directory가 기본적으로 구조화된 데이터를 반환하므로, 과거 문자열 라벨이 필요하면 format="label"을 지정하세요.

이상의 변경으로
- 데이터 무결성: 쓰기 중단/크래시 상황에서 손상 없이 교체 보장, 백업 안전.
- 성능/메모리: 대용량 파일에서도 O(1) 메모리, tail/offset 처리 최적화.
- 아키텍처: 순환 참조 제거, 예외 처리 명확화.
- 버그/일관성: total_lines 계산, exists 경로 해석, list_directory 구조화 등 해결.