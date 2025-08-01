
# AI Coding Brain MCP - 최종 리팩토링 계획 (O3 조언)

## 질문 시각
2025-07-18 22:07:18

## 유저 프리퍼런스 프로세스

## 유저 프리퍼런스의 핵심 작업 프로세스

### 1. 상세 작업 계획 수립 (최우선)
- 모든 작업 시작 전 상세 계획 제시
- 현재 상태 분석 → 수정 계획 → 테스트 계획 → 위험 요소
- 사용자 승인 필수: "이 계획대로 진행해도 될까요?"

### 2. 단계별 승인 프로세스
- 작업 계획 후 승인 대기
- 중요 변경 전 승인 대기
- 파괴적 작업 전 경고와 승인
- 각 단계 완료 후 다음 진행 확인

### 3. 백업-수정-검증-정리 프로세스
- 백업 생성 (필수)
- 코드 수정
- 자동 검증
- 성공 시 백업 삭제, 실패 시 롤백

### 4. 작업 단위 관리
- #0 작업 분석 및 계획
- #1, #2, #3 단계별 분할 실행
- 각 단계 결과 확인 후 확장

### 5. o3 활용 프로세스
- 복잡한 문제 발생 시 o3 질문
- 구체적 컨텍스트 제공
- 답변 검토 후 단계적 적용

### 6. 완료 후 리포트
- 변경된 모듈/함수 목록
- Git 커밋 내역
- 다음 추천 단계


## 현재 상태

## 현재 워크플로우 시스템 상태

### 구현된 명령어
- /a (프로젝트 분석) - 구현됨
- /start, /plan, /task, /next, /status, /focus, /complete - 미구현

### 파일 구조 문제
- workflow_helper.py 중복 (2개)
- 명령어가 workflow_extension.py에 분산
- improved_manager.py 비대 (26.9 KB)
- messaging 등 불필요한 복잡성

### 실제 사용 패턴
- Claude는 helpers 메서드 직접 호출
- 워크플로우 명령어는 거의 사용 안 함
- Git 커밋으로 작업 추적
- execute_code로 대부분 처리


## O3의 답변
#0 작업 분석 및 계획 – “워크플로우 모듈 대수술 ‑ 유지 vs 제거”  

────────────────────────────────────────  
1. 현재 상태 진단  
   • 워크플로우 명령어 대부분 미사용(`/a`만 간헐적 사용).  
   • 중복 파일·비대한 모듈로 복잡성↑, 유지보수 비용↑.  
   • 실제 업무 흐름은 “execute_code + Git 커밋”으로 충분히 돌아감.  

2. 대안 시나리오  
   A. 완전 제거: Git + 단순 로그(YAML/JSON)만 남기기.  
   B. 초소형화: 1-파일(또는 2-파일)짜리 ‘WorkflowSession’ 유틸을 두고  
      ‑ 계획 작성/승인 요청  
      ‑ 백업·롤백 트리거  
      ‑ 단계 상태 기록·최종 리포트 … 정도만 담당.  

3. 권장 방안 – B(초소형화)  
   이유  
   • 유저 프리퍼런스 6-단계 프로세스를 “자동 프롬프트 + 상태 저장”으로 매끄럽게 지원.  
   • Git 만으로는 “승인 대기” → “롤백점 관리” → “최종 리포트 자동 생성”이 번거로움.  
   • 코드베이스를 50-60% 이상 줄이면서 기존 로그/승인 UX 유지 가능.  

4. 목표 범위(필수 기능만)  
   1) plan()      : 상세 작업 계획 기록 및 출력  
   2) request_ok(): 사용자 승인 필요 단계에서 호출(Yes/No)  
   3) checkpoint(): 자동 Git commit (백업) + 해시 기억  
   4) rollback()  : 마지막 checkpoint로 되돌림  
   5) log_step()  : 단계 결과/메트릭 저장  
   6) finish()    : 변경 목록·커밋 해시·요약 리포트 출력  

5. 예상 파일 구조 (총 2 파일, 300~400 LoC)  
   workflow.py          ← WorkflowSession 클래스 + 함수형 래퍼  
   git_utils.py          ← checkpoint/rollback 도우미  
   (★ 기존 improved_manager.py, workflow_helper.py, workflow_extension.py → 삭제)  

6. 구현/리팩토링 단계 (#1 ~ #3)  
   #1 모듈 생성   : workflow.py, git_utils.py 스캐폴딩 + 테스트 스텁  
   #2 핵심 로직   : plan, request_ok, checkpoint, rollback, log_step, finish  
   #3 마이그레이션:  
       ‑ 기존 코드에서 호출되는 helper → 새로운 API로 교체  
       ‑ 불필요 모듈/파일 제거, __init__.py 정리  
       ‑ 단위테스트 6 케이스 작성(Git mock 포함)  

7. 테스트 전략  
   • pytest + tmp git repo fixture로 checkpoint/rollback 검증  
   • happy-path / 승인 거부 / 롤백 Trigger / finish 리포트 4 시나리오  

8. 위험 요소 & 완화책  
   • Git 명령 실패 → 모의 repo 테스트 + 예외 wrap  
   • 기존 코드가 삭제된 API 호출 → grep 전수 검색 후 자동 대체 스크립트  
   • 사용자 프롬프트 차단(비동기) → 입출력 캡처 테스트  

9. 예상 효과  
   • 워크플로우 관련 코드 1.2 만 → 400 LoC 이하 (-90% 이상)  
   • 의존성 0 (내장 subprocess만)  
   • 유저 프리퍼런스 6-단계 절차를 한눈에 보여주는 단일-객체 제공  

────────────────────────────────────────  
질문 1 – 워크플로우가 정말 필요한가?  
→ “로깅·승인·롤백”을 조금이라도 자동화하고 싶다면 ‘필요’.  
   단, 현재 구조는 과투자 → ‘초소형화’가 현실적.  

질문 2 – 유저 프로세스와의 통합?  
   ① plan() 호출 시 자동으로 “이 계획대로 진행해도 될까요?” 프롬프트 출력.  
   ② request_ok()는 모든 “중요 변경 전/파괴적 작업 전” 구간에서 사용.  
   ③ checkpoint()는 “백업-수정-검증” 루프에서 백업 단계에 자동 실행.  
   ④ finish()가 6-단계 보고서(변경 목록, 커밋 로그, 다음 TODO) 생성.  

질문 3 – 대안?  
   • Git + README 로그(수동)만으로도 가능하지만 승인/롤백 UX 손실.  
   • json_repl_session.py 내장보다 독립 2-파일 유지가 가독성·재사용에 낫다.  

질문 4 – AI Coding Brain 목적에 맞는 최적 구조?  
   → “코딩 대화”가 본질, 워크플로우는 ‘얇은 감시 & 자동화 도우미’ 역할이면 족함.  
      • 실행코드/테스트는 그대로 유지  
      • 워크플로우는 ①계획 ②승인 ③백업/롤백 ④리포트 4 기능만 담당.  

────────────────────────────────────────  
다음 단계(#1) 작업 요청
1) workflow.py, git_utils.py 기본 골격 생성  
2) plan(), request_ok() 로직 작성 + 최소 테스트

이 계획대로 진행해도 될까요? “네 / 아니오”로 답변해 주세요.

## 메타 정보
- 추론 시간: 56.48초
- 사용 토큰: 2955
