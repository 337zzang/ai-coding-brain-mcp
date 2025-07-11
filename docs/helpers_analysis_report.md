# AI Helpers 모듈 구조 분석 보고서

## 1. 현재 모듈 구조

### 1.1 ai_helpers 서브모듈 (16개)
- **search.py**: 검색 관련 함수 11개 (scan_directory_dict, search_files_advanced 등)
- **decorators.py**: 데코레이터 및 추적 함수 9개
- **code.py**: AST 기반 코드 수정 클래스 6개 (ASTParser, FunctionReplacer 등)
- **legacy_replacements.py**: 폐기 예정 함수 4개
- **file.py**: 파일 I/O 함수 3개
- **context.py**: 컨텍스트 관련 함수 2개
- **search_helpers.py**: 검색 호환성 함수 2개
- 기타: build.py, compile.py, git.py, helper_result.py, project.py, utils.py

### 1.2 메인 헬퍼 파일
- **helpers_wrapper.py**: HelpersWrapper 클래스, safe_helper 함수
- **helper_result.py**: HelperResult 클래스
- **git_fallback_helpers.py**: GitFallbackHelpers 클래스
- **search_helpers_standalone.py**: 독립 실행용 검색 헬퍼
- **helpers_convenience.py**: init_wrapped_helpers 함수

## 2. 발견된 중복 함수

1. **_safe_import_parse_with_snippets()**
   - 위치: code.py, file.py
   - 문제: 동일한 함수가 두 모듈에 중복 정의

2. **get_project_context()**
   - 위치: context.py, decorators.py
   - 문제: 컨텍스트 접근 로직 중복

3. **track_file_access()**
   - 위치: file.py, legacy_replacements.py
   - 문제: 파일 추적 로직 중복

4. **검색 관련 함수들**
   - search_helpers.py와 search.py에서 동일 함수 중복 import 시도
   - list_file_paths, grep_code, scan_dir

## 3. 주요 문제점

### 3.1 모듈 초기화 문제
- __init__.py에서 try/except로 불완전한 import
- 실패 시 더미 함수 정의로 인한 혼란
- 동일 함수를 여러 곳에서 중복 import

### 3.2 인터페이스 일관성 부족
- 일부 함수는 dict 반환, 일부는 HelperResult 반환
- Git 헬퍼 함수들이 명확히 정의되지 않음
- 워크플로우 함수들이 문자열 명령 기반

### 3.3 구조적 문제
- 레거시 코드와 새 코드가 혼재
- 목적별 그룹화가 불명확
- 중복 구현으로 인한 유지보수 어려움

## 4. 개선 방향

### 4.1 즉시 개선 가능
- 중복 함수 제거
- 더미 함수 대신 명확한 에러 처리
- search_helpers.py와 search.py 통합

### 4.2 단계별 개선 필요
- 모든 헬퍼가 HelperResult 반환하도록 표준화
- Git/워크플로우 헬퍼 인터페이스 개선
- 레거시 모듈 단계적 제거

### 4.3 장기 개선 목표
- 목적별 모듈 재구성
- HelpersWrapper 자동 적용
- 타입 힌트 및 문서화 강화
