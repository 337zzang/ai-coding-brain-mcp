
# 프로젝트 전환 시스템 오류 분석 요청

## 🚨 발생한 문제들

### 1. 프로젝트 컨텍스트 불일치
- flow_project_with_workflow("ai-coding-brain-mcp") 실행 후
- os.getcwd()는 변경되었지만 get_current_project()는 이전 프로젝트 반환
- Session의 project_context가 제대로 업데이트되지 않음

### 2. 반환값 구조 불일치
- 함수마다 다른 키 사용: 'project' vs 'project_name'
- 일관성 없는 응답 구조

### 3. Task Number None 문제
- Task 생성 시 number 필드가 None으로 설정됨
- UltraSimpleFlowManager.create_task에서 번호 할당 누락

### 4. Flow Repository 프로젝트 분리 미흡
- 다른 프로젝트의 플랜이 조회되는 문제
- 프로젝트별 독립적인 저장소 경로가 필요

## 🔍 코드 구조

### Session (싱글톤)
- contextvars.ContextVar 사용
- get_current_session()으로 접근
- project_context 속성 보유

### ProjectContext (일반 클래스)
- Session에 의해 관리됨
- 프로젝트 경로 관리
- os.chdir 사용하지 않음

### 현재 흐름
1. flow_project_with_workflow() 호출
2. Session.set_project() 호출
3. ProjectContext 생성/업데이트
4. get_current_project()는 Session에서 정보 획득

## ❓ 핵심 질문

1. Session.set_project()가 호출되는데 왜 get_current_project()가 이전 프로젝트를 반환하는가?
2. os.getcwd()와 ProjectContext의 경로가 왜 동기화되지 않는가?
3. Task number 자동 할당을 어디에 구현해야 효율적인가?
4. Flow Repository를 프로젝트별로 완전히 분리하려면 어떻게 해야 하는가?

## 🎯 요청사항
1. 코드 분석을 통한 근본 원인 파악
2. 최소한의 변경으로 모든 문제를 해결하는 방안
3. 기존 아키텍처를 최대한 유지하면서 개선
