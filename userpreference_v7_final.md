# AI Coding Brain MCP - 유저 프리퍼런스 v7

## 🎯 execute_code 최적화 가이드

### 🔄 연속 실행 패턴 (Sequential Execution Pattern)
execute_code 사용 시 항상 작은 단위로 나누어 순차적으로 실행하세요:

```
#1 초기 설정 및 데이터 로드
#2 데이터 탐색 및 분석
#3 결과 검증 및 저장
```

각 단계는 다음 원칙을 따릅니다:
- 한 번에 하나의 목적만 수행
- 이전 단계의 변수를 활용
- 결과를 즉시 확인하고 다음 단계 결정

### 📝 코드 작성 템플릿

#### 단계별 실행 템플릿
```python
# #1 초기화 및 설정
print("🔧 #1 초기화 단계")
# 필요한 import
# 기본 변수 설정
# 결과 출력

# #2 데이터 처리
print("\n📊 #2 데이터 처리")
# 이전 변수 활용
# 처리 로직
# 중간 결과 확인

# #3 결과 저장
print("\n💾 #3 결과 저장")
# 최종 처리
# 저장 또는 출력
# 다음 작업 준비
```

## 🆕 /flow와 /a 명령어 역할 분리 (v7 업데이트)

### 📊 /flow 프로젝트 전환 (읽기 전용) ✅

`fp("프로젝트명")` 또는 `helpers.workflow('/flow 프로젝트명')` 실행 시:

#### 현재 구현 동작
```
#1 프로젝트 디렉토리로 전환
#2 기존 분석 파일 확인
   - file_directory.md
   - memory/project_context.json

#3-A 새 프로젝트 또는 파일이 없으면:
   ⚠️ 다음 분석 파일이 없습니다:
   - file_directory.md
   - project_context

   💡 프로젝트 분석을 실행하시겠습니까?
   👉 helpers.workflow('/a') 또는 /a 명령어를 실행하세요

#3-B 기존 프로젝트로 전환 시:
   📂 기존 프로젝트로 전환: 프로젝트명
   (현재는 project_context.json 내용 표시 안 함)
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

### 💡 현재 구현 상태와 개선점

**구현 완료 ✅**
1. 새 프로젝트 또는 분석 파일 없을 때 → /a 실행 제안
2. project_context.json 로드 및 표시 로직 구현
3. 역할 분리: /flow(읽기), /a(분석), 워크플로우(작업관리)

**개선 가능 ⚠️**
1. 기존 프로젝트로 전환 시 project_context.json 자동 표시
   - 현재: "📂 기존 프로젝트로 전환" 메시지만
   - 개선안: 프로젝트 정보도 함께 표시

**권장 사용 패턴**
```python
# 새 프로젝트 시작
fp("my-project")
>>> ⚠️ 분석 파일 없음
helpers.workflow('/a')  # 분석 실행
>>> ✅ 분석 완료

# 프로젝트 정보 확인
cat memory/project_context.json

# 또는 Python으로
with open('memory/project_context.json') as f:
    context = json.load(f)
    print(f"기술 스택: {context['tech_stack']}")
```

### 📋 작업 관리는 워크플로우로

TODO와 작업 관리는 **워크플로우 명령어만** 사용합니다:

```python
# 작업 관리
helpers.workflow("/start 새 기능 개발")
helpers.workflow("/task API 엔드포인트 추가")
helpers.workflow("/status")
helpers.workflow("/complete")
```

### 📌 핵심 원칙

- **구조는 /a로**: 파일 구조, 기술 스택 분석
- **작업은 워크플로우로**: 태스크, 진행상황 관리
- **/flow는 빠르고 가벼움**: 전환과 기본 정보만
- **분석은 선택사항**: 필요할 때만 /a 실행

## 🚀 권장 작업 흐름

### 시작
```python
fp("프로젝트명")
workflow("/start 작업명")
show_history()  # 이전 작업 확인
```

### 수정
```python
# #1 백업
git_commit("backup: 수정 전 백업")

# #2 수정 실행
replace_block("file.py", old_code, new_code)

# #3 검증
if "예상_텍스트" in read_file("file.py"):
    print("✅ 수정 성공")
```

### 완료
```python
git_add(".") 
git_commit("작업 내용")
workflow("/complete 작업 요약")
```

## 📌 피해야 할 패턴

❌ "TODO 항목을 분석해주세요"
✅ "워크플로우 상태를 확인해주세요"

❌ "/a로 TODO 찾아주세요"
✅ "/a로 프로젝트 구조를 분석해주세요"

❌ "모든 파일을 한번에 수정..."
✅ "단계별로 확인받으며 수정..."

## 🎯 최적 사용 패턴을 위한 프롬프트 작성법

### 1. 프로젝트 시작 프롬프트
```
프로젝트: [프로젝트명]
/flow [프로젝트명]으로 전환 후 작업 시작

주요 작업:
1. [작업1]
2. [작업2]

워크플로우로 진행 상황 추적하면서 작업해주세요.
```

### 2. 단계별 실행 프롬프트
```
[작업명]을 단계별로 진행해주세요.

#1 먼저 [대상] 구조를 파악하고
#2 [조건]에 맞는 항목을 찾아서
#3 [작업]을 수행한 후
#4 결과를 [형식]으로 정리해주세요.

각 단계마다 결과를 확인하고 다음 진행 여부를 결정하겠습니다.
```

## 🏗️ 체계적인 개발 프로세스 프롬프트

### 상세설계 요청 프롬프트
```
[작업명]에 대한 상세설계를 먼저 제시해주세요.

설계 포함사항:
1. 현재 상태 분석
2. 변경이 필요한 모듈/함수 목록
3. 각 변경사항의 구체적인 방법
4. 예상되는 영향 범위
5. 작업 순서 및 단계

설계 완료 후 "이대로 진행해도 될까요?" 확인 부탁드립니다.
```

(이하 기존 v6 내용 유지...)
