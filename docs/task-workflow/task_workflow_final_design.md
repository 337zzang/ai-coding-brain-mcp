
# 🎯 최종 설계: 유저프리퍼런스 기반 Task 워크플로우

## 📌 설계 원칙
1. **코드 변경 최소화**: FlowManagerUnified에는 상태값만 추가
2. **유저프리퍼런스 중심**: AI의 행동 가이드를 유저프리퍼런스에 정의
3. **유연한 확장**: 코드 수정 없이 워크플로우 변경 가능

## 🔧 구현 계획

### 1️⃣ FlowManagerUnified 코드 변경 (최소)

```python
# flow_manager_unified.py 수정 사항

# 1. Task 상태 확장
TASK_STATES = ['todo', 'planning', 'in_progress', 'reviewing', 'completed', 'approved', 'skipped', 'error']

# 2. _start_task 메서드 수정
def _start_task(self, args: str) -> Dict[str, Any]:
    task_id = args.strip()
    # 상태를 'planning'으로 변경 (기존: 바로 in_progress)
    self.update_task_status(task_id, 'planning')
    return {'ok': True, 'data': f'Task {task_id} 설계 단계로 진입'}

# 3. _complete_task 메서드 수정  
def _complete_task(self, args: str) -> Dict[str, Any]:
    task_id = args.strip()
    # 상태를 'reviewing'으로 변경 (기존: 바로 completed)
    self.update_task_status(task_id, 'reviewing')
    return {'ok': True, 'data': f'Task {task_id} 검토 단계로 진입'}
```

### 2️⃣ 유저프리퍼런스 추가 내용

```markdown
## 🤖 Task 워크플로우 AI 가이드

### Task 상태 감지 및 자동 행동

AI는 Task 상태를 감지하고 다음과 같이 행동합니다:

#### 📐 planning 상태 감지 시
1. 설계 템플릿 자동 제시
2. 사용자에게 설계 작성 요청
3. 설계 완료 확인 후 승인 요청
4. 승인 시 상태를 'in_progress'로 변경

#### 🔄 in_progress 상태에서
1. 작업 진행 시 자동으로 add_task_action 호출
2. 중요 결정 시 승인 요청
3. 진행률 자동 업데이트

#### 🔍 reviewing 상태 감지 시
1. context 정보 기반 보고서 자동 생성
2. 보고서 검토 요청
3. 승인 시 상태를 'completed'로 변경

#### ✅ 승인 포인트
- planning → in_progress: "설계를 검토해주세요 ✔️"
- reviewing → completed: "결과를 승인하시겠습니까? ✔️"
```

### 3️⃣ AI 행동 플로우

```
사용자: /start task_123
  ↓
시스템: 상태 → planning
  ↓
AI: [유저프리퍼런스 확인] planning 상태 감지
  ↓
AI: 설계 템플릿 제시 + "설계를 작성해주세요"
  ↓
사용자: 설계 작성
  ↓
AI: "이 설계대로 진행하시겠습니까? ✔️"
  ↓
사용자: 승인
  ↓
AI: update_task_status('in_progress') + context.plan 저장
  ↓
[작업 진행]
  ↓
사용자: /complete task_123
  ↓
시스템: 상태 → reviewing
  ↓
AI: [유저프리퍼런스 확인] reviewing 상태 감지
  ↓
AI: 보고서 자동 생성 + "결과를 승인하시겠습니까? ✔️"
  ↓
사용자: 승인
  ↓
AI: update_task_status('completed') + context.report 저장
```

## 🎯 핵심 장점

1. **최소 코드 변경**
   - 상태값 추가와 2개 메서드만 수정
   - 복잡한 로직은 모두 AI가 처리

2. **유연한 워크플로우**
   - 유저프리퍼런스 수정으로 즉시 변경 가능
   - 코드 재배포 불필요

3. **AI 활용 극대화**
   - AI가 상태를 보고 적절한 행동
   - 템플릿, 가이드, 보고서 자동 생성

4. **사용자 경험 개선**
   - 명확한 가이드와 승인 절차
   - 체계적인 작업 관리

## 📋 구현 우선순위

1. **즉시**: FlowManagerUnified에 상태값 추가
2. **단기**: _start_task, _complete_task 메서드 수정
3. **중기**: 유저프리퍼런스에 AI 가이드 추가
4. **장기**: 전체 워크플로우 최적화
