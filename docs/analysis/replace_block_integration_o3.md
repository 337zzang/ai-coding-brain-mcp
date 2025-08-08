아래 분석과 제안은 “replace_block_final.py”의 강점을 “code.py”에 안전하게 흡수해 단일 코드 수정 모듈로 만드는 데 초점을 맞춥니다. 핵심은 기능 상위호환, 유지보수성, 테스트 용이성, 그리고 API 하위호환을 모두 만족하는 것입니다.

1) 장단점 비교

- code.py의 replace
  - 장점
    - 단순하고 읽기 쉬우며 wrap_output으로 표준 응답 유지
    - 정확매치→퍼지매치 순으로 시도해 예측 가능
    - 기존 사용자/호출부와 광범위한 호환성
    - 이미 안정적으로 동작 중인 들여쓰기 보정(adjust_indentation) 로직
    - 기본 preview 제공(일부 요약)
  - 단점
    - 퍼지매치가 문자 단위 중심(추정)으로, 들여쓰기 차이에 덜 강인
    - AST 검증/백업/상세 verbose 로그 등 안전장치 부족
    - 특수 문자열(f-string, raw, 백슬래시 많은 코드)에 대한 별도 취급 미흡
    - 오류 메시지 힌트는 있으나 매칭 근거, 유사도 등의 디버그 정보 제한

- replace_block_final.py (ReplaceBlock)
  - 장점
    - 라인 단위 퍼지매치 + 들여쓰기 무시 → 코드 블록 교체에 강인
    - 패턴 타입 자동 감지(멀티라인, f-string 등)
    - 미리보기(프리뷰), 상세 verbose, 유사도, 매칭 범위 등 풍부한 메타 정보
    - AST 구문 검증, 백업 등 안전성 강화
    - 오류 메시지 상세화, 진단 가능성 향상
  - 단점
    - code.py와 스타일/구조(클래스 기반, 함수 중복) 상 이질감
    - 두 구현 병존 시 중복과 복잡도 상승 위험
    - 라인 단위 매칭 → 문자 인덱스 변환, EOL 보존, 기존 indent 로직 연계 필요

결론
- 퍼지매치: ReplaceBlock의 “라인 단위 + 들여쓰기 무시”가 블록 교체에 더 적합
- 들여쓰기 조정: code.py의 adjust_indentation가 이미 유효하므로 유지
- 보강 기능(AST/백업/verbose): ReplaceBlock 기능 흡수 권장
- API: 기존 replace는 하위호환 유지, 옵션 확장으로 고급 기능 노출

2) 최적 통합 방안 (설계 및 코드 예시)

통합 전략
- ReplaceBlock의 핵심 로직을 code.py 내부 “비공개 헬퍼 함수”로 이식해 함수형 스타일 유지
- 기존 replace를 확장(옵션 추가)하고, 편의용 replace_advanced를 별칭으로 제공
- 퍼지매치는 “라인 기반 퍼지”로 단일화하고, 기존 find_fuzzy_match는 래퍼로 대체(호환 유지)
- 들여쓰기 처리는 기존 adjust_indentation 유지
- preview/verbose/validate/backup 옵션을 replace에 추가(기본값 False로 하위호환 유지)

제안 API
- replace(filepath, old_code, new_code, fuzzy=True, threshold=0.8, preview=False, validate=False, backup=False, verbose=False, indent_strategy='auto')
- replace_advanced(...): replace를 호출하되 validate=True, backup=True, verbose=True 등 실용적인 기본값

핵심 통합 코드 예시 (요약)

아래 코드는 방향성과 핵심 로직만 발췌했습니다. 실제 적용 시 기존 코드와 wrap_output, adjust_indentation, 에러 처리 스타일을 맞추십시오.

```python
# code.py 내부

import difflib
import shutil
import tempfile
import os
from typing import Dict, Any, Optional, Tuple, List

# 가정: wrap_output, adjust_indentation 는 기존에 존재
# from .decorators import wrap_output
# from .indent import adjust_indentation

def _detect_eol(s: str) -> str:
    return '\r\n' if '\r\n' in s and s.count('\r\n') >= s.count('\n') else '\n'

def _line_start_offsets(s: str) -> List[int]:
    # 각 라인의 시작 문자 인덱스(0-based)
    offsets = [0]
    for i, ch in enumerate(s):
        if ch == '\n':
            offsets.append(i + 1)
    return offsets

def _find_fuzzy_block_by_lines(content: str, pattern: str, threshold: float = 0.7) -> Optional[Tuple[int, int, float, str, int, int]]:
    """
    라인 단위 퍼지 매칭 (들여쓰기 무시).
    반환: (char_start, char_end, ratio, matched_text, start_line, end_line)
    """
    lines = content.split('\n')
    pattern_lines = pattern.replace('\r\n','\n').replace('\r','\n').split('\n')
    pat_len = len(pattern_lines)
    if pat_len == 0:
        return None

    pattern_stripped = [ln.strip() for ln in pattern_lines]
    pattern_joined = '\n'.join(pattern_stripped)

    best = None
    best_ratio = 0.0
    best_text = ""
    best_span = (0, 0)
    offsets = _line_start_offsets(content)

    for i in range(0, len(lines) - pat_len + 1):
        window = lines[i:i + pat_len]
        window_stripped = [ln.strip() for ln in window]
        window_joined = '\n'.join(window_stripped)

        ratio = difflib.SequenceMatcher(None, pattern_joined, window_joined).ratio()
        if ratio >= threshold and ratio > best_ratio:
            best_ratio = ratio
            best = (i, i + pat_len)
            best_text = '\n'.join(window)

    if not best:
        return None

    start_line, end_line = best
    # 문자 인덱스로 변환
    char_start = _line_start_offsets(content)[start_line]
    matched_text = '\n'.join(lines[start_line:end_line])
    char_end = char_start + len(matched_text)
    return (char_start, char_end, best_ratio, matched_text, start_line, end_line)

def _generate_preview(old_text: str, new_text: str, n: int = 3) -> str:
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile='old',
        tofile='new',
        lineterm=''
    )
    # 요약 길이 조절은 호출부에서
    return '\n'.join(diff)

def _backup_file(path: str) -> str:
    base = f"{path}.bak"
    if not os.path.exists(base):
        shutil.copy2(path, base)
        return base
    # 충돌 시 증가 숫자
    idx = 1
    while True:
        candidate = f"{base}.{idx}"
        if not os.path.exists(candidate):
            shutil.copy2(path, candidate)
            return candidate
        idx += 1

def _validate_python_syntax(path: str, text: str) -> Optional[str]:
    # .py 파일에만 적용
    _, ext = os.path.splitext(path)
    if ext.lower() != '.py':
        return None
    try:
        import ast
        ast.parse(text)
        return None
    except Exception as e:
        return f"AST validation failed: {e}"

def _atomic_write(path: str, text: str, eol: str = '\n'):
    # EOL 복원
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', eol)
    dir_ = os.path.dirname(os.path.abspath(path)) or '.'
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix='.tmp_replace_')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise

# 기존 함수가 있다면 호환 래퍼로 대체/대입
def find_fuzzy_match(content: str, old_code: str, threshold: float):
    res = _find_fuzzy_block_by_lines(content, old_code, threshold)
    if not res:
        return None
    char_start, char_end, ratio, matched_text, *_ = res
    return (char_start, char_end, matched_text)

@wrap_output
def replace(
    filepath: str,
    old_code: str,
    new_code: str,
    fuzzy: bool = True,
    threshold: float = 0.8,
    preview: bool = False,
    validate: bool = False,
    backup: bool = False,
    verbose: bool = False,
    indent_strategy: str = 'auto'
) -> Dict[str, Any]:
    # 파일 읽기
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        raw = f.read()
    original_eol = _detect_eol(raw)

    content = raw.replace('\r\n', '\n').replace('\r', '\n')
    old_code = old_code.replace('\r\n', '\n').replace('\r', '\n')
    new_code = new_code.replace('\r\n', '\n').replace('\r', '\n')

    # 후행 공백 제거된 old_code로 정확매치 먼저
    old_lines = [ln.rstrip() for ln in old_code.split('\n')]
    old_code_norm = '\n'.join(old_lines)

    match_start = -1
    match_end = -1
    matched_text = ""
    ratio = 1.0
    match_found = False

    if old_code_norm in content:
        match_start = content.index(old_code_norm)
        match_end = match_start + len(old_code_norm)
        matched_text = old_code_norm
        match_found = True
        if verbose:
            pass  # 필요 시 로그
    elif fuzzy:
        fuzzy_res = _find_fuzzy_block_by_lines(content, old_code, threshold)
        if fuzzy_res:
            match_start, match_end, ratio, matched_text, *_ = fuzzy_res
            match_found = True

    if not match_found:
        # 기존 친절한 오류 메시지 + 보강
        lines = content.split('\n')
        snippet = []
        search_pattern = old_lines[0].strip() if old_lines else ""
        for i, ln in enumerate(lines):
            if search_pattern and search_pattern in ln:
                start = max(0, i - 2); end = min(len(lines), i + 3)
                snippet = lines[start:end]
                break
        msg = f"Pattern not found in {filepath}"
        if snippet:
            msg += "\nDid you mean this area?\n" + '\n'.join(snippet)
        raise ValueError(msg)

    # 들여쓰기 타겟 계산(기존 로직 유지)
    before = content[:match_start]
    lines_before = before.split('\n')
    if lines_before:
        last_line = lines_before[-1] if match_start > 0 else ""
        target_indent = len(last_line) - len(last_line.lstrip())
    else:
        target_indent = 0

    # 매칭이 라인 중간이면 현재 라인 prefix 길이 사용
    if match_start > 0 and content[match_start - 1] != '\n':
        line_start = content.rfind('\n', 0, match_start) + 1
        line_prefix = content[line_start:match_start]
        target_indent = len(line_prefix)

    # 들여쓰기 적용
    preserve_relative = True
    adjusted_new = adjust_indentation(new_code, target_indent, preserve_relative=preserve_relative)

    # 새 파일 내용 생성
    new_content = content[:match_start] + adjusted_new + content[match_end:]

    # AST 검증
    if validate:
        err = _validate_python_syntax(filepath, new_content)
        if err:
            raise ValueError(err)

    # preview 모드
    preview_text = None
    if preview:
        preview_text = _generate_preview(matched_text, adjusted_new)

    # 백업
    backup_path = None
    if not preview and backup:
        backup_path = _backup_file(filepath)

    # 쓰기(프리뷰면 미기록)
    if not preview:
        _atomic_write(filepath, new_content, eol=original_eol)

    # 응답 데이터
    data = {
        "filepath": filepath,
        "changed": not preview,
        "preview": bool(preview),
        "backup_path": backup_path,
        "match": {
            "start": match_start,
            "end": match_end,
            "ratio": ratio,
            "lines": len(matched_text.split('\n')),
        },
        "indent": target_indent,
        "meta": {
            "fuzzy_used": fuzzy and ratio < 1.0,
            "threshold": threshold,
            "verbose": verbose,
        }
    }
    if preview:
        data["diff"] = preview_text
        data["old_excerpt"] = matched_text[:1000]
        data["new_excerpt"] = adjusted_new[:1000]

    return data

def replace_advanced(
    filepath: str,
    old_code: str,
    new_code: str,
    fuzzy: bool = True,
    threshold: float = 0.75,
    preview: bool = False,
    validate: bool = True,
    backup: bool = True,
    verbose: bool = True,
    indent_strategy: str = 'auto'
) -> Dict[str, Any]:
    # wrap_output은 replace에 달려 있으므로 여기서는 그대로 위임
    return replace(
        filepath=filepath,
        old_code=old_code,
        new_code=new_code,
        fuzzy=fuzzy,
        threshold=threshold,
        preview=preview,
        validate=validate,
        backup=backup,
        verbose=verbose,
        indent_strategy=indent_strategy
    )
```

설명
- 퍼지매치: _find_fuzzy_block_by_lines로 단일화(ReplaceBlock의 장점 흡수). 들여쓰기 무시한 라인 비교로 블록 교체에 강인
- 들여쓰기: 기존 adjust_indentation 재사용
- backup/validate/verbose/preview: replace에 옵션으로 추가(기본 False)해 하위호환 유지
- EOL 보존, 원자적 쓰기 추가로 안정성 강화
- 기존 find_fuzzy_match는 새 구현의 래퍼로 교체해 내부 중복 제거 및 하위호환

3) 단계별 통합 계획

- 0단계: 작업 브랜치 생성, CI 파이프라인에 새 테스트 잡 추가
- 1단계: ReplaceBlock 핵심 기능 이식
  - _find_fuzzy_block_by_lines, _line_start_offsets, _backup_file, _validate_python_syntax, _detect_eol, _atomic_write, _generate_preview 추가
  - 기존 find_fuzzy_match는 래퍼로 교체(내부적으로 새 함수 호출)
- 2단계: replace 확장
  - 새 옵션(validate, backup, verbose, indent_strategy) 추가. 기본값 False로 하위호환 보장
  - preview 응답에 diff 추가(기존 동작은 유지하되 확장)
- 3단계: 중복 제거
  - code.py 내 기존 퍼지매치 구현(문자 단위)이 있다면 사용처를 새 로직으로 통일
  - 들여쓰기 보정은 기존 adjust_indentation 유지
- 4단계: 새 alias 제공
  - replace_advanced 추가(실무 친화적 기본값: validate=True, backup=True, verbose=True)
- 5단계: 문서/도크스트링/사용 예 업데이트
  - 옵션 의미, 기본값, 예시, 주의사항
- 6단계: 점진적 마이그레이션
  - 내부 호출부가 기존 replace를 사용 중이라면 영향 없음
  - 외부 사용자는 필요 시 replace_advanced 사용 권고

4) 위험 요소와 해결 방안

- 퍼지 오탐(유사 블록이 여러 곳 존재)
  - 위험: 잘못된 블록을 교체
  - 해결: threshold를 보수적으로 유지(기본 0.8), preview로 확인, verbose로 매칭 범위/유사도 노출
  - 추가 옵션 제안(후속): occurrence(1-based), search_range(lines: tuple), anchor_before/after
- 성능 저하(매우 큰 파일)
  - 위험: 모든 라인 윈도우 비교 비용
  - 해결: 패턴 라인 수가 N이면 O((M-N)*N)인데 보통 N이 작음. 필요 시 윈도우 샘플링/스킵 최적화 옵션 도입
- EOL 변화
  - 위험: CRLF → LF로 바뀌는 회귀
  - 해결: _detect_eol로 원래 EOL 유지(이미 코드 반영)
- AST 검증 오탐
  - 위험: .py 이외 확장자에서 불필요 오류
  - 해결: .py 에서만 검증, 실패 시 미기록 + 명확 메시지
- 백업 파일 누적
  - 위험: 디스크 사용 증가
  - 해결: 순번 백업 제공, 팀 합의에 따라 보존 기간/개수 정책 도입 가능
- 동시성/원자성
  - 위험: 쓰기 도중 실패
  - 해결: _atomic_write로 임시 파일 + os.replace 사용

5) 테스트 계획

카테고리 및 핵심 케이스
- 정확 매치
  - 동일 블록 교체, preview False/True
  - EOL CRLF 파일에서 교체 후 EOL 보존 확인
- 퍼지 매치(들여쓰기 차이)
  - old_code의 들여쓰기를 변경해도 성공
  - threshold 경계값(0.79 실패/0.80 성공 등)
- 특수 문자열
  - f-string, raw string, 백슬래시, 삼중따옴표 멀티라인 블록 교체
- 반복 패턴 다수
  - 동일한 블록 2개 이상 존재 시 최대 유사도 선택 확인
  - 추후 occurrence 옵션 추가 시 지정 인덱스 교체 검증
- AST 검증
  - validate=True에서 문법 오류 유발 교체 → 실패/롤백(미기록) 확인
  - 정상 교체 → 통과
- 백업
  - backup=True 시 .bak 생성, 충돌 시 .bak.N 생성
- 미리보기/디프
  - preview=True일 때 파일 미수정, diff 포함 확인
- 경계 조건
  - 파일 시작/끝 위치 매치
  - 라인 중간 매치(현재 라인 prefix 들여쓰기 반영)
  - 빈 패턴, 매우 짧은 패턴 실패 처리
- 회귀
  - 기존 replace 기본 옵션 호출 경로가 과거와 동일 동작(하위호환)

추가 권장 사항
- 퍼지 오탐 방지를 위한 선택적 보호장치(occurrence, search_range)를 다음 릴리즈에 추가
- replace/insert/delete 공통 미리보기(diff) 유틸을 통합해 일관 출력 유지
- verbose일 때 meta에 pattern_type, match_window(라인 범위), matched_excerpt 등 진단 정보 확장

요약 결론
- 퍼지매치는 ReplaceBlock의 라인 기반 알고리즘으로 통일
- 들여쓰기는 code.py의 adjust_indentation 유지
- replace는 하위호환 유지하면서 validate/backup/verbose/indent_strategy 등 확장
- replace_advanced 제공으로 고급 사용성 강화
- 백업/AST 검증/원자적 쓰기로 안전성 향상
- 테스트 체계 강화로 회귀 방지

위 코드 예시와 계획대로 진행하면, replace_block_final.py의 고급 기능을 code.py에 안정적으로 흡수하면서도 기존 사용자의 경험을 해치지 않고 한 파일(모듈)로 통합할 수 있습니다.