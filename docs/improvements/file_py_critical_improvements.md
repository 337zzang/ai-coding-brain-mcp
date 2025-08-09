# file.py 개선안 - 치명적 문제 해결

## 1. 🔴 원자적 쓰기 구현 (데이터 무결성)

### 현재 문제점
```python
# 현재 write() - 위험한 코드
def write(filepath, content, backup=False, encoding='utf-8'):
    p = resolve_project_path(filepath)
    if backup and p.exists():
        shutil.copy2(p, p.with_suffix(p.suffix + '.backup'))
    p.write_text(content, encoding=encoding)  # ❌ 중단 시 데이터 손실!
```

### 개선된 코드
```python
import tempfile
import os
from datetime import datetime

def write(filepath, content, backup=False, encoding='utf-8'):
    """원자적 쓰기를 구현한 안전한 파일 쓰기"""
    try:
        p = resolve_project_path(filepath)

        # 1. 백업 처리 (타임스탬프 포함)
        if backup and p.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = p.with_suffix(f'{p.suffix}.{timestamp}.backup')
            shutil.copy2(p, backup_path)

        # 2. 원자적 쓰기 - 임시 파일 사용
        # 같은 디렉토리에 임시 파일 생성 (같은 파일시스템 보장)
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

            # 원자적 교체 (POSIX: rename, Windows: replace)
            if os.name == 'nt':  # Windows
                # Windows는 대상 파일이 있으면 replace 필요
                if p.exists():
                    os.replace(temp_path, str(p))
                else:
                    os.rename(temp_path, str(p))
            else:  # Unix/Linux/Mac
                os.rename(temp_path, str(p))  # 원자적 작업

            return ok({
                'path': str(p),
                'size': len(content),
                'backup': str(backup_path) if backup else None
            })

        except Exception as e:
            # 임시 파일 정리
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        return err(f"Write failed: {e}")
```

## 2. 🔴 메모리 효율적인 파일 처리

### info() 함수 개선
```python
def info(filepath):
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

        # 텍스트 파일인 경우만 라인 수 계산 (메모리 효율적)
        if is_file and stat.st_size < 100 * 1024 * 1024:  # 100MB 미만만
            try:
                line_count = 0
                last_line = 0

                # 메모리 효율적인 라인 카운트
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_count, _ in enumerate(f, 1):
                        pass
                    last_line = line_count - 1 if line_count > 0 else 0

                result.update({
                    'lines': line_count,
                    'lineCount': line_count,
                    'lastLine': last_line,
                    'appendPosition': line_count
                })
            except:
                # 바이너리 파일이거나 읽기 실패
                pass

        return ok(result)

    except Exception as e:
        return err(f"Info failed: {e}")
```

### read() 함수 개선
```python
from itertools import islice

def read(filepath, encoding='utf-8', offset=0, length=1000):
    """효율적인 부분 읽기 구현"""
    try:
        p = resolve_project_path(filepath)

        if not p.exists():
            return err(f"File not found: {filepath}")

        # 작은 파일은 전체 읽기
        if p.stat().st_size < 1024 * 10:  # 10KB 미만
            content = p.read_text(encoding=encoding)
            lines = content.splitlines()

            if offset < 0:  # 끝에서부터
                selected = lines[offset:] if abs(offset) <= len(lines) else lines
            else:
                end = offset + length if length else None
                selected = lines[offset:end]

            return ok('\n'.join(selected))

        # 큰 파일은 효율적 처리
        with open(p, 'r', encoding=encoding, errors='ignore') as f:
            if offset < 0:
                # Tail 읽기 - deque 사용 (메모리 효율적)
                from collections import deque
                lines = deque(maxlen=abs(offset))
                for line in f:
                    lines.append(line.rstrip('\n'))
                content = '\n'.join(lines)
            else:
                # 정방향 읽기 - islice 사용 (I/O 효율적)
                end = offset + length if length else None
                lines = list(islice(f, offset, end))
                content = ''.join(lines).rstrip('\n')

        return ok(content)

    except Exception as e:
        return err(f"Read failed: {e}")
```

## 3. 🔴 아키텍처 개선

### resolve_project_path() 순환 참조 해결
```python
def resolve_project_path(path: Union[str, Path]) -> Path:
    """
    프로젝트 경로 해결 - 순환 참조 제거

    상위 모듈 import 대신 환경 변수나 전역 설정 사용
    """
    if isinstance(path, str):
        path = Path(path)

    # 절대 경로는 그대로 반환
    if path.is_absolute():
        return path

    # 환경 변수에서 프로젝트 경로 확인
    import os
    project_base = os.environ.get('AI_PROJECT_BASE')

    if project_base:
        return Path(project_base) / path
    else:
        # 현재 작업 디렉토리 기준
        return Path.cwd() / path
```

## 4. 구조화된 디렉토리 목록

```python
def list_directory(path='.'):
    """구조화된 디렉토리 목록 반환"""
    try:
        p = resolve_project_path(path)

        if not p.exists():
            return err(f"Directory not found: {path}")

        if not p.is_dir():
            return err(f"Not a directory: {path}")

        items = []
        for item in sorted(p.iterdir()):
            stat = item.stat()
            items.append({
                'name': item.name,
                'type': 'directory' if item.is_dir() else 'file',
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'path': str(item)
            })

        return ok({
            'path': str(p),
            'items': items,
            'count': len(items)
        })

    except Exception as e:
        return err(f"List directory failed: {e}")
```

## 5. 추가 개선 사항

### 5.1 대용량 파일 스트리밍 지원
```python
def read_stream(filepath, chunk_size=8192):
    """대용량 파일을 위한 스트리밍 읽기"""
    try:
        p = resolve_project_path(filepath)

        with open(p, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    except Exception as e:
        yield err(f"Stream read failed: {e}")
```

### 5.2 안전한 JSON 읽기/쓰기
```python
def write_json(filepath, data, indent=2, backup=True):
    """원자적 JSON 쓰기"""
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return write(filepath, content, backup=backup)
    except Exception as e:
        return err(f"JSON write failed: {e}")
```

## 요약

1. **원자적 쓰기**: 임시 파일 + os.replace()로 데이터 무결성 보장
2. **메모리 효율**: 스트리밍과 제너레이터로 대용량 파일 처리
3. **성능 개선**: islice()로 효율적인 부분 읽기
4. **아키텍처**: 순환 참조 제거, 환경 변수 활용
5. **API 개선**: 구조화된 데이터 반환

이러한 개선으로 데이터 손실 방지, 메모리 효율성, 성능 향상을 달성할 수 있습니다.
