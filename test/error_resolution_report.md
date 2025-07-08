
## 🔍 오류 발생 및 해결 과정 정리

### 1. 데이터 구조 관련 오류

#### 1.1 KeyError: 'total'
- **발생 위치**: tasks 데이터 접근 시
- **원인**: tasks.data['total'] 키가 존재하지 않음
- **해결**: 
  - 실제 데이터 구조 확인: tasks.data.keys()
  - 올바른 키 사용: tasks.data['total_tasks']

#### 1.2 KeyError: 'plan'
- **발생 위치**: status.data['plan'] 접근 시
- **원인**: 중첩된 구조를 고려하지 않음
- **해결**: status.data['status']['plan'] 사용

#### 1.3 KeyError: 'task'
- **발생 위치**: current.data['task'] 접근 시
- **원인**: 실제 키는 'current_task'
- **해결**: current.data['current_task'] 사용

### 2. 타입 관련 오류

#### 2.1 TypeError: Object of type TaskStatus is not JSON serializable
- **발생 위치**: json.dumps(tasks.data)
- **원인**: TaskStatus enum 타입이 JSON으로 직렬화 불가
- **해결**: 
  - JSON 직렬화 대신 직접 출력
  - str(task['status']).replace('TaskStatus.', '')

#### 2.2 AttributeError: 'str' object has no attribute 'get'
- **발생 위치**: task 객체 접근 시
- **원인**: task가 dict가 아닌 str 타입
- **해결**: isinstance(task, dict) 체크 후 처리

### 3. 메서드 관련 오류

#### 3.1 AttributeError: 'module' has no attribute 'get_timestamp'
- **발생 위치**: helpers.get_timestamp()
- **원인**: 존재하지 않는 메서드 호출
- **해결**: datetime.now().strftime() 직접 사용

#### 3.2 AttributeError: 'module' has no attribute 'create_directory'
- **발생 위치**: helpers.create_directory("test")
- **원인**: 메서드명 오류
- **해결**: 
  - dir(helpers)로 확인
  - os.makedirs() 직접 사용

#### 3.3 AttributeError: 'HelperResult' object has no attribute 'get'
- **발생 위치**: scan_result.get('directories')
- **원인**: HelperResult 객체를 dict처럼 사용
- **해결**: scan_result.data.get('directories')

### 4. 워크플로우 명령어 오류

#### 4.1 형식 오류: /plan 계획이름 | 설명 [--reset]
- **발생 위치**: /plan 명령어 사용 시
- **원인**: 잘못된 구분자 사용 (공백 대신 파이프)
- **해결**: /plan workflow-context-test | 설명

#### 4.2 플랜 생성 실패 (이미 활성 플랜 존재)
- **발생 위치**: 새 플랜 생성 시도
- **원인**: 기존 활성 플랜이 있음
- **해결**: 
  - 기존 플랜 자동 아카이브
  - --reset 옵션은 작동하지 않음

### 5. 파일 시스템 오류

#### 5.1 디렉토리 생성 문제
- **발생 위치**: test 디렉토리 생성
- **원인**: helpers에 create_directory 메서드 없음
- **해결**: os.makedirs("test", exist_ok=True)

### 6. 데이터 접근 패턴 오류

#### 6.1 current_task 속성 접근
- **문제**: task.id, task.description 등 직접 접근 시도
- **원인**: dict 객체의 속성처럼 접근
- **해결**: task.get('id'), task.get('description')

### 7. Git 관련 이슈

#### 7.1 Task ID 연동 미작동
- **문제**: 파일 작업 시 task_id가 None으로 기록
- **원인**: 현재 task의 ID가 제공되지 않음
- **해결**: task 식별자를 인덱스 기반으로 생성

## 📊 오류 통계
- 총 오류 발생: 약 15회
- KeyError: 3회
- AttributeError: 7회
- TypeError: 2회
- 워크플로우 명령어: 2회
- 기타: 1회

## 🛠️ 주요 해결 패턴

1. **데이터 구조 확인 우선**
   ```python
   print(f"keys: {list(data.keys())}")
   print(f"type: {type(data)}")
   ```

2. **안전한 접근 패턴**
   ```python
   value = data.get('key', 'default')
   if isinstance(data, dict):
       # dict 처리
   ```

3. **HelperResult 올바른 사용**
   ```python
   if result.ok:
       data = result.data
   ```

4. **메서드 존재 확인**
   ```python
   methods = [m for m in dir(helpers) if 'keyword' in m]
   ```

5. **예외 처리 추가**
   ```python
   try:
       # 작업 수행
   except KeyError as e:
       print(f"키 오류: {e}")
   ```
