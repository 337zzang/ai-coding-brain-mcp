# o3_task_0016 분석 결과

아래는 “o3 분석 결과”를 Flow Project v2의 Plan/Task 계층 구조에 자연스럽게 편입하여 ‘지식 베이스(knowledge base)’를 구축‧활용하는 전체 로드맵이다.  

────────────────────────────────
1. 폴더·파일 레이아웃 확정
────────────────────────────────
.ai-brain/  
├── workflow.json             # Plan/Task 메타데이터 (v2 스키마)  
├── context.json              # 대화 세션 컨텍스트  
├── documents/                # Plan별 문서 스테이징 공간  
│   └── {plan_id}/  
│       ├── summary.md  
│       └── references/       # (o3 결과, RFC, 논문 등)  
├── llm/                      # “소스” o3 분석 결과 저장소  
│   └── o3_{stamp}_{slug}.md  # ↔ Plan/Task에 연결할 원본  
└── kb/                       # 지식 베이스 전용  
    ├── index.json            # md → Plan/Task 매핑 인덱스  
    └── vector_store.faiss    # 임베딩 검색용(옵션)  

핵심 개념  
• llm/ 는 변하지 않는 “원본 결과물” 디렉터리  
• documents/{plan}/references/ 는 각 Plan 에 직접 귀속되는 ‘가공본(사본 or symlink)’  
• kb/ 는 검색·질의 응답을 위한 색인 및 벡터 스토어 저장소  

────────────────────────────────
2. o3 결과물에 메타데이터 주입
────────────────────────────────
o3 파일을 md 로 덤프할 때 YAML front-matter 를 추가해 연결 정보를 명시하면 이후 자동화가 쉬워진다.

예: llm/o3_20231130_arch_diag.md
```md
---
title: "아키텍처 흐름도 분석"
plan_id: "plan_001"
task_id: "task_001"
tags: ["architecture", "refactor"]
created_at: "2023-11-30T08:58:21Z"
author: "o3"
---
# 분석 내용
…
```

규칙  
• plan_id / task_id 중 하나는 필수  
• 복수 Task 에 걸친 경우 task_ids: [ … ] 형태 허용  
• tags 로 주제별 분류 → 벡터 검색 보조  

────────────────────────────────
3. 통합 스크립트 (import_o3.py) 설계
────────────────────────────────
목표: llm/ 아래 md 를 스캔 → (a) workflow.json 에 참조 추가, (b) documents/{plan}/references/ 로 사본 or 심볼릭링크 생성, (c) kb/index.json & vector_store 갱신.

주요 흐름(pseudocode)

```python
def run():
    wf = load_json('.ai-brain/workflow.json')
    kb_index = load_json('.ai-brain/kb/index.json', default={})

    for path in glob('.ai-brain/llm/*.md'):
        meta = parse_front_matter(path)
        pid = meta.get('plan_id')
        tids = meta.get('task_id') or meta.get('task_ids', [])
        if not pid:
            continue                       # 최소 Plan 은 필요
        
        # 1) Plan 레퍼런스 등록
        plan = find_plan(wf, pid)
        plan['context'].setdefault('references', [])
        if path not in plan['context']['references']:
            plan['context']['references'].append(path)
        
        # 2) Task 레퍼런스 등록
        for tid in tids if isinstance(tids, list) else [tids]:
            task = find_task(plan, tid)
            task.setdefault('references', [])
            if path not in task['references']:
                task['references'].append(path)
        
        # 3) documents/{plan}/references/ 로 복사 or symlink
        dst_dir = f'.ai-brain/documents/{pid}/references/'
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(path))
        if not os.path.exists(dst):
            os.symlink(os.path.relpath(path, dst_dir), dst)   # or shutil.copy
        
        # 4) KB 인덱스 갱신
        kb_index[path] = {
            'plan_id': pid,
            'task_ids': tids,
            'tags': meta.get('tags', []),
            'title': meta.get('title'),
            'created_at': meta.get('created_at')
        }
        
        # 5) (선택) 벡터 임베딩 추가
        embed_and_store(path, '.ai-brain/kb/vector_store.faiss')

    wf['metadata']['updated_at'] = now_iso()
    save_json('.ai-brain/workflow.json', wf)
    save_json('.ai-brain/kb/index.json', kb_index)
```

• embed_and_store 는 OpenAI / HuggingFace 임베딩을 생성 후 FAISS 에 upsert  
• 스크립트는 각 커밋 or /flow import-o3 명령으로 호출  

────────────────────────────────
4. workflow.json 필드 확장 예시
────────────────────────────────
```jsonc
{
  "plans": [
    {
      "id": "plan_001",
      "title": "WorkflowManager 리팩토링",
      "context": {
        "references": [
          "llm/o3_20231130_arch_diag.md",
          "llm/o3_20231201_command_table.md"
        ]
      },
      "tasks": [
        {
          "id": "task_001",
          "title": "명령어 매핑 수정",
          "references": ["llm/o3_20231130_arch_diag.md"]
        }
      ]
    }
  ]
}
```

Task 레벨에도 references 배열을 허용해 세밀한 추적을 지원한다.

────────────────────────────────
5. 지식 베이스 조회 API (선택)
────────────────────────────────
FastAPI 예시:

GET /kb/search?q=“명령어 시스템 개선” →  
1) vector_store.similarity_search(q)  
2) kb/index.json 통해 Plan/Task 매핑 반환 →  
3) UI 에서 해당 Plan/Task 로 하이퍼링크

응답 형태
```json
[
  {
    "score": 0.87,
    "file": "llm/o3_20231130_arch_diag.md",
    "snippet": "...명령어 시스템의 문제점은...",
    "plan_id": "plan_001",
    "task_ids": ["task_001"]
  }
]
```

────────────────────────────────
6. /flow 명령어 확장
────────────────────────────────
/flow import-o3             # llm/ → Plan/Task 매핑 자동 반영  
/flow kb search <query>     # 벡터 검색 결과 요약  
/flow kb show <file|plan>   # 특정 분석 문서 or Plan 관련 문서 목록 출력  

────────────────────────────────
7. 운영 가이드라인
────────────────────────────────
1) o3 팀은 항상 front-matter 를 포함하여 md 파일을 생성  
2) Plan/Task 생성 → ID 확정 → o3 측과 공유  
3) 개발자는 import-o3 스크립트를 주기적으로 실행하거나 CI 파이프라인에 포함  
4) 커밋 시 .ai-brain/kb/vector_store.* 는 대용량일 경우 Git-LFS 로 관리  
5) Plan 완료 시 documents/{plan}/summary.md 에 핵심 레슨 learned를 수동·자동 병합하여 “폐쇄형 지식 항목”으로 보존  

────────────────────────────────
8. 기대 효과
────────────────────────────────
• 분석 결과가 Plan/Task 메타와 1:1 ― N 으로 직접 연결되어 “잃어버린 맥락” 방지  
• kb/ 레이어 덕분에 LLM 이 과거 분석·결정·이슈를 즉시 검색·조합 → 답변 품질 향상  
• documents/ 경로를 통해 인간 개발자도 브라우저나 IDE 플러그인으로 손쉽게 열람  
• 전체 프로세스가 스크립트화되어 프로젝트 규모가 커져도 관리비용 최소화  

이렇게 하면 Flow Project v2와 o3 분석 결과가 결합된 일관된 지식 생태계를 구축할 수 있다.