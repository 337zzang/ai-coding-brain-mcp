@echo off
echo ========================================
echo Claude Code 설치 테스트
echo ========================================
echo.

echo 🧪 WSL 상태 확인...
wsl --version
echo.

echo 🧪 Ubuntu 상태 확인...
wsl --list --verbose
echo.

echo 🧪 Node.js 상태 확인...
wsl node --version
wsl npm --version
echo.

echo 🧪 Claude Code 상태 확인...
wsl bash -c "source ~/.bashrc && claude --version"
echo.

echo 🧪 전체 테스트 완료!
echo 💡 모든 버전이 정상적으로 표시되면 설치가 완료된 것입니다.
pause
