# 통합 워크플로우 프로토콜 사용 가이드

## 개요
AI Helpers v2가 완전히 통합된 워크플로우 프로토콜입니다.
생성일: 2025-07-15 07:24:51

## 구성
- **통합 모듈**: `python/integrated_workflow_protocol.py`
- **세션 래퍼**: `python/workflow_session.py`
- **AI Helpers v2**: `python/ai_helpers_v2/`

## 사용법

### 1. REPL 세션에서 사용
```python
# 세션 래퍼 실행
exec(open('python/workflow_session.py').read())

# 프로젝트 전환
flow_project('my-project')

# 워크플로우 실행
run_workflow()  # 각 단계별로 실행
```

### 2. 직접 임포트
```python
import sys
sys.path.insert(0, 'python')
from integrated_workflow_protocol import flow_project, run_workflow

# 사용
flow_project('my-project')
run_workflow()
```

### 3. execute_code에서 사용
```python
exec(open('python/workflow_session.py').read())
flow_project('ai-coding-brain-mcp')
run_workflow()
```

## 주요 기능

### 프로젝트 관리
- `flow_project(name)`: 프로젝트 전환 및 구조 생성
- 자동 백업 및 컨텍스트 관리
- file_directory.md 자동 생성

### 워크플로우 상태
1. **initialized**: 프로젝트 분석
2. **planning**: 작업 계획 수립
3. **executing**: 작업 실행
4. **testing**: 테스트 분석
5. **documenting**: 문서 생성
6. **completed**: 완료
7. **error**: 오류 처리

### AI Helpers v2 통합
- 모든 파일 작업
- 코드 검색 및 분석
- Git 작업
- 프로젝트 구조 관리

## 특징
- ✅ 레거시 코드 완전 제거
- ✅ AI Helpers v2 완전 통합
- ✅ 프로토콜 기반 추적
- ✅ 자동 캐싱 및 메트릭
- ✅ stdout JSON 프로토콜

## 문제 해결

### ImportError 발생 시
```python
import sys
sys.path.insert(0, 'python')
sys.path.insert(0, 'python/ai_helpers_v2')
```

### 프로젝트 경로 문제
절대 경로 사용을 권장합니다.

## 다음 단계
1. TypeScript 통합 래퍼 작성
2. MCP 서버와 연동
3. 고급 워크플로우 자동화
