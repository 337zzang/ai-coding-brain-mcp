# 폴더 기반 Flow 시스템 설계 (by o3)

📌 목표  
1) 모든 Flow를 하나의 `flows.json`에 몰아-넣던 구조 → 프로젝트별 폴더-트리로 분산 저장  
2) Git 협업 시 충돌 감소·리뷰 용이  
3) 기존 프로젝트(legacy) 무중단 마이그레이션

────────────────────────────────────────
1. 새 디렉터리 스펙
────────────────────────────────────────
프로젝트루트/
└── .ai-brain/
    └── flows/
        └── <flow_id>/                 # ← Flow 단위 폴더
            ├── flow_metadata.json     # ← Flow 자체 메타
            └── plans/                 # ← Plan 전용 서브폴더
                ├── <plan_id>_<name>.json
                └── ...

규칙
• <flow_id> : Flow.id 그대로(충돌 없도록 slugify 제공)  
• <plan_id>_<name>.json : plan.id + sanitized(plan.name). 중복 시 plan.id만 사용  
• 모든 JSON 은 UTF-8, 끝에 ‘\n’ 포함, 들여쓰기 2칸

────────────────────────────────────────
2. 도메인 모델은 “변경 없음”
────────────────────────────────────────
Flow(plans: Dict[str, Plan]) 그대로 두고, 단지 **물리적 직렬화 방식**만 변경한다.  
→ 다른 계층(서비스, CLI, UI)은 수정 불요.

────────────────────────────────────────
3. FlowRepository 수정 설계
────────────────────────────────────────
(생략된 부분만 표시)

class JsonFlowRepository(FlowRepository):
    FLOW_DIR      = '.ai-brain/flows'
    META_FILENAME = 'flow_metadata.json'
    PLANS_DIR     = 'plans'

    # ---------------------------------
    # 1) 경로 해석 헬퍼
    # ---------------------------------
    def _root(self) -> Path:
        # ProjectContext가 주면 context.root / FLOW_DIR, 없으면 cwd 사용
        base = self._context.root if getattr(self, '_context', None) else Path.cwd()
        return base / self.FLOW_DIR

    def _flow_dir(self, flow_id: str) -> Path:
        return self._root() / flow_id

    def _plan_file(self, flow_id: str, plan_id: str, plan_name: str) -> Path:
        safe_name = slugify(plan_name)   # 한글 가능, 공백→_
        return self._flow_dir(flow_id) / self.PLANS_DIR / f'{plan_id}_{safe_name}.json'

    # ---------------------------------
    # 2) load_all()
    # ---------------------------------
    def load_all(self) -> Dict[str, Flow]:
        result: Dict[str, Flow] = {}

        root = self._root()
        if not root.exists():
            return result

        for flow_path in root.iterdir():
            if not flow_path.is_dir():
                continue

            meta_fp = flow_path / self.META_FILENAME
            if not meta_fp.exists():
                continue  # 잘못된 디렉터리는 스킵

            with meta_fp.open() as f:
                meta_dict = json.load(f)

            # --- Plan 병합 ---
            plans_dir = flow_path / self.PLANS_DIR
            plan_objs = {}
            if plans_dir.exists():
                for fp in plans_dir.glob('*.json'):
                    with fp.open() as pf:
                        p_dict = json.load(pf)
                    plan_objs[p_dict['id']] = Plan.model_validate(p_dict)
            meta_dict['plans'] = plan_objs

            flow = Flow.model_validate(meta_dict)
            result[flow.id] = flow

        # ------- 레거시 falls back -------
        legacy_file = root / 'flows.json'
        if legacy_file.exists():
            with legacy_file.open() as f:
                legacy_dict: Dict[str, Any] = json.load(f)
            # 1개의 Flow만 들어있던 구조
            legacy_flow = Flow.model_validate(legacy_dict)
            result[legacy_flow.id] = legacy_flow

        return result

    # ---------------------------------
    # 3) save()
    # ---------------------------------
    def save(self, flow: Flow) -> None:
        flow_dir = self._flow_dir(flow.id)
        plans_dir = flow_dir / self.PLANS_DIR
        plans_dir.mkdir(parents=True, exist_ok=True)

        # (a)  메타데이터
        meta_path = flow_dir / self.META_FILENAME
        meta_dict = flow.model_dump(exclude={'plans'})
        self._atomic_write(meta_path, meta_dict)

        # (b)  Plan 파일
        current_plan_files = set()
        for idx, pl in enumerate(flow.plans.values(), start=1):
            fp = self._plan_file(flow.id, pl.id, pl.name)
            current_plan_files.add(fp)
            self._atomic_write(fp, pl.model_dump())

        # (c)  삭제된 Plan 청소
        for fp in plans_dir.glob('*.json'):
            if fp not in current_plan_files:
                fp.unlink()

    def save_all(self, flows: Dict[str, Flow]) -> None:
        for f in flows.values():
            self.save(f)

    # ---------------------------------
    # 4) delete()
    # (조상 메서드 호출 대신 디렉터리 통째 삭제)
    # ---------------------------------
    def delete(self, flow_id: str) -> bool:
        flow_dir = self._flow_dir(flow_id)
        if flow_dir.exists():
            shutil.rmtree(flow_dir)
            return True
        return False

    # ---------------------------------
    # 5) 유틸 – 원자적 쓰기
    # ---------------------------------
    @staticmethod
    def _atomic_write(path: Path, data: dict) -> None:
        tmp = path.with_suffix('.tmp')
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        tmp.replace(path)

────────────────────────────────────────
4. 마이그레이션 전략
────────────────────────────────────────
단계 0 – 백업  
• `flows.json`를 `flows.json.bak_YYYYMMDDhhmmss`로 복사

단계 1 – 1회성 스크립트 (`python -m ai_brain.migrate_flows`)  

```python
from ai_brain.infrastructure.flow_repository import JsonFlowRepository

def run_migration(context: ProjectContext):
    repo = JsonFlowRepository(context=context)

    legacy_file = context.root / '.ai-brain/flows/flows.json'
    if not legacy_file.exists():
        print('🔹 No legacy flows.json, skip.')
        return

    with legacy_file.open() as f:
        legacy_flow = Flow.model_validate(json.load(f))

    repo.save(legacy_flow)
    legacy_file.rename(legacy_file.with_suffix('.migrated.bak'))
    print(f'✅ migrated Flow {legacy_flow.id} → folder structure')
```

단계 2 – 레거시 읽기 호환  
`load_all()`은 위에서 보듯 `flows.json`도 읽어 들인다.  
• 따라서 “마이그레이션 안 했지만 새 버전 코드로 실행”해도 동작  
• 다만 저장 시점엔 새 구조로만 저장 → 결과적으로 1회성 자동 변환

단계 3 – CI 체크  
• `.github/workflows/tests.yml` 등에 `python -m ai_brain.migrate_flows --dry-run` 추가해 충돌 여부 사전 탐지  
• 마이그레이션 완료 후 Pull Request 머지 규칙: `flows.json` 존재 금지

────────────────────────────────────────
5. 변경-영향 및 테스트 포인트
────────────────────────────────────────
1. 프로젝트가 여러 Flow를 가질 수 있는가?  
   – 네. 각 Flow 폴더 분산 → 동시 작업 충돌 최소화

2. 성능  
   – 로드 시 폴더 갯수만큼 I/O 증가. CLI·IDE 초기화에서 100 flow ≒ 0.1s 미만 (측정 필요)  
   – 대안: `flow_index.json` 캐시 추가 가능 (후순위)

3. 단위 테스트
   • test_save_and_load_should_preserve_data()  
   • test_delete_removes_whole_directory()  
   • test_migration_script_creates_expected_files()

────────────────────────────────────────
6. 향후 확장 여지
────────────────────────────────────────
• Plan도 다시 Task 단위 폴더로 쪼개 Git diff granularity ↑  
• `FlowRepository`에서 S3, GCS back-end 구현 시 동일 패턴 적용 가능  
• 메타데이터 스키마 변경 시 `version` 필드 추가 및 업그레이드 루틴 분리

────────────────────────────────────────
요약
• FlowRepository 의 저장 위치를 “폴더/메타/개별 Plan 파일” 구조로 전환  
• load_all()/save()/delete() 로직을 디렉터리 기준으로 재작성, 레거시 `flows.json` 읽기 지원  
• 1회용 마이그레이션 스크립트 제공 → 기존 데이터 자동 전환 후 안전 백업  
→ 결과적으로 Git 충돌 감소, 리뷰 편의성 ↑, 대용량 프로젝트 확장성 확보.