# ai-coding-brain-mcp

통합 AI 코딩 브레인 MCP - Memory Bank, Desktop Commander, Notebook, Claude Memory 통합

## 📋 프로젝트 정보

- **버전**: 1.0.0
- **언어**: TypeScript/JavaScript
- **최종 업데이트**: 2025-07-02 13:59:10

## 📊 프로젝트 통계

- **전체 파일**: 494개
- **디렉토리**: 136개
- **주요 언어**:
  - Python: 82개 파일
  - TypeScript: 34개 파일
  - JavaScript: 39개 파일

## 🗂️ 프로젝트 구조

```
ai-coding-brain-mcp/
├── backup/
├── backup_before_refactor_20250701_111943/
├── docs/
├── memory/
├── python/
├── src/
├── test/
└── ...
```


## 🛠️ 주요 기능

### 1. start_project
새 프로젝트를 생성하고 초기 구조를 설정합니다.

```python
# 새 프로젝트 생성
result = helpers.start_project("my-new-project")

# Git 초기화 없이 프로젝트 생성
result = helpers.start_project("my-project", init_git=False)
```

**생성되는 구조:**
```
my-new-project/
├── README.md          # 프로젝트 문서
├── src/              # 소스 코드
├── test/             # 테스트 코드
├── docs/             # 문서
├── memory/           # 프로젝트 메모리/컨텍스트
└── .gitignore        # Git 무시 파일 (init_git=True인 경우)
```

### 2. flow_project
기존 프로젝트로 전환하고 컨텍스트를 로드합니다.

```python
# 프로젝트 전환
result = helpers.flow_project("existing-project")

# 반환값
{
    'success': True,
    'project_name': 'existing-project',
    'path': '/path/to/project',
    'git_branch': 'main',
    'workflow_status': {...}
}
```

### 3. execute_code
Python 코드를 안전한 환경에서 실행합니다.

```python
result = helpers.execute_code("""
print("Hello from AI Coding Brain!")
""")
```

## 🚀 시작하기

### 설치

```bash
# 의존성 설치
npm install
pip install -r requirements.txt
```

### 실행

```bash
# 프로젝트 실행 명령어를 여기에 추가하세요
```

## 📖 문서

- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) - 프로젝트 상세 컨텍스트
- [file_directory.md](./file_directory.md) - 파일 구조 문서

## 🤝 기여하기

기여를 환영합니다! PR을 보내주세요.

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*
