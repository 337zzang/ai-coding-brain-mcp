@echo off
echo ========================================
echo Claude Code 설치 스크립트
echo ========================================
echo.

echo 🔧 WSL Ubuntu에서 패키지 업데이트 중...
wsl sudo apt update
if %errorlevel% neq 0 (
    echo ❌ 패키지 업데이트 실패
    pause
    exit /b 1
)

echo 🔧 Node.js 및 npm 설치 중...
wsl sudo apt install -y nodejs npm
if %errorlevel% neq 0 (
    echo ❌ Node.js 설치 실패
    pause
    exit /b 1
)

echo 📦 Node.js 버전 확인...
wsl node --version
wsl npm --version

echo 🔧 npm 글로벌 디렉토리 설정...
wsl mkdir -p ~/.npm-global
wsl npm config set prefix '~/.npm-global'
wsl echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc

echo 🤖 Claude Code 설치 중...
wsl bash -c "source ~/.bashrc && npm install -g @anthropic-ai/claude-code"
if %errorlevel% neq 0 (
    echo ❌ Claude Code 설치 실패
    pause
    exit /b 1
)

echo 📦 Claude Code 버전 확인...
wsl bash -c "source ~/.bashrc && claude --version"

echo.
echo ✅ Claude Code 설치 완료!
echo.
echo 🚀 다음 단계:
echo 1. WSL Ubuntu 터미널을 열어주세요
echo 2. 'claude' 명령어를 실행하세요
echo 3. '/auth login' 으로 인증하세요
echo 4. API 키를 입력하세요
echo.
pause
