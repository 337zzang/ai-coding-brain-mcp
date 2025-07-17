@echo off
cd /d C:\Users\82106\Desktop\ai-coding-brain-mcp
echo === TypeScript Compile Check ===
echo.
call npx tsc --noEmit
echo.
echo Exit Code: %ERRORLEVEL%
