# 🧠 Project Wisdom - 

## 📌 프로젝트 비전
프로젝트 작업 중 축적된 지혜와 교훈을 관리합니다.

## 🐛 자주 발생하는 오류 패턴

## ❌ 자주 하는 실수들

## ✅ 베스트 프랙티스

### architecture
- 순환 import 해결: 각 모듈의 책임을 명확히 분리
- file_system_helpers는 순수한 파일 작업만, 트래킹은 auto_tracking_wrapper에서
- 자동 저장 데코레이터(@autosave)를 상태 변경 메서드에 적용하여 데이터 안정성 확보
- Pydantic 모델에 비즈니스 로직을 메서드로 구현하여 타입 안전성과 캡슐화 확보
- 이원화된 데이터 구조(Plan.tasks와 context.tasks['next'])를 단일화하여 동기화 문제 해결
- 상태 전환 로직을 모델 메서드(transition_to)로 캡슐화하여 일관성 확보
- WorkflowManager 패턴으로 비즈니스 로직을 중앙화하여 유지보수성 향상

### bug_fix
- get_snippet_preview 버그 수정 완료 - parser.get_snippet_preview() → parse_with_snippets() + _get_snippet() 조합으로 해결

### debugging
- JSON REPL 세션 재시작 필요시 restart_json_repl 사용 - 모듈 변경사항 반영

### file_handling
- 파일 경로 문제시 절대 경로 사용 - os.path.join()으로 안전하게 구성

### task_management
- Task 상태 이력을 추적하여 작업 분석 및 시간 추정 정확도 향상
