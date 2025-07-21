
# 📁 AI Coding Brain MCP 파일 구조 규칙

## 디렉토리 구조

```
ai-coding-brain-mcp/
├── docs/                    # 📄 모든 문서 (설계, 분석, 가이드)
│   ├── task-workflow/       # Task 워크플로우 관련 문서
│   ├── flow-improvement/    # Flow 개선 관련 문서
│   └── o3-analysis/         # o3 분석 결과
│
├── test/                    # 🧪 테스트 파일 및 결과
│   ├── unit/               # 단위 테스트
│   ├── integration/        # 통합 테스트
│   └── results/            # 테스트 결과 JSON
│
├── backups/                 # 💾 백업 파일
│   └── YYYYMMDD/           # 날짜별 백업
│
├── python/                  # 🐍 소스 코드
│   └── ai_helpers_new/     # 메인 모듈
│
├── examples/                # 📚 예제 코드
│
└── .ai-brain/              # 🧠 AI 작업 상태 (임시)
    ├── flows.json          # Flow 상태
    ├── o3_tasks/           # o3 작업 추적
    └── checkpoints/        # 작업 체크포인트
```

## 파일 저장 규칙

### 1. 문서 (docs/)
- 설계 문서: `docs/[기능명]/[문서명]_design.md`
- 분석 문서: `docs/[기능명]/[문서명]_analysis.md`
- 보고서: `docs/[기능명]/[문서명]_report.md`
- o3 분석: `docs/o3-analysis/[주제]_analysis.md`

### 2. 테스트 (test/)
- 테스트 코드: `test/test_[모듈명].py`
- 테스트 결과: `test/results/[테스트명]_result.json`
- 테스트 데이터: `test/data/[데이터명].json`

### 3. 백업 (backups/)
- 코드 백업: `backups/[파일명].backup_YYYYMMDD_HHMMSS`
- 일일 백업: `backups/YYYYMMDD/[파일명]`

### 4. AI 작업 상태 (.ai-brain/)
- Flow 상태: `.ai-brain/flows.json`
- o3 작업: `.ai-brain/o3_task_[ID].json`
- 체크포인트: `.ai-brain/checkpoints/[작업명]_checkpoint.json`

## ❌ 하지 말아야 할 것
- 모든 파일을 .ai-brain에 저장
- 백업 파일을 소스 디렉토리에 저장
- 문서를 코드 디렉토리에 저장

## ✅ 권장 사항
- 관련 문서는 하위 디렉토리로 그룹화
- 백업은 날짜/시간 스탬프 포함
- 테스트 결과는 별도 보관
- 임시 파일은 .ai-brain에만
