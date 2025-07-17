
## 🆕 /flow와 /a 명령어 역할 분리 (v7 업데이트)

### 📊 /flow 프로젝트 전환 (읽기 전용) ✅

`fp("프로젝트명")` 또는 `helpers.workflow('/flow 프로젝트명')` 실행 시:

#### 현재 구현 동작
```python
#1 프로젝트 디렉토리로 전환
#2 기존 분석 파일 확인
   - file_directory.md
   - memory/project_context.json
   - README.md

#3-A 파일이 있으면:
   📊 프로젝트 컨텍스트 정보:
   - 분석일시: 2025-01-17 10:47:42
   - 프로젝트 타입: typescript
   - 기술 스택: TypeScript, Node.js
   - 전체 파일: 559개
   - 소스 파일: 124개
   - 테스트 파일: 53개

#3-B 파일이 없으면:
   ⚠️ 다음 분석 파일이 없습니다:
   - file_directory.md
   - project_context

   💡 프로젝트 분석을 실행하시겠습니까?
   👉 helpers.workflow('/a') 또는 /a 명령어를 실행하세요
```

### 🔍 /a 프로젝트 분석 (구조만) ✅

`helpers.workflow('/a')` 실행 시:

#### 생성하는 파일들
1. **file_directory.md** - 프로젝트 구조 트리
2. **memory/project_context.json** - 프로젝트 메타데이터
3. **README.md** - 없는 경우만 템플릿 생성

#### project_context.json 구조
```json
{
  "analyzed_at": "2025-01-17 10:47:42",
  "project_type": "typescript",
  "tech_stack": ["TypeScript", "Node.js"],
  "structure": {
    "total_files": 559,
    "source_files": 124,
    "test_files": 53,
    "directories": ["src", "tests", "docs", "python"]
  },
  "entry_points": ["src/index.ts"],
  "dependencies_count": 24,
  "build_tools": ["npm", "tsc"]
}
```

### 💡 핵심 개선사항 (v7)

1. **자동 표시 개선**
   - fp() 실행 시 project_context.json 내용을 자동으로 읽고 표시
   - 기술 스택, 파일 수 등 주요 정보를 한눈에 확인

2. **명확한 가이드**
   - 분석 파일이 없을 때 구체적인 안내 메시지
   - /a 명령어로 무엇을 할 수 있는지 명시

3. **역할 분리 유지**
   - /flow: 전환과 정보 표시만 (읽기 전용)
   - /a: 분석 파일 생성 (쓰기 작업)
   - 워크플로우: TODO와 작업 관리

### 📌 사용 예시

```python
# 새 프로젝트로 전환
fp("my-new-project")
>>> ⚠️ 분석 파일이 없습니다
>>> 💡 helpers.workflow('/a') 실행하세요

# 분석 실행
helpers.workflow('/a')
>>> ✅ file_directory.md 생성
>>> ✅ project_context.json 생성

# 다시 전환
fp("my-new-project")
>>> 📊 프로젝트 컨텍스트 정보:
>>> - 프로젝트 타입: python
>>> - 기술 스택: Python, FastAPI
>>> - 전체 파일: 45개
```
