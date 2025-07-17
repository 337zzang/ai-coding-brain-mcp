# execute_code Tool

## 개요
Python 코드를 영속적 REPL 세션에서 실행하는 핵심 도구입니다.

## 주요 기능

### 1. 영속적 세션
- 모든 변수와 상태가 execute_code 호출 간에 유지됩니다
- 한 번 정의한 변수는 다음 호출에서도 사용 가능합니다
- 세션이 종료되어도 파일로 저장된 데이터는 보존됩니다

### 2. 프로젝트별 격리
- 각 프로젝트는 독립적인 Python 환경을 가집니다
- 프로젝트 전환 시 자동으로 환경이 전환됩니다
- memory/ 디렉토리에 프로젝트별 데이터가 저장됩니다

### 3. 헬퍼 함수 (76개+)
- 파일 시스템 조작: read_file, write_file, create_file 등
- Git 통합: git_status, git_commit, git_push 등
- 코드 분석: parse_file, find_function, search_code 등
- 프로젝트 관리: flow_project, list_projects, project_info 등

### 4. Safe 함수 시리즈
더 안전한 에러 처리를 제공하는 함수들:
- safe_parse_file(): 코드 파싱 with 에러 처리
- safe_find_function(): 함수 검색 with 에러 처리
- safe_replace_block(): 코드 수정 with 백업
- safe_git_status(): Git 상태 확인 with 에러 처리

## 사용 예시

### 기본 사용
```python
# 변수 정의
data = [1, 2, 3, 4, 5]
print(f"데이터: {data}")
```

### 파일 작업
```python
# 파일 읽기
content = helpers.read_file("example.txt")

# 파일 쓰기
helpers.write_file("output.txt", "Hello World")
```

### Git 작업
```python
# 상태 확인
status = helpers.git_status()

# 커밋
helpers.git_add(".")
helpers.git_commit("feat: 새 기능 추가")
```

## 주의사항

### Import 규칙
부트스트랩이 작동하지 않으므로 명시적 import가 필요합니다:
```python
from datetime import datetime as dt
import json, re, random
from pathlib import Path
```

### 메모리 관리
- 대용량 데이터는 파일로 저장하여 메모리 사용량을 줄이세요
- 필요시 restart_json_repl로 세션을 초기화할 수 있습니다

### 성능 최적화
- 큰 파일은 청크 단위로 처리하세요 (write_file의 mode='append' 활용)
- 복잡한 작업은 단계별로 나누어 실행하세요
