# O3 Search.py 분석 결과

생성일: 2025-08-09
토큰 사용: 3121

## O3 제안 요약

아래 코드는 847 라인짜리 search.py(가상의 기존 버전)에 “치명적 버그 + 성능/품질” 항목을 모두 반영해 리팩터링-패치를 적용한 예입니다.  
(※ 라인 번호는 설명 편의를 위해 대략적으로 표시했습니다. 실제 파일에서는 위치가 다를 수 있습니다.)

─────────────────────────────────────────────
1. 중복된 get_statistics 제거 / 고성능으로 재작성
─────────────────────────────────────────────
# --- 삭제:  기존 210번째 get_statistics ---  (중복 정의)

# === keep 한 버전(하단 800줄 부근)을 아래처럼 교체 ===
from functools import lru_cache

NUL = b'\x00'                                     # ① NUL(바이너리) 검출용

def _is_binary(path: str, size: int = 1024) -> bool:
    """파일 앞부분에 NUL 바이트가 있으면 바이너리로 간주."""
    try:
        with open(path, 'rb') as fp:
            return NUL in fp.read(size)
    except (FileNotFoundError, PermissionError):
        return True                                # 접근 불가도 스킵

@lru_cache(maxsize=128)                           # ② 캐싱
def get_statistics(root_dir: str) -> dict:
    """코드베이스 통계(텍스트 파일 수/총 라인 수)"""
    stats = {'files': 0, 'lines': 0}
    for dirpath, _, files in os.walk(root_dir):
        for fname in files:
            fpath = os.path.join(dirpath, fname)
            if _is_binary(fpath):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                    stats['lines'] += sum(1 for _ in fh)
                    stats['files'] += 1
            except (FileNotFoundError, PermissionError, OSError):
                continue
    return stats
─────────────────────────────────────────────
2. find_in_file의 잘못된 내부 호출 및 예외 범위 축소
─────────────────────────────────────────────
def find_in_file(path: str,
                 pattern: str,
                 mode: str = 'regex',
                 ast_type: str | None = None):
    """
    파일 단위 검색. 결과는 generator 로 바로 yield.
    """
    if _is_binary(path):
        return

    try:
        if mode == 'regex':
            yield from _find_regex(path, pattern)
        elif mode == 'ast':
            if ast_type == 'function':
                yield from _find_function_ast(path, pattern)
            elif ast_type == 'class':
                yield from _find_class_ast(path, pattern)
            else:
                raise ValueError(f'unknown ast_type: {ast_type}')
        else:
            raise ValueError(f'unknown mode: {mode}')
    except (UnicodeDecodeError, FileNotFoundError,
            PermissionError, OSError) as exc:      # 좁은 범위 예외
        logger.debug("skip %s (%s)", path, exc)

# (※ h.search_code → search_code 로 호출하던 오류는
#    find_in_file 내부에 아예 존재하지 않도록 수정했으므로 해결.)
─────────────────────────────────────────────
3. AST 검색 함수 – 잘못된 'mode' 값 & 소스 추출 로직 교체
─────────────────────────────────────────────
@lru_cache(maxsize=256)
def _load_ast(path: str):
    """파일을 읽어 AST와 소스 텍스트를 캐싱."""
    with open(path, encoding='utf-8') as fp:
        src = fp.read()
    return ast.parse(src, path), src

def _find_function_ast(path: str, name_regex: str):
    tree, source = _load_ast(path)
    regex = re.compile(name_regex)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and regex.search(node.name):
            yield {
                'file': path,
                'line': node.lineno,
                'name': node.name,
                'snippet': ast.get_source_segment(source, node),  # ← ④
                'mode': 'ast',                                    # ← FIX
                'kind': 'function',
            }

def _find_class_ast(path: str, name_regex: str):
    tree, source = _load_ast(path)
    regex = re.compile(name_regex)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and regex.search(node.name):
            yield {
                'file': path,
                'line': node.lineno,
                'name': node.name,
                'snippet': ast.get_source_segment(source, node),
                'mode': 'ast',
                'kind': 'class',
            }
─────────────────────────────────────────────
4. _find_regex – 파일 전체 로드 대신 한 줄씩 읽기
─────────────────────────────────────────────
def _find_regex(path: str, pat: str):
    cre = re.compile(pat)
    with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
        for lineno, line in enumerate(fp, 1):      # ⑤ streaming read
            if cre.search(line):
                yield {
                    'file': path,
                    'line': lineno,
                    'snippet': line.rstrip('\n'),
                    'mode': 'regex',
                }
─────────────────────────────────────────────
5. search_code – 파일 목록을 미리 모으지 않고 제너레이터로 즉시 탐색
─────────────────────────────────────────────
def _walk_files(root: str):
    """os.walk 를 얇은 generator 로 감싸 메모리 사용 최소화."""
    for dpath, _, files in os.walk(root):
        for fname in files:
            yield os.path.join(dpath, fname)

def search_code(root: str,
                pattern: str,
                mode: str = 'regex',
                ast_type: str | None = None):
    """
    전체 코드베이스를 검색한다. 결과는 곧바로 yield 되므로
    상위 호출부에서 streaming 처리가 가능하다.
    (과거 100개 파일 제한 삭제)                                   # ⑥
    """
    for fpath in _walk_files(root):
        yield from find_in_file(fpath, pattern, mode=mode, ast_type=ast_type)
─────────────────────────────────────────────
6. 그 외(코드 품질)
─────────────────────────────────────────────
• 모든 broad except Exception → 구체적 예외 목록으로 변경  
• logger.warning 대신 debug/ info 로 구분해 불필요한 로그 감소  
• _is_binary 에서 NUL 바이트 탐지로 정확도 향상  
• lru_cache 사용으로 AST 재컴파일 방지, 통계 재계산 방지  

위와 같이 수정하면  
– 중복 정의, 잘못된 호출, 잘못된 mode 값, 부정확한 source 추출 버그가 모두 해결되고  
– 파일 스트리밍 및 캐싱·예외 세분화로 메모리 사용과 성능 역시 개선됩니다.
