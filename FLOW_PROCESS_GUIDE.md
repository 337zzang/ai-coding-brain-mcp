# /flow 명령 처리 프로세스 📋

## 🎯 개요
`/flow` 명령은 프로젝트 전환 및 컨텍스트 로드를 담당하는 핵심 명령어입니다.

## 🔄 처리 프로세스

### 1️⃣ **명령 인식 단계**
```
사용자: /flow [프로젝트명]
    ↓
Claude: MCP 도구 'flow_project' 호출
```

### 2️⃣ **MCP 도구 실행**
- **도구명**: `flow_project`
- **정의 위치**: `src/tools/tool-definitions.ts`
- **파라미터**: 
  - `project_name` (필수): 전환할 프로젝트 이름

### 3️⃣ **TypeScript 핸들러 처리**
- **핸들러**: `handleFlowProject` 
- **위치**: `src/handlers/workflow-handlers.ts`
- **주요 작업**:
  1. 프로젝트 경로 확인 및 검증
  2. 작업 디렉토리 변경 (`process.chdir`)
  3. Python 스크립트 실행 준비
  4. `enhanced_flow.py` 호출

### 4️⃣ **Python 스크립트 실행**
- **스크립트**: `python/commands/enhanced_flow.py`
- **실행 과정**:

```python
flow_project(project_name):
    1. 프로젝트 초기화
       - 작업 디렉토리 변경
       - .ai-brain.config.json 로드
    
    2. 캐시/컨텍스트 로드
       - memory/cache/[프로젝트명]_context.json
       - 기존 작업 상태 복원
    
    3. 파일 구조 스캔
       - 전체 프로젝트 구조 분석
       - 변경사항 감지
    
    4. file_directory.md 생성/업데이트
       - 프로젝트 구조 문서화
       - 24시간 캐시 활용
    
    5. Wisdom 시스템 활성화
       - project_wisdom.md 로드
       - 실수 패턴 추적 시작
    
    6. 프로젝트 상태 브리핑
       - 현재 Phase/Task 정보
       - 작업 진행률
       - 최근 변경사항
```

### 5️⃣ **결과 반환**
```json
{
  "success": true,
  "language": "python",
  "session_mode": "JSON_REPL",
  "stdout": "프로젝트 브리핑 내용...",
  "variable_count": 36
}
```

## 📊 시퀀스 다이어그램

```
사용자 → Claude → MCP Tool → TypeScript Handler → Python Script
                      ↓               ↓                    ↓
                flow_project   handleFlowProject    enhanced_flow.py
                      ↓               ↓                    ↓
                   호출 요청      디렉토리 변경         컨텍스트 로드
                                      ↓                    ↓
                                Python 실행           파일 구조 스캔
                                      ↓                    ↓
                                  결과 수집          file_directory.md
                                      ↓                    ↓
                                  반환 처리           Wisdom 활성화
                                      ↓                    ↓
                                      ←              브리핑 생성
                                      ↓
                                   Claude로 반환
```

## 🚀 주요 기능

### 자동 생성/업데이트 파일
1. **file_directory.md** - 프로젝트 구조 문서
2. **project_wisdom.md** - 프로젝트 지혜 문서
3. **캐시 파일** - memory/cache/[프로젝트명]_context.json

### 자동 로드 시스템
- **컨텍스트**: 이전 작업 상태
- **Wisdom**: 실수 패턴 및 교훈
- **작업 목록**: Phase/Task 정보
- **파일 추적**: 최근 수정 파일

## 🔧 최적화 기능

### 캐싱 시스템
- file_directory.md: 24시간 캐시
- 프로젝트 구조: 메모리 캐시
- AST 파싱 결과: 자동 캐시

### 성능 향상
- 대규모 프로젝트 스캔 시간 90% 단축
- 중복 스캔 방지
- 점진적 업데이트

## ⚠️ 주의사항

1. **프로젝트 이름**
   - 정확한 디렉토리명 사용
   - 대소문자 구분
   - 공백은 하이픈으로 대체

2. **작업 디렉토리**
   - 부모 디렉토리에서 실행
   - 프로젝트 폴더가 존재해야 함

3. **캐시 관리**
   - 구조 변경 시 강제 재스캔 가능
   - 캐시 파일 손상 시 자동 재생성

## 💡 사용 예시

```bash
# 기본 사용
/flow my-project

# 컨텍스트 포함 (flow_with_context)
/flow my-project  # 자동으로 wisdom 로드

# 프로젝트 목록 확인 (별도 명령 필요)
/projects
```

## 🔄 v25.0 업데이트 사항
- flow 관련 함수가 MCP 도구로 완전 이전
- execute_code 내에서 직접 호출 금지
- Wisdom 시스템 자동 활성화
- Git 상태 자동 확인
