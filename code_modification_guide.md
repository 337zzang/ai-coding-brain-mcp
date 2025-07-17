
## 🎯 REPL 환경에서 효율적인 코드 수정 가이드

### ✅ 검증된 방법

1. **라인 기반 수정 (가장 효율적)**
```python
def replace_function(filepath, func_name, new_code):
    # 1. parse_file로 위치 정보 획득
    parsed = parse_file(filepath)
    target = next((f for f in parsed['functions'] if f['name'] == func_name), None)

    # 2. 파일을 라인 단위로 읽기
    lines = helpers.read_file(filepath).splitlines(keepends=True)

    # 3. 새 코드 준비 (개행 문자 확인)
    new_lines = new_code.splitlines(keepends=True)
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'

    # 4. 라인 단위로 교체 (0-based index)
    start_idx = target['start'] - 1
    end_idx = target['end']
    result_lines = lines[:start_idx] + new_lines + lines[end_idx:]

    # 5. 저장
    helpers.write_file(filepath, ''.join(result_lines))
```

2. **AST 활용 (정밀한 위치 정보)**
- Python 3.9+에서 end_lineno, end_col_offset 제공
- 컬럼 단위까지 정확한 수정 가능

3. **Desktop Commander 활용**
- 복잡한 패턴 매칭이 필요한 경우
- DC의 edit_block 사용 (전체 경로 필요)

### ⚠️ 주의사항

1. **개행 문자 처리**
- splitlines(keepends=True) 사용 필수
- 마지막 줄 개행 확인

2. **인덱스 변환**
- parse_file은 1-based line numbers
- Python 리스트는 0-based index

3. **들여쓰기 유지**
- 원본 함수의 들여쓰기 레벨 확인
- 새 코드에 동일한 들여쓰기 적용

### ❌ 사용하지 말아야 할 것들
- helpers.replace_block() - 작동 안 함
- safe_replace_block() - 동일한 문제
- 부정확한 문자열 매칭

### 💡 REPL 세션 활용 팁
1. 파싱 결과를 변수에 저장하여 재사용
2. 자주 사용하는 수정 함수를 세션에 정의
3. 큰 파일은 필요한 부분만 메모리에 로드
