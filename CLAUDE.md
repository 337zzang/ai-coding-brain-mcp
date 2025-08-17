# 프로젝트별 Claude Code 가이드라인

## 📌 프로젝트 정보
- **프로젝트명**: ai-coding-brain-mcp
- **주요 기술**: Node.js, Python, MCP Protocol
- **최종 업데이트**: 2025-08-16

## 🎯 프로젝트별 특수 규칙

### 1. 코딩 컨벤션
- **네이밍**: snake_case (Python), camelCase (JavaScript)
- **인덴트**: 4 spaces (Python), 2 spaces (JavaScript)
- **주석**: 함수별 docstring 필수

### 2. 자주 사용하는 명령어
```bash
# MCP 서버 실행
npm run build && node dist/index.js

# Python 헬퍼 테스트
python -m pytest tests/

# 통합 테스트
npm test
```

### 3. 프로젝트 구조
```
ai-coding-brain-mcp/
├── python/          # Python 헬퍼 함수
├── src/            # TypeScript MCP 서버
├── dist/           # 빌드된 JavaScript
├── tests/          # 테스트 파일
└── .ai-brain/      # AI 메모리 및 상태
```

## 🚀 Quick Commands

### 개발 워크플로우
```bash
# 새 기능 시작 (Plan Mode 활용)
claude --new "implement [feature_name]"

# 코드 분석 및 테스트 (병렬 실행)
claude "analyze and test @python/ai_helpers_new/*.py"

# 배포 전 검증
claude "optimize and validate before deployment"
```

### 디버깅
```bash
# 버그 분석 (Think 모드 활용)
claude "think harder about this memory leak in @src/handlers.ts"

# 성능 문제 해결
claude "analyze performance bottleneck in @python/json_repl_session.py"
```

## 📋 체크리스트

### 코드 작성 전
- [ ] 기존 코드 분석 (@참조 활용)
- [ ] Plan Mode로 전체 계획 수립
- [ ] 복잡도 평가 (Think 레벨 결정)

### 코드 작성 후
- [ ] code-analyzer로 품질 검증
- [ ] test-runner로 테스트 실행
- [ ] code-optimizer로 최종 최적화

### PR 생성 전
- [ ] 모든 테스트 통과
- [ ] 문서 업데이트
- [ ] 성능 벤치마크 확인

## 💡 팀 컨벤션

### Git 커밋 메시지
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드 업무 수정
```

### 코드 리뷰 규칙
1. 모든 PR은 최소 1명 리뷰
2. 테스트 커버리지 95% 이상
3. 성능 regression 없음 확인

## 🔗 관련 문서
- [README.md](./README.md) - 프로젝트 개요
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 기여 가이드
- [API.md](./docs/API.md) - API 문서

---
*이 문서는 프로젝트별 Claude Code 설정입니다.*
*전역 설정은 ~/.claude/CLAUDE.md를 참조하세요.*
