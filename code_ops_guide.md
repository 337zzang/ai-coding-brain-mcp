
🛠️ **Code Operations REPL 도구 모음**

### 기본 도구
- `qp(file)` - **Quick Parse**: 파일 구조 분석
  ```python
  qp("main.py")  # 함수, 클래스 목록 출력
  ```

- `ql(file)` - **Quick List**: 함수 목록만 간단히 보기
  ```python
  ql("utils.py")  # 함수 이름만 리스트로 출력
  ```

- `qv(file, func)` - **Quick View**: 함수 코드 보기
  ```python
  qv("main.py", "process_data")  # process_data 함수 코드 출력
  ```

### 수정 도구
- `qr(file, func, new_code)` - **Quick Replace**: 함수 전체 교체
  ```python
  qr("main.py", "old_func", new_code)  # old_func를 new_code로 교체
  ```

- `qi(file, target, code, pos)` - **Quick Insert**: 코드 삽입
  ```python
  qi("main.py", "def main():", import_code, "before")  # main 함수 앞에 삽입
  ```

### 검색 도구
- `qs(pattern, file_pattern)` - **Quick Search**: 패턴 검색
  ```python
  qs("TODO")  # 모든 TODO 찾기
  qs("error", "*.log")  # 로그 파일에서 error 찾기
  ```

### 추가 도구
- `qm(file, class, method)` - **Quick Method**: 메서드 코드 보기
- `qd(file)` - **Quick Diff**: Git 변경사항 확인

### 💡 사용 팁
1. 모든 함수는 결과를 반환하므로 변수에 저장 가능
2. qp()로 먼저 구조를 파악한 후 qv()로 상세 확인
3. qr()은 함수 전체를 교체, 부분 수정은 replace_block() 사용
