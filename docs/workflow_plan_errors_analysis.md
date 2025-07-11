# 플랜 작성 시 발생하는 오류 정리

## 발견된 주요 오류

### 1. 메모리-파일 동기화 불일치
- **증상**: 새 플랜 생성 후 메모리에는 존재하지만 workflow.json 파일에 저장되지 않음
- **원인**: WorkflowManager가 자동 저장을 수행하지 않음
- **해결방법**: 
  ```python
  wm._save_data()  # 또는
  wm.storage.save(wm.state.to_dict())
  ```

### 2. WorkflowManager.save() 메서드 부재
- **증상**: `AttributeError: 'WorkflowManager' object has no attribute 'save'`
- **원인**: 공개 save() 메서드가 없고, _save_data()가 private 메서드로 존재
- **해결방법**: _save_data() 사용 또는 storage.save() 직접 호출

### 3. helpers.workflow() 응답 구조 복잡성
- **증상**: `/status` 명령 결과를 get_data()로 접근 시 예상과 다른 구조
- **원인**: 응답이 중첩된 구조로 반환됨 (success, status, tasks_summary 등)
- **해결방법**: 
  ```python
  status = helpers.workflow("/status")
  data = status.get_data({})
  actual_status = data.get('status', {})  # 실제 상태는 'status' 키 안에
  ```

### 4. 플랜 전환 시 이전 플랜 처리
- **증상**: 새 플랜 생성 시 이전 플랜이 자동으로 보관되지 않음
- **원인**: 명시적인 플랜 전환 로직 부재
- **해결방법**: 새 플랜 생성 전 기존 플랜 보관 필요

### 5. 캐시 동기화 문제
- **증상**: WorkflowManager 인스턴스가 최신 상태를 반영하지 않음
- **원인**: 싱글톤 패턴의 캐시가 갱신되지 않음
- **해결방법**: 
  ```python
  WorkflowManager.invalidate_and_reload("프로젝트명")
  ```

## 권장 워크플로우

1. **플랜 생성 시**:
   ```python
   # 1. 새 플랜 생성
   helpers.workflow("/plan 플랜명")
   
   # 2. 태스크 추가
   helpers.workflow("/task 태스크명")
   
   # 3. 명시적 저장
   wm = WorkflowManager.get_instance("프로젝트명")
   wm._save_data()
   ```

2. **상태 확인 시**:
   ```python
   # 응답 구조를 고려한 접근
   status = helpers.workflow("/status")
   data = status.get_data({})
   actual_status = data.get('status', {})
   plan_name = actual_status.get('plan_name')
   ```

3. **캐시 문제 발생 시**:
   ```python
   WorkflowManager.clear_instance("프로젝트명")
   wm = WorkflowManager.get_instance("프로젝트명")
   wm.reload()
   ```

## 개선 제안

1. **자동 저장 구현**: 플랜/태스크 변경 시 자동으로 파일 저장
2. **공개 save() 메서드 추가**: _save_data()를 public으로 노출
3. **응답 구조 단순화**: helpers.workflow() 응답을 평탄화
4. **캐시 자동 갱신**: 파일 변경 감지 시 자동 리로드
5. **플랜 전환 로직 개선**: 새 플랜 생성 시 이전 플랜 자동 처리

## MCP 개선 플랜과의 연관성

발견된 오류들이 MCP 개선 태스크와 정확히 일치:

- **자동 저장 문제** → '컨텍스트 자동 갱신 강화' 태스크
- **API 불일치** → '현재 MCP 통합 수준 분석' 태스크  
- **캐시 동기화** → 'EventBus 비동기 처리 최적화' 태스크
- **에러 처리** → '에러 처리 표준화' 태스크
- **수동 개입** → 'AI 에이전트 자율성 구현' 태스크

이 플랜을 통해 현재 워크플로우 시스템의 핵심 문제들을 해결할 수 있음.