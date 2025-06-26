# AI Coding Brain MCP 🧠

AI Coding Brain MCP는 Claude와 함께 효율적인 코딩 작업을 돕는 MCP(Model Context Protocol) 서버입니다.

## 🚀 주요 기능

### 📁 파일 시스템 관리
- **스마트 파일 수정**: AST 기반 안전한 코드 수정
- **파일 분석**: 코드 구조 분석 및 의존성 파악
- **디렉토리 구조 관리**: 프로젝트 구조 자동 생성 및 캐싱

### 🔄 Git 버전 관리
- **스마트 커밋**: 컨텍스트 기반 자동 커밋 메시지 생성
- **브랜치 관리**: 스마트 브랜치 생성 및 전환
- **안전한 롤백**: Git stash를 활용한 안전한 작업 복원
- **한글 인코딩 지원**: UTF-8 기반 완벽한 한글 지원

### 📝 .gitignore 관리 (v25.0 신규)
- **프로젝트 분석**: 프로젝트를 스캔하여 .gitignore에 추가할 파일/폴더 자동 제안
- **패턴 추가**: 기존 .gitignore에 새로운 패턴 추가 (중복 자동 제거)
- **파일 생성**: 프로젝트에 맞는 .gitignore 자동 생성

### 🧠 Wisdom 시스템
- **실시간 패턴 감지**: 코드 작성 중 실수 자동 감지
- **학습 시스템**: 프로젝트별 실수 패턴 학습 및 경고
- **베스트 프랙티스**: 프로젝트별 모범 사례 자동 축적

### 📋 워크플로우 관리
- **프로젝트 전환**: 컨텍스트 보존과 함께 프로젝트 전환
- **작업 관리**: Task 기반 체계적인 작업 진행
- **계획 수립**: Phase별 작업 계획 자동 생성

## 🛠️ 설치 및 설정

### 요구사항
- Node.js 18+
- Python 3.8+
- Git

### 설치
```bash
# 저장소 클론
git clone https://github.com/yourusername/ai-coding-brain-mcp.git
cd ai-coding-brain-mcp

# 의존성 설치
npm install

# 빌드
npm run build
```

### Claude Desktop 설정
`claude_desktop_config.json`에 다음 내용 추가:

```json
{
  "mcpServers": {
    "ai-coding-brain": {
      "command": "node",
      "args": ["C:/path/to/ai-coding-brain-mcp/dist/index.js"],
      "cwd": "C:/path/to/your/projects"
    }
  }
}
```

## 📚 사용법

### 프로젝트 전환
```python
flow_project("my-project")
```

### Git 작업
```python
# 상태 확인
git_status()

# 스마트 커밋
git_commit_smart("기능 추가: 로그인 API")

# 브랜치 생성
git_branch_smart("feature/새기능")
```

### .gitignore 관리
```python
# 프로젝트 분석
gitignore_analyze()

# 패턴 추가
gitignore_update(["*.log", "*.tmp"], "임시 파일")

# 새 파일 생성
gitignore_create(["Python", "Node.js", "IDE"])
```

### 파일 작업
```python
# AST 기반 함수 수정
helpers.replace_block("app.py", "function_name", new_code)

# 코드 분석
helpers.parse_with_snippets("app.py")
```

## 🔧 주요 도구 목록

### Git 관련
- `git_status`: Git 상태 확인
- `git_commit_smart`: 스마트 커밋
- `git_branch_smart`: 스마트 브랜치 생성
- `git_rollback_smart`: 안전한 롤백
- `git_push`: 원격 저장소 푸시

### .gitignore 관련
- `gitignore_analyze`: 프로젝트 분석 및 제안
- `gitignore_update`: 패턴 추가
- `gitignore_create`: 새 파일 생성

### 파일 시스템
- `execute_code`: Python 코드 실행
- `file_analyze`: 파일 구조 분석

### 워크플로우
- `flow_project`: 프로젝트 전환
- `plan_project`: 계획 수립
- `task_manage`: 작업 관리
- `next_task`: 다음 작업 진행

### Wisdom
- `wisdom_stats`: 통계 확인
- `track_mistake`: 실수 추적
- `add_best_practice`: 베스트 프랙티스 추가

## 📋 버전 히스토리

### v25.0 (2025-06-26)
- 백업 시스템을 Git 기반으로 완전 전환
- .gitignore 관리 기능 추가
- Git 한글 인코딩 문제 해결

### v24.0
- Wisdom 시스템 도입
- AST 기반 코드 수정 도구 강화

## 🤝 기여하기

이슈와 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License