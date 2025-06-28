# 🧠 Project Wisdom - 

## 📌 프로젝트 비전
프로젝트 작업 중 축적된 지혜와 교훈을 관리합니다.

## 🐛 자주 발생하는 오류 패턴

## ❌ 자주 하는 실수들

### long_function (29회)
- 올바른 방법: 문서를 참고하세요

### console_usage (11회)
- 올바른 방법: import { logger } from '../utils/logger'; logger.info('메시지');

### hardcoded_path (7회)
- 올바른 방법: 문서를 참고하세요

### large_class (3회)
- 올바른 방법: 문서를 참고하세요

### too_many_parameters (3회)
- 올바른 방법: 문서를 참고하세요

### direct_flow (1회)
- 올바른 방법: execute_code: helpers.cmd_flow_with_context('project-name')

## ✅ 베스트 프랙티스

### debugging
- import 경로 문제 시 sys.path 확인 및 절대 경로 사용
- 버그 수정 시 근본 원인 분석 후 사용성 개선까지 고려

### design
- Task 추가 시 현재 컨텍스트(phase) 자동 활용으로 UX 개선
