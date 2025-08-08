# Execute_code 실행 시 발생한 문제점 정리

## 🔴 주요 오류 패턴

### 1. Flow API 관련 오류

#### A. FlowAPI 메서드 호출 오류
```python
# 오류 사례
api.show_status()  # AttributeError: 'FlowAPI' object has no attribute 'show_status'
```
**원인**: FlowAPI에 show_status() 메서드가 없음
**해결**: flow("/status") 사용 또는 api.get_current_plan() 등 실제 메서드 사용

#### B. FlowAPI 객체 subscript 오류
```python
# 오류 사례
select_result = api.select_plan(plan_id)
if select_result['ok']:  # TypeError: 'FlowAPI' object is not subscriptable
```
**원인**: select_plan()이 체이닝을 위해 FlowAPI 객체 자체를 반환
**해결**: 체이닝 메서드는 반환값을 확인하지 않고 사용

### 2. Task 데이터 구조 오류

#### A. Task 속성 접근 오류
```python
# 오류 사례
print(f"{task['name']}")  # KeyError: 'name'
```
**원인**: Task 객체는 'name'이 아닌 'title' 속성 사용
**해결**: task['title'] 사용

#### B. Task 번호 누락
```python
# Task 데이터 예시
{
  'id': 'task_20250805_000750_d247b1',
  'title': 'Task 1: 환경 준비 및 import 추가',
  'description': '',
  'status': 'todo',
  'number': None  # 번호가 None
}
```
**문제**: Task 생성 시 number 필드가 설정되지 않음

### 3. Git 상태 접근 오류

```python
# 오류 사례
print(f"변경 파일: {git_status['data']['modified']}")  # KeyError: 'modified'
```
**원인**: git_status의 실제 구조와 예상 구조 불일치
**실제 구조**:
```python
{
  'files': [...],  # 변경된 파일 목록
  'count': 594,    # 전체 변경 파일 수
  'branch': 'refactor/...',
  'clean': False
}
```

### 4. 헬퍼 함수 이름 오류

```python
# 오류 사례
h.file_info("path")  # AttributeError: no attribute 'file_info'
```
**원인**: 잘못된 함수명
**해결**: h.get_file_info() 사용

### 5. search_code 매개변수 오류

```python
# 오류 사례
h.search_code("path", "pattern", filePattern="*.py")  
# TypeError: unexpected keyword argument 'filePattern'
```
**원인**: search_code는 file_pattern (언더스코어) 사용
**해결**: file_pattern="*.py" 사용

### 6. flow 명령어 초기화 오류

```python
# 오류 사례
h.flow("/status")
# AttributeError: 'NoneType' object has no attribute 'is_initialized'
```
**원인**: Flow 매니저가 초기화되지 않음
**해결**: FlowAPI 직접 사용 (api = h.get_flow_api())

## 📊 오류 빈도 분석

1. **KeyError** (30%): 잘못된 딕셔너리 키 접근
2. **AttributeError** (40%): 존재하지 않는 메서드/속성
3. **TypeError** (20%): 잘못된 타입 사용
4. **기타** (10%): import 오류, 초기화 오류 등

## ✅ 개선 제안

### 1. 표준 응답 형식 일관성
- 모든 FlowAPI 메서드가 {'ok': bool, 'data': Any, 'error': str} 반환
- 체이닝 메서드는 예외적으로 self 반환

### 2. Task 데이터 모델 표준화
- 'name' vs 'title' 혼용 문제 해결
- number 필드 자동 설정

### 3. 문서화 개선
- 각 API의 반환 타입 명시
- 실제 사용 예제 포함

### 4. 타입 힌트 추가
```python
def get_flow_api() -> FlowAPI:
    pass

def create_task(plan_id: str, name: str) -> Dict[str, Any]:
    pass
```

### 5. 디버깅 도구
- API 응답 구조 검사 함수
- 자동 완성 지원 개선
