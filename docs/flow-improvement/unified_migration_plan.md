# Flow-Project 통합 시스템 마이그레이션 계획

## 🔄 마이그레이션 단계

### Phase 1: 데이터 백업 및 분석 (Day 1)
1. **전체 백업**
   ```python
   # 백업 스크립트
   backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
   backup_dir = f'.ai-brain/backups/migration_{backup_timestamp}'

   # 백업할 파일들
   - .ai-brain/flows.json
   - ~/.ai-coding-brain/cache/current_project.json
   - .ai-brain/current_flow.txt
   - .ai-brain/contexts/
   ```

2. **데이터 분석**
   - 현재 프로젝트 수
   - Flow 수 및 상태
   - 고아 Flow (project가 없는 것들)
   - 중복 Flow

### Phase 2: 마이그레이션 스크립트 실행 (Day 2)
```python
def migrate_to_unified():
    # 1. 기존 데이터 읽기
    old_flows = read_json('.ai-brain/flows.json')
    old_project = read_json('~/.ai-coding-brain/cache/current_project.json')

    # 2. 프로젝트별 Flow 매핑
    project_flow_map = {}
    for flow_id, flow in old_flows.items():
        project_name = flow.get('project') or flow.get('name')
        if project_name:
            if project_name not in project_flow_map:
                project_flow_map[project_name] = []
            project_flow_map[project_name].append(flow_id)

    # 3. 통합 데이터 구조 생성
    unified_data = {
        'projects': {},
        'flows': old_flows,
        'current': {
            'project': old_project.get('name'),
            'flow_id': read_file('.ai-brain/current_flow.txt')
        }
    }

    # 4. 프로젝트 정보 생성
    for project_name, flow_ids in project_flow_map.items():
        # Primary Flow 선택 (가장 최근 것)
        primary_flow_id = select_primary_flow(flow_ids)

        unified_data['projects'][project_name] = {
            'path': find_project_path(project_name),
            'primary_flow_id': primary_flow_id,
            'all_flow_ids': flow_ids
        }
```

### Phase 3: 인터페이스 통합 (Day 3-4)
1. **명령어 매핑**
   ```python
   COMMAND_MAPPING = {
       '/flow': '/project',           # Flow 명령을 프로젝트로
       '/flow create': '/create',     # 프로젝트 생성
       '/flow list': '/projects',     # 프로젝트 목록
       '/fp': '/project',            # 기존 fp 명령 통합
   }
   ```

2. **새로운 통합 명령어**
   ```bash
   /project [name]     # 프로젝트 전환 (Flow 자동 전환)
   /create [name]      # 새 프로젝트 생성
   /projects          # 전체 프로젝트 목록
   /status           # 현재 프로젝트/Flow 상태
   /archive [name]    # 프로젝트 아카이브
   ```

### Phase 4: 테스트 및 검증 (Day 5)
1. **기능 테스트**
   - [ ] 프로젝트 전환 테스트
   - [ ] Flow 자동 생성 테스트
   - [ ] 기존 명령어 호환성 테스트
   - [ ] Context 시스템 통합 테스트

2. **데이터 무결성 검증**
   - [ ] 모든 Flow가 프로젝트에 매핑됨
   - [ ] 모든 Task/Plan이 보존됨
   - [ ] Context 기록이 유지됨

## 🎯 예상 결과

### 사용자 경험 개선
```bash
# Before (복잡함)
$ fp ai-coding-brain-mcp        # 프로젝트 전환
$ wf "/flow ai-coding-brain-mcp" # Flow 찾기 (작동 안함)
$ # Flow와 프로젝트가 연결 안됨

# After (간단함)
$ /project ai-coding-brain-mcp   # 모든 것이 자동
$ # 프로젝트 전환 = Flow 전환 = Context 전환
```

### 데이터 구조 개선
```json
// Before: 분산된 데이터
{
  "flows.json": { /* Flow만 */ },
  "current_project.json": { /* 프로젝트만 */ },
  "current_flow.txt": "flow_id"
}

// After: 통합된 데이터
{
  "unified_system.json": {
    "projects": { /* 프로젝트 + Flow 연결 */ },
    "flows": { /* 모든 Flow */ },
    "current": { /* 현재 상태 */ }
  }
}
```

## ⚠️ 위험 요소 및 대응

| 위험 요소 | 영향도 | 대응 방안 |
|----------|-------|-----------|
| 데이터 손실 | 높음 | 3중 백업 시스템 |
| 기존 명령어 오류 | 중간 | 호환성 레이어 구현 |
| 성능 저하 | 낮음 | 캐싱 시스템 도입 |

## 📋 체크리스트

### 구현 전
- [ ] 전체 시스템 백업
- [ ] 테스트 환경 구축
- [ ] 롤백 계획 수립

### 구현 중
- [ ] 단계별 검증
- [ ] 로그 기록
- [ ] 실시간 모니터링

### 구현 후
- [ ] 통합 테스트
- [ ] 성능 측정
- [ ] 사용자 가이드 작성
