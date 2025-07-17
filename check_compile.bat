@echo off
cd /d C:\Users\82106\Desktop\ai-coding-brain-mcp
echo === TypeScript Type Check === > C:\Users\82106\Desktop\ai-coding-brain-mcp\compile_result.txt
npx tsc --noEmit >> C:\Users\82106\Desktop\ai-coding-brain-mcp\compile_result.txt 2>&1
echo. >> C:\Users\82106\Desktop\ai-coding-brain-mcp\compile_result.txt
echo Exit Code: %ERRORLEVEL% >> C:\Users\82106\Desktop\ai-coding-brain-mcp\compile_result.txt
