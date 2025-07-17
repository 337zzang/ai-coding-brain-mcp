#!/bin/bash
# AI Coding Brain MCP 빌드 스크립트

echo "🔨 AI Coding Brain MCP 빌드 시작..."

# TypeScript 컴파일
if command -v tsc &> /dev/null; then
    echo "✅ TypeScript 컴파일러 발견"
    tsc
    echo "✅ 빌드 완료!"
else
    echo "❌ TypeScript가 설치되지 않았습니다"
    echo "실행: npm install"
fi
