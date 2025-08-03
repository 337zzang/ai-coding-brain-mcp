
# 🔍 AI Coding Brain MCP 오류 분류 분석

## 1️⃣ 코드 오류 (실제 버그)

### 🔴 Critical: 내부 참조 오류
**문제**: `NameError: name 'h' is not defined`
- **위치**: 
  - `write_json()` in file.py
  - `quick_o3_context()` in llm.py
- **원인**: 모듈 내부에서 `import ai_helpers_new as h` 시도
- **영향**: 해당 함수 완전 사용 불가
- **수정 방안**:
  ```python
  # ❌ 현재 (오류)
  def write_json(path, data):
      json_str = h.prepare_json(data)  # 'h'가 정의되지 않음

  # ✅ 수정안
  from . import prepare_json  # 또는
  from .utils import prepare_json
  ```

### 🟡 Medium: 반환 타입 불일치
**문제**: `view()` 함수가 dict 대신 다른 타입 반환
- **증상**: `AttributeError: 'str' object has no attribute 'get'`
- **영향**: 문서화된 사용법으로 사용 불가
- **수정 방안**: 
  - 반환 타입을 표준 응답 형식으로 통일
  - 또는 문서를 실제 동작에 맞게 수정

### 🟢 Low: API 일관성 부족
**문제**: FlowAPI가 표준 응답 형식 미준수
- **현재**: `{'id': '...', 'name': '...'}` (ok 키 없음)
- **기대**: `{'ok': True, 'data': {...}}`
- **영향**: 사용 가능하나 일관성 부족

## 2️⃣ 유저프리퍼런스 지침 오류 (문서 업데이트 필요)

### 📝 명시되지 않은 동작
1. **FlowAPI 반환 형식**
   - 지침에 ok 키가 없다는 것이 명시되지 않음
   - 실제로는 데이터를 직접 반환

2. **os.chdir 경고 부족**
   - 지침: "주의 필요" 정도로만 언급
   - 실제: 작업 디렉토리가 실제로 변경되어 영향 큼

3. **view() 함수 사용법**
   - 지침의 예제 코드가 실제와 불일치

## 3️⃣ 정상 작동 항목 (지침과 일치)

✅ **완벽 작동**:
- 프로젝트 전환 및 경로 관리
- Git 작업 (status, branch, log 등)
- TaskLogger 모든 기능
- AST 검증 패턴
- execute_code 분할 실행
- 파일 읽기/쓰기 (JSON 제외)
- Manager API

## 📊 요약

| 분류 | 개수 | 심각도 |
|------|------|--------|
| 코드 오류 (버그) | 3개 | 🔴 1개, 🟡 1개, 🟢 1개 |
| 지침 오류 (문서) | 3개 | 모두 🟡 (중간) |
| 정상 작동 | 7개 | - |

## 🎯 우선순위

### P0 (즉시 수정)
1. `write_json()`, `quick_o3_context()`의 NameError
2. `view()` 반환 타입 수정

### P1 (문서 업데이트)
1. FlowAPI 반환 형식 명시
2. os.chdir 경고 강화
3. view() 사용법 예제 수정

### P2 (개선사항)
1. 모든 API 표준 응답 형식 통일
2. 타입 힌트 추가
