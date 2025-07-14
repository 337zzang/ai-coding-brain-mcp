# AI Coding Brain MCP - 실용 가이드 v2.0

## 🎯 핵심 원칙
1. **execute_code 중심** - 대부분의 작업을 직접 처리
2. **세션 활용** - 변수 유지로 복잡한 작업 가능
3. **실용적 접근** - 동작하는 코드 우선

## 💻 execute_code 사용법

### 기본 패턴
```python
# 상태 확인 후 작업
if 'data' not in globals():
    data = load_data()  # 첫 실행
else:
    process(data)       # 이어서 작업

# 진행 상황 추적
if 'progress' not in globals():
    progress = {'step': 1, 'total': 5}
progress['step'] += 1
print(f"진행률: {progress['step']}/{progress['total']}")
```

### 실용 예시
1. **대용량 파일 처리**
   - 단계별로 나눠서 실행
   - 중간 결과 변수에 저장
   - 실패시 해당 단계만 재실행

2. **프로젝트 파일 관리**
   - helpers 함수로 파일 작업
   - 일괄 처리와 진행률 표시

## 🛠️ MCP 도구 우선순위
1. `execute_code` - 항상 우선
2. `project_knowledge_search` - GitHub 코드/문서 검색
3. 기타 도구 - 필요한 경우만
   - `desktop-commander` - 시스템 명령
   - `web_search` - 최신 정보
   - `perplexity` - 기술 문서

## 📋 작업 흐름
```
1. flow_project로 현황 파악
2. execute_code로 작업 수행
3. 결과 확인 및 다음 단계
4. 필요시 간단한 문서화
```

## ⚠️ 주의사항
- execute_code는 실시간이 아님 (완료 후 결과)
- 에러 처리 필수 (try-except)
- 긴 작업은 단계별로 분할
- 중요 결과는 파일로도 저장

## 📌 helpers 함수 사용법
```python
# 올바른 사용법
result = helpers.read_file("file.txt")
content = result['content']  # ✅

# 잘못된 사용법
content = result  # ❌ HelperResult 객체
```

---
간단하고 실용적으로 작업하세요.
필요할 때 도구를 사용하고, 
복잡한 것은 단순하게 나누세요.
