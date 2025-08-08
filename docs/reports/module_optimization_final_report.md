# 모듈 최적화 및 코드 정리 분석 보고서

생성일: 2025-08-04

## 📋 전체 요약

### 분석 대상
1. **json_repl_session.py** - 핵심 REPL 세션 모듈
2. **AI Helpers 모듈** (9개) - file, code, search, git, llm, project, flow_api, task_logger, wrappers

## 🔴 즉시 수정 필요 (Critical)

### 1. json_repl_session.py
- **레거시 코드 제거**
  - 라인 156, 160: wf, flow 전역 변수 및 import
  - 라인 172, 244, 276: fp 변수 참조

- **표준 응답 형식 미준수**
  - 현재: `{'success': True, 'stdout': '', 'stderr': ''}`
  - 목표: `{'ok': bool, 'data': Any, 'error': str}`

- **보안 문제**
  - AST 검증 없이 exec() 직접 실행
  - 전체 builtins 노출

### 2. task_logger.py
- **모든 함수 표준 응답 형식 미준수** (20개 함수)
- 현재 None 반환 → 표준 형식으로 수정 필요

## 🟡 중기 개선 필요

### 1. 대형 모듈 분할
- **code.py** (515줄) → 파싱/수정/검증 모듈로 분할
- **llm.py** (641줄) → O3/컨텍스트빌더 분리
- **task_logger.py** (621줄) → 로거/분석기 분리

### 2. 함수 분할
- **execute_code()** (56줄) → 20줄 단위 3개 함수
- **main()** (80줄) → 초기화/루프/처리 분리

## 🟢 장기 개선 사항

### 1. 아키텍처 개선
- Session/CodeRunner/ApiAdapter 분리
- Subprocess Worker 통합
- 의존성 주입 패턴 적용

### 2. 테스트 및 문서화
- 단위 테스트 추가
- API 문서 자동 생성
- 타입 힌트 완성

## ✅ 유저프리퍼런스 준수 현황

| 원칙 | 현재 상태 | 개선 필요 |
|------|----------|-----------|
| 표준 응답 형식 | ❌ 대부분 미준수 | 전체 모듈 수정 |
| Flow API 통합 | ✅ 19개 메서드 완료 | - |
| AST 검증 | ❌ 없음 | execute_code 수정 |
| execute_code 분할 실행 | ⚠️ 부분적 | 개선 필요 |
| 완전한 추적성 | ⚠️ TaskLogger 있으나 미사용 | 통합 필요 |

## 🚀 실행 계획

### Phase 1 (즉시)
1. json_repl_session.py 레거시 코드 제거
2. 표준 응답 형식으로 전환
3. AST 검증 추가

### Phase 2 (1주일 내)
1. task_logger.py 표준화
2. 대형 모듈 분할
3. 보안 강화

### Phase 3 (2주일 내)
1. 테스트 작성
2. 문서화
3. 성능 최적화
