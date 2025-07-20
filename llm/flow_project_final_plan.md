# flow_project 최종 개선 계획

## o3 분석 요약
- 추론 시간: high effort로 심층 분석
- 9,159자의 상세 분석 제공
- 10단계 구현 로드맵 제시


## 📋 핵심 분석 결과

### 1. 현재 시스템의 장단점
**장점**:
- ✅ 바탕화면 기반으로 직관적
- ✅ os.chdir로 상대 경로 사용 가능
- ✅ Git, npm 등 도구가 자연스럽게 작동

**단점**:
- ❌ 프로젝트별 컨텍스트 미분리
- ❌ 단일 캐시 파일로 마지막 프로젝트만 기억
- ❌ 멀티 세션/스레드에서 충돌 가능
- ❌ 바탕화면이 없는 환경에서 작동 불가

### 2. 개선 방향

#### A. 단기 개선 (기존 구조 유지)
1. **프로젝트별 메모리 폴더 활성화**
   - 각 프로젝트에 .flow/ 폴더 생성
   - context.json, progress.md 자동 관리

2. **컨텍스트 자동 저장/복원**
   ```python
   def flow_project(name):
       # 현재 프로젝트 상태 저장
       save_current_context()

       # 프로젝트 전환
       os.chdir(project_path)

       # 새 프로젝트 컨텍스트 복원
       restore_project_context()
   ```

3. **진행 상황 가시화**
   - progress.md 자동 생성
   - 태스크 상태 추적

#### B. 장기 개선 (새로운 구조)
```
~/.flow_project/              # 중앙 레지스트리
├── config.toml              # 전역 설정
├── registry.json            # 프로젝트 목록
└── sessions/                # 프로젝트별 세션
    └── {project_id}/
        ├── context.json     # 컨텍스트
        ├── env_snapshot.json # 환경 상태
        └── workflow.json    # 워크플로우
```

### 3. 구현 우선순위

#### Phase 1 (즉시 실행 가능)
```python
# 1. 프로젝트별 .flow 폴더 생성
def ensure_flow_folder(project_path):
    flow_path = Path(project_path) / '.flow'
    flow_path.mkdir(exist_ok=True)

    # 기본 파일 생성
    (flow_path / 'context.json').touch()
    (flow_path / 'progress.md').touch()

# 2. 컨텍스트 저장/복원
def save_context(project_path):
    context = {
        'cwd': os.getcwd(),
        'env': dict(os.environ),
        'timestamp': datetime.now().isoformat(),
        'open_files': get_open_files(),
        'git_status': get_git_status()
    }
    save_json(project_path / '.flow/context.json', context)
```

#### Phase 2 (1주 내)
- Registry 시스템 구축
- 가상환경 자동 활성화
- IDE 통합

### 4. 호환성 유지 전략
```python
# 기존 코드와 100% 호환
fp("my_project")  # 변경 없음

# 새로운 기능은 선택적 사용
fp("my_project", restore_env=True)  # 환경 복원
fp("my_project", show_progress=True)  # 진행 상황 표시
```


## 다음 단계
1. Phase 1 구현 시작 (프로젝트별 .flow 폴더)
2. 기존 시스템과 병행 운영
3. 점진적 마이그레이션
