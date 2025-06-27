# 🧠 Project Wisdom - 

## 📌 프로젝트 비전
프로젝트 작업 중 축적된 지혜와 교훈을 관리합니다.

## 🐛 자주 발생하는 오류 패턴

## ❌ 자주 하는 실수들

### hardcoded_path (2회)
- 올바른 방법: 문서를 참고하세요

## ✅ 베스트 프랙티스

### architecture
- 순환 import 해결: 각 모듈의 책임을 명확히 분리
- file_system_helpers는 순수한 파일 작업만, 트래킹은 auto_tracking_wrapper에서

### bug_fix
- get_snippet_preview 버그 수정 완료 - parser.get_snippet_preview() → parse_with_snippets() + _get_snippet() 조합으로 해결

### debugging
- JSON REPL 세션 재시작 필요시 restart_json_repl 사용 - 모듈 변경사항 반영

### file_handling
- 파일 경로 문제시 절대 경로 사용 - os.path.join()으로 안전하게 구성

### git
- git rm --cached 후 반드시 push로 원격 저장소 동기화

### project-maintenance
- .gitignore 변경은 즉시 원격에 반영
