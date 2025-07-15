
# AI Coding Brain MCP - 유저 프롬프트 개선 가이드

## 🎯 최적 사용 패턴을 위한 프롬프트 작성법

### 1. 프로젝트 시작 프롬프트
```
프로젝트: [프로젝트명]
/flow [프로젝트명]으로 전환 후 작업 시작

주요 작업:
1. [작업1]
2. [작업2]

워크플로우로 진행 상황 추적하면서 작업해주세요.
```

### 2. 코드 분석 및 수정 프롬프트 (권장)
```
다음 파일들을 분석하고 개선해주세요:
- [파일1.py]
- [파일2.py]

분석 기준:
- TODO 항목 확인
- 중복 코드 찾기
- 성능 개선 가능 부분

parse_file()과 replace_block()을 활용해서 안전하게 수정해주세요.
각 수정 전에 확인 받고, Git 백업도 해주세요.
```

### 3. 연속 작업 프롬프트 (stdout 체인 활용)
```
다음 작업을 단계별로 진행해주세요:

Phase 1: 프로젝트 구조 분석
- scan_directory()로 전체 구조 파악
- 주요 파일 식별

Phase 2: 코드 품질 검사
- parse_file()로 각 파일 분석
- 문제점 리스트 작성

Phase 3: 개선 작업
- 문제점별로 수정 계획 수립
- replace_block()으로 안전하게 수정

각 Phase 완료 시 [NEXT_ACTION] 태그로 다음 작업 지시하고,
task_context 변수에 상태를 저장해서 이어갈 수 있게 해주세요.
```

### 4. Git 통합 작업 프롬프트
```
작업 시작 전 git_status()로 현재 상태 확인하고,
주요 변경사항마다 의미있는 커밋을 만들어주세요.

커밋 규칙:
- feat: 새 기능
- fix: 버그 수정
- refactor: 리팩토링
- docs: 문서 수정

작업 완료 후 전체 변경사항 요약해주세요.
```

### 5. 효율적인 검색 프롬프트
```
다음 패턴들을 코드에서 찾아주세요:
- "TODO" 또는 "FIXME" 주석
- try-except 없는 위험한 코드
- 하드코딩된 값들

search_code()를 사용해서 효율적으로 검색하고,
결과를 카테고리별로 정리해주세요.
```

## 🚀 권장 작업 흐름

### 시작
```
fp("프로젝트명")
workflow("/start 작업명")
show_history()  # 이전 작업 확인
```

### 분석
```
parsed = parse_file("main.py")
# 안전한 dict 반환 - 함수, 클래스 정보
```

### 수정
```
replace_block("file.py", old_code, new_code)
# 자동 백업 생성
```

### 완료
```
git_add(".") 
git_commit("작업 내용")
workflow("/complete 작업 요약")
```

## 📌 피해야 할 패턴

❌ "helpers.parse_with_snippets() 사용해서..."
✅ "parse_file() 사용해서..."

❌ "결과['snippets'][0].name 접근..."
✅ "결과['functions'][0]['name'] 접근..."

❌ "모든 파일을 한번에 수정..."
✅ "단계별로 확인받으며 수정..."

## 💡 고급 팁

1. **변수로 상태 관리**
   - task_context, analysis_result 등 딕셔너리 활용
   - 여러 execute_code 호출 간 데이터 공유

2. **stdout 활용**
   - [NEXT_ACTION]: 다음 작업 지시
   - [CONTEXT]: 참조할 변수
   - [STATUS]: 현재 진행 상황

3. **히스토리 활용**
   - add_history()로 중요 작업 기록
   - continue_from_last()로 이전 작업 재개

4. **안전한 함수 우선**
   - parse_file, search_code, git_status 등
   - 모든 반환값이 dict/list[dict]로 일관성 있음
