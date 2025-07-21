# o3 Task 워크플로우 분석

──────────────────────────────────────────────────
1. 목표 재정의
──────────────────────────────────────────────────
A) FlowManagerUnified 소스는 “상태값 추가” 외에는 건드리지 않는다.  
B) 상태가 바뀌면 AI가 “유저프리퍼런스(UP)”에 명시된 가이드를 찾아 실행한다.  
C) 이후에도 새 상태·새 가이드를 Low-Code 로 추가할 수 있어야 한다.

──────────────────────────────────────────────────
2. 전체 아키텍처
──────────────────────────────────────────────────
          ┌──────────────────────────────────────┐
          │               Client UI              │
          └──────────────────────────────────────┘
                            │ ① 상태변경 요청
                            ▼
┌────────────────────────────────────────────────────────────┐
│                FlowManagerUnified (기존)                  │
│  • TASK_STATES += ['planning','reviewing','approved']      │
│  • update_status(task_id,new_state)                        │
│        └─ emit StateChangedEvent(task,new_state) ─────────►│
└────────────────────────────────────────────────────────────┘
                            │ ② 이벤트
                            ▼
┌────────────────────────────────────────────────────────────┐
│             Event/Message Bus (Redis, NATS 등)            │
└────────────────────────────────────────────────────────────┘
                            │ ③ publish/subscribe
                            ▼
┌────────────────────────────────────────────────────────────┐
│           AI Orchestrator (신규, 독립 프로세스)           │
│  1. 수신한 이벤트를 PreferenceResolver에 전달             │
│  2. 반환된 ai_action 을 SkillRouter로 dispatch            │
└────────────────────────────────────────────────────────────┘
              │ ④ resolve            │ ⑤ call
              ▼                      ▼
┌───────────────────────┐     ┌──────────────────────────────┐
│ PreferenceResolver    │     │ SkillRouter + 개별 Skill     │
│  • 유저/팀/글로벌 UP   │     │  • provide_design_template   │
│  • 계층형 머지/캐시    │     │  • generate_review_report    │
└───────────────────────┘     │  • approval_guide            │
                              └──────────────────────────────┘
              │                      │ ⑥ 실행결과
              ▼                      ▼
             DB / Notification / Comment / Webhook … (결과 반영)

──────────────────────────────────────────────────
3. 핵심 컴포넌트 상세
──────────────────────────────────────────────────
3-1. FlowManagerUnified (변경 최소화)
```
class FlowManagerUnified:
    TASK_STATES = ['todo', 'planning', 'in_progress',
                   'reviewing', 'completed', 'approved']

    def update_status(self, task_id: str, new_state: str):
        assert new_state in self.TASK_STATES
        task = self._get_task(task_id)
        task.state = new_state
        self._save(task)
        EventBus.publish('task.state_changed',  # 단순 pub
                         {'task_id': task_id,
                          'new_state': new_state,
                          'user_id': task.owner})
```

3-2. UP(유저프리퍼런스) 스키마 제안 (YAML/JSON)
```
task_flow_rules:          # 필수 키
  default:                # 글로벌(모든 유저)
    planning:
      ai_action: provide_design_template
      prompt: |
        당신은 **설계컨설턴트**입니다. 현재 업무: {{task.title}}
        [결과] 아키텍처 초안, 일정표, 위험요소를 표로 정리
    reviewing:
      ai_action: generate_review_report
      prompt: >
        당신은 **QA 리더**입니다...
    approved:
      ai_action: approval_guide
      approvers: ["manager_123", "qa_456"]

  user_42:                # 사용자 또는 팀별 override
    reviewing:
      ai_action: generate_marketing_review
      prompt: |
        마케팅 관점에서 리뷰 보고서를 작성...
```
• 해석 규칙  
  1) user-specific → team-specific → default 우선순위  
  2) 속성 미정의 시 상위(precedence) 값 fallback

3-3. PreferenceResolver
```
class PreferenceResolver:
    @lru_cache(maxsize=4096, ttl=300)
    def get_rule(user_id, state):
        # 1. DB or S3에서 YAML 로드 → 파싱
        # 2. precedence 병합
        # 3. return dict(ai_action, prompt, ...)
```

3-4. SkillRouter & Skills
```
class SkillRouter:
    _map = {
        'provide_design_template': DesignTemplateSkill(),
        'generate_review_report':  ReviewReportSkill(),
        'approval_guide':          ApprovalGuideSkill(),
    }

    def dispatch(self, rule, task):
        skill = self._map[rule['ai_action']]
        return skill.execute(rule, task)
```
각 Skill 내부는 LLM 호출, 결과물 저장 위치(코멘트, 첨부파일, 알림)만 담당.

3-5. AI Orchestrator (listener)
```
def on_state_changed(event):
    user_id = event['user_id']; state = event['new_state']
    rule = PreferenceResolver.get_rule(user_id, state)
    if not rule: return       # 해당 상태에 지정된 작업 없으면 무시
    task = TaskRepo.get(event['task_id'])
    SkillRouter.dispatch(rule, task)
EventBus.subscribe('task.state_changed', on_state_changed)
```

3-6. 에러·재시도
• Skill 실패 시 DLQ(Dead-Letter-Queue)로 보내고 Slack alert  
• Idempotent하게 저장(결과 comment 존재 여부 체크)

──────────────────────────────────────────────────
4. 시나리오 예시
──────────────────────────────────────────────────
1) 사용자가 Task A 상태를 planning 으로 변경.  
2) FlowManagerUnified → event publish  
3) AI Orchestrator → UP 조회(설계 템플릿)  
4) DesignTemplateSkill → LLM 호출 → 결과를 Task A 의 comment 로 삽입  
5) UI에는 ‘AI 설계 초안이 추가되었습니다’ 배너 노출  

──────────────────────────────────────────────────
5. 장점
──────────────────────────────────────────────────
• 코드 변경 최소: 상태(enum) 추가 + 5줄 pub.  
• 비즈니스 로직/AI 로직 분리 → 팀별 프롬프트·행동을 실시간 hot-swap.  
• 이벤트드리븐 구조라 확장(추가 상태, 추가 Skill) 용이.  
• 캐싱 하여 성능↑, DLQ 로 안정성↑.  

──────────────────────────────────────────────────
6. 향후 확장 포인트
──────────────────────────────────────────────────
• Visual Preference Editor: YAML 대신 GUI 제공.  
• 다단계 승인 workflow(approved → deployed 등)도 UP에 정의.  
• Rule Engine 도입하여 “조건식(if label == urgent)” 지원.  
• Fine-Tuned GPT vs. Function-Calling 비교해 Skill 최적화.  

──────────────────────────────────────────────────
7. 체크리스트
──────────────────────────────────────────────────
[ ] TASK_STATES 수정 후 테스트 통과  
[ ] EventBus 모듈 선택(NATS/Redis) 및 인프라 배포  
[ ] PreferenceResolver 캐시·만료 설정 검증  
[ ] 기본 Skill 3종(설계, 리뷰, 승인가이드) 완료  
[ ] 문서화 & 예시 YAML 배포  

위 설계대로 구현하면 기존 FlowManagerUnified 를 거의 건드리지 않으면서
사용자 맞춤 ‘AI 자동 Task 가이드’ 가 유연하게 동작합니다.