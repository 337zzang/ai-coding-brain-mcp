@echo off
echo ========================================
echo Claude Code Ubuntu 설치 스크립트
echo ========================================
echo.

echo 🔧 WSL 업데이트 중...
wsl --update
if %errorlevel% neq 0 (
    echo ❌ WSL 업데이트 실패
    pause
    exit /b 1
)

echo 🔧 Ubuntu 설치 중...
wsl --install Ubuntu
if %errorlevel% neq 0 (
    echo ❌ Ubuntu 설치 실패
    pause
    exit /b 1
)

echo.
echo ✅ Ubuntu 설치 완료!
echo 💡 Ubuntu 초기 설정을 완료한 후 3단계를 실행하세요.
pause
