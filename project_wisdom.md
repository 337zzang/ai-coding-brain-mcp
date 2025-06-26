# 🧠 Project Wisdom - 

*최종 업데이트: 2025-06-25 17:21*

## 📌 프로젝트 비전
## 🐛 자주 발생하는 오류 패턴

### FileDirectoryUpdateError (1회)
- 처음 발견: 2025-06-25
- 예시:
  - `enhanced_file_directory_generator.py에 구문 오류`

### AttributeError (1회)
- 처음 발견: 2025-06-25
- 예시:
  - `ASTParser has no attribute get_snippet_preview - 라인 513 수정 필요`

## ❌ 자주 하는 실수들

### api_assumption (2회)
- 처음 발견: 2025-06-25
- 발생 위치: get_project_structure() 반환 형식 잘못 가정, search_files_advanced() 키 이름 잘못 가정

### console_usage (1회)
- 처음 발견: 2025-06-24
- 발생 위치: in test.py

### direct_flow (1회)
- 처음 발견: 2025-06-24
- 발생 위치: in test.py

### manual_indentation (1회)
- 처음 발견: 2025-06-25
- 발생 위치: enhanced_flow.py 수정 중 수동 들여쓰기로 오류 발생

### manual_code_edit (1회)
- 처음 발견: 2025-06-25
- 발생 위치: plan.py 대규모 수정

## ✅ 베스트 프랙티스

### Development
- search_code_content 사용 시 file_extensions=['py'] 형태로 사용
- 함수 시그니처는 일관성 있게 유지 - wrapper와 원본 함수가 동일한 파라미터 사용

### Documentation
- tool-definitions.ts 문서도 함께 업데이트하여 사용법 명확히 문서화
- UserPreferences v23.0: Python 코드 수정 안전 가이드 추가로 들여쓰기 오류 방지

### Compatibility
- Pydantic v2에서는 모델을 dictionary로 변환하여 처리 (plan_to_dict 패턴 사용)

### Workflow
- flow_project 실행 시 file_directory.md 자동 업데이트로 항상 최신 구조 유지

### Performance
- flow_project 실행 시 file_directory.md 캐시 활용으로 성능 향상
- Lazy Loading으로 초기 로드 시간 단축
- 성능 측정을 통한 최적화 포인트 파악

### Coding_Standards
- 파일 수정 시 항상 AST 기반 도구(helpers.replace_block) 사용으로 들여쓰기 오류 방지

### Architecture
- DLC 아키텍처로 필요한 기능만 동적 로드하여 성능 최적화
- 모듈별 독립적 개발과 테스트로 유지보수성 향상
- ProjectAnalyzer를 활용하여 AI 명령어 지능화
- 프로젝트별 Wisdom 분리로 맥락에 맞는 조언 제공

### Debugging
- API 사용 전 항상 반환 형식 확인: type(), keys(), 첫 번째 항목 출력
- inspect_result() 헬퍼로 API 반환값 안전하게 검사
- 순환 import 문제 시 함수를 직접 구현하여 해결
- get_snippet_preview 오류시 read_file + 문자열 검색 사용

### Safety
- 함수 호출 시 작은 테스트로 반환 형식 먼저 검증
- 백업 생성 후 작업 - 실패시 즉시 복원 가능
- 자동 백업으로 작업 손실 방지

### Maintenance
- file_directory.md 업데이트는 file_directory_generator.py의 create_file_directory_md() 사용
- 구형 코드는 백업 후 제거하여 코드베이스 정리
- 구형 코드 제거로 코드베이스 정리 및 유지보수성 향상

### Code_Quality
- 사용하지 않는 주석 블록은 삭제하여 코드 가독성 향상
- Pydantic v2에서는 .dict() 대신 .model_dump() 사용

### Feature
- 대화형 계획 수립 기능 추가 - 사용자와 상호작용하며 계획 수립

### Code_Modification
- 대규모 함수 수정시 edit_block 50줄 제한 주의 - 분할 수정 필요

### Validation
- AST 컴파일로 Python 문법 검증 - compile() 함수 사용

### Bug_Discovery
- ast_parser_helpers.py의 get_snippet_preview 버그 발견 - ASTParser 클래스와 인터페이스 불일치

### Integration
- plan.py에 Wisdom 시스템 통합으로 계획 수립 효율성 향상

### Ux
- enhanced_flow에 verbose 옵션 추가로 사용자 경험 개선
- flow_project에 verbose 옵션 추가로 사용성 개선

### Refactoring
- enhanced_flow 개선: 성능 추적, Wisdom 통합, UX 개선

### Configuration
- 프로젝트별 설정 파일로 커스터마이징 가능

### Visualization
- Wisdom 시각화로 개발 패턴을 한눈에 파악

