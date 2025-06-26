# 🔐 GitHub 인증 설정 가이드

## 📋 목차
1. [Personal Access Token (PAT) 설정](#personal-access-token-설정)
2. [SSH 키 설정](#ssh-키-설정)
3. [Git Credential Manager 설정](#git-credential-manager)
4. [보안 주의사항](#보안-주의사항)

## Personal Access Token 설정

### 1. GitHub에서 PAT 생성

1. GitHub.com 로그인
2. 우측 상단 프로필 → **Settings**
3. 좌측 메뉴 최하단 **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. **Generate new token** → **Generate new token (classic)**
6. 설정:
   - **Note**: `ai-coding-brain-mcp` (토큰 용도)
   - **Expiration**: 90 days (또는 원하는 기간)
   - **Scopes**: 
     - ✅ `repo` (전체 저장소 접근)
     - ✅ `workflow` (GitHub Actions)
7. **Generate token** 클릭
8. **토큰 복사** (한 번만 표시되므로 안전한 곳에 저장!)

### 2. Windows에서 PAT 설정

#### 방법 1: Git Credential Manager (권장)
```bash
# Git Credential Manager 확인
git config --global credential.helper

# 처음 push할 때 인증 창이 뜨면:
# Username: GitHub 사용자명
# Password: PAT 토큰 (비밀번호 대신!)
```

#### 방법 2: 환경 변수 설정
```bash
# Windows PowerShell에서
[Environment]::SetEnvironmentVariable("GH_TOKEN", "your-pat-token", "User")

# 또는 시스템 환경 변수에 추가
# 시스템 속성 → 환경 변수 → GH_TOKEN 추가
```

#### 방법 3: Git Config에 저장 (보안 주의!)
```bash
# HTTPS URL에 토큰 포함 (권장하지 않음)
git remote set-url origin https://USERNAME:TOKEN@github.com/337zzang/ai-coding-brain-mcp.git
```

### 3. 안전한 PAT 관리

프로젝트에 `.env` 파일 생성:
```env
# .env 파일 (절대 커밋하지 마세요!)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=337zzang
```

## SSH 키 설정

### 1. SSH 키 생성
```bash
# PowerShell 또는 Git Bash에서
ssh-keygen -t ed25519 -C "your-email@example.com"

# 기본 위치 사용 (Enter 키)
# 비밀번호 설정 (선택사항)
```

### 2. SSH 키 GitHub에 등록
```bash
# 공개 키 복사
cat ~/.ssh/id_ed25519.pub
```

1. GitHub.com → Settings → SSH and GPG keys
2. **New SSH key**
3. Title: `AI Coding Brain MCP Dev Machine`
4. Key: 복사한 공개 키 붙여넣기
5. **Add SSH key**

### 3. SSH로 리모트 변경
```bash
# HTTPS를 SSH로 변경
git remote set-url origin git@github.com:337zzang/ai-coding-brain-mcp.git
```

## Git Credential Manager

### Windows 기본 설정
```bash
# Git Credential Manager 설치 확인
git config --global credential.helper manager

# 캐시 시간 설정 (선택사항)
git config --global credential.helper 'cache --timeout=3600'
```

### 저장된 인증 정보 확인/삭제
```bash
# Windows 자격 증명 관리자에서
# 제어판 → 사용자 계정 → 자격 증명 관리자 → Windows 자격 증명
# git:https://github.com 항목 확인/수정/삭제
```

## 보안 주의사항

### ❌ 하지 말아야 할 것
1. 토큰을 코드에 직접 입력
2. 토큰을 커밋
3. 공개 저장소에 토큰 노출

### ✅ 해야 할 것
1. `.gitignore`에 `.env` 추가
2. 토큰 정기적 갱신
3. 최소 권한 원칙 (필요한 scope만)
4. 2FA (2단계 인증) 활성화

## 프로젝트 적용 방법

### 1. Git 초기화 및 연결
```bash
cd C:\Users\Administrator\Desktop\ai-coding-brain-mcp

# Git 초기화
git init

# 사용자 정보 설정
git config user.name "Your Name"
git config user.email "your-email@example.com"

# 원격 저장소 추가
git remote add origin https://github.com/337zzang/ai-coding-brain-mcp.git

# 첫 커밋
git add .
git commit -m "Initial commit: AI Coding Brain MCP v1.0.0"

# 푸시 (여기서 인증 필요)
git push -u origin main
```

### 2. MCP 도구로 푸시
```python
# Git 상태 확인
git_status()

# 커밋
git_commit_smart("기능 추가: Git 백업 시스템")

# 푸시 (인증 정보가 저장되어 있으면 자동)
git_push()
```

## 문제 해결

### 인증 실패 시
```bash
# 저장된 인증 정보 삭제
git config --global --unset credential.helper

# 다시 설정
git config --global credential.helper manager
```

### 403 Forbidden 오류
- PAT 토큰 권한 확인 (repo scope 필요)
- 토큰 만료 확인
- 저장소 접근 권한 확인

### SSL 인증서 오류 (회사 네트워크)
```bash
# 임시 해결 (보안 주의!)
git config --global http.sslVerify false
```

---

*최종 업데이트: 2025-06-26*
