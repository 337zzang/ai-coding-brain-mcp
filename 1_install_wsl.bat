@echo off
echo ========================================
echo Claude Code WSL 설치 스크립트
echo ========================================
echo.
echo ⚠️ 이 스크립트는 관리자 권한으로 실행해야 합니다.
echo.
pause

echo 🔧 WSL 기능 활성화 중...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
if %errorlevel% neq 0 (
    echo ❌ WSL 기능 활성화 실패
    pause
    exit /b 1
)

echo 🔧 Virtual Machine Platform 활성화 중...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
if %errorlevel% neq 0 (
    echo ❌ Virtual Machine Platform 활성화 실패
    pause
    exit /b 1
)

echo.
echo ✅ WSL 기능 활성화 완료!
echo.
echo 🔄 지금 재부팅하시겠습니까? (Y/N)
set /p restart="입력: "
if /i "%restart%"=="Y" (
    echo 재부팅 중...
    shutdown /r /t 5
) else (
    echo 수동으로 재부팅 후 2단계 스크립트를 실행하세요.
)
pause
