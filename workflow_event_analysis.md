# 워크플로우 및 이벤트 시스템 분석 보고서

## 전체 구조
- 총 모듈: 50개
- 총 클래스: 82개  
- 총 함수: 575개

## 핵심 아키텍처

### 1. 워크플로우 시스템 (workflow.v3)
- WorkflowManager: 싱글톤 패턴으로 전체 워크플로우 관리
- WorkflowDispatcher: 명령어 라우팅 및 실행
- CommandParser: 사용자 명령어 파싱
- WorkflowStorage: 상태 영속성 관리

### 2. 이벤트 시스템
- EventBus: 중앙 이벤트 버스 (publish/subscribe 패턴)
- BaseEventListener: 모든 리스너의 추상 기본 클래스
- 13개의 구체적인 리스너 구현체

### 3. 통합 포인트
- WorkflowEventAdapter: 워크플로우와 이벤트 시스템 연결
- ContextIntegration: 워크플로우와 컨텍스트 매니저 연결
- TaskContextManager: 태스크별 컨텍스트 관리

## 이벤트 흐름
사용자 명령 → Parser → Dispatcher → Manager → EventBus → Listeners

## 사용되지 않는 함수 (120개 중 주요 항목)
- 테스트 관련 함수들
- 미구현 데코레이터 (rate_limit, auto_save)
- 일부 유틸리티 함수들
