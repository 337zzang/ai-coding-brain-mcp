# 헬퍼 시스템 통합 계획

생성일: 2025-07-19 22:26:55

## 현재 상황
- ai_helpers_v2: 13개 파일
- ai_helpers_new: 6개 파일
- 공통 파일: 1개
- v2 고유: 12개
- new 고유: 5개

## 통합 방향 (o3 권장사항)
1. ai_helpers_new를 기준으로 통합
2. v2의 필요한 기능만 포팅
3. 단일 'ai_helpers' 패키지로 통합
4. json_repl_session.py 수정

## 파일별 분석
### 공통 파일
- __init__.py

### v2 고유 파일
- llm_ops.py
- file_ops.py
- git_ops.py
- file_result_utils.py
- code_ops.py
- ez_code.py
- safe_code_modifier.py
- search_ops.py
- helper_result.py
- improved_ast_parser.py
- core.py
- project_ops.py

### new 고유 파일
- file.py
- search.py
- code.py
- llm.py
- util.py
