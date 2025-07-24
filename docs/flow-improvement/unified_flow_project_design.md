# Flow-Project 통합 관리 시스템 설계

## 🎯 설계 목표

### 1. 개념 통합
- **핵심 원칙**: 1 Project = 1 Primary Flow
- 프로젝트 디렉토리와 Flow가 1:1 매핑
- 프로젝트 전환 = Flow 전환

### 2. 데이터 구조 통합
```json
{
  "projects": {
    "ai-coding-brain-mcp": {
      "path": "C:\Users\Administrator\Desktop\ai-coding-brain-mcp",
      "type": "node",
      "primary_flow_id": "flow_xxx",
      "metadata": {
        "created_at": "2025-07-23",
        "last_accessed": "2025-07-23"
      }
    }
  },
  "flows": {
    "flow_xxx": {
      "id": "flow_xxx",
      "project_name": "ai-coding-brain-mcp",
      "project_path": "C:\Users\Administrator\Desktop\ai-coding-brain-mcp",
      "plans": {},
      "is_primary": true
    }
  },
  "current": {
    "project": "ai-coding-brain-mcp",
    "flow_id": "flow_xxx"
  }
}
```

## 📐 상세 설계

### 1. 통합 매니저 클래스
```python
class UnifiedProjectFlowManager:
    def __init__(self):
        self.data_file = '.ai-brain/unified_system.json'
        self.load()

    def switch_project(self, project_name: str):
        '''프로젝트 전환 = Flow 전환'''
        # 1. 프로젝트 디렉토리 찾기 (바탕화면)
        # 2. 디렉토리 이동
        # 3. Primary Flow 활성화 또는 생성
        # 4. Context 기록

    def create_project_flow(self, project_name: str):
        '''새 프로젝트 = 새 Flow 자동 생성'''
        # 1. 프로젝트 디렉토리 생성
        # 2. Primary Flow 생성
        # 3. 기본 Plan 템플릿 생성

    def get_current_context(self):
        '''현재 프로젝트/Flow 컨텍스트'''
        return {
            'project': self.current_project,
            'flow': self.current_flow,
            'path': os.getcwd()
        }
```

### 2. 명령어 체계 통합
```bash
# 기존 명령어들을 통합
/project [name]     → 프로젝트/Flow 전환
/create [name]      → 프로젝트/Flow 생성
/status            → 현재 상태 (프로젝트 + Flow)
/plan              → 현재 프로젝트의 Plan
/task              → 현재 프로젝트의 Task
```

### 3. 자동 매핑 시스템
```python
class AutoMapper:
    @staticmethod
    def detect_project():
        '''현재 디렉토리에서 프로젝트 자동 감지'''
        current_dir = os.getcwd()
        project_name = os.path.basename(current_dir)
        return project_name

    @staticmethod
    def ensure_flow_exists(project_name):
        '''프로젝트에 Flow가 없으면 자동 생성'''
        if not has_primary_flow(project_name):
            create_primary_flow(project_name)
```

### 4. 마이그레이션 전략
```python
def migrate_to_unified_system():
    '''기존 데이터를 통합 시스템으로 마이그레이션'''
    # 1. 기존 flows.json 읽기
    # 2. current_project.json 읽기
    # 3. 통합 데이터 구조로 변환
    # 4. unified_system.json 생성
    # 5. 백업 생성
```

## 🛠️ 구현 계획

### Phase 1: 데이터 구조 통합
- [ ] UnifiedData 클래스 구현
- [ ] 마이그레이션 스크립트 작성
- [ ] 백업 시스템 구현

### Phase 2: 통합 매니저 구현
- [ ] UnifiedProjectFlowManager 클래스
- [ ] 자동 매핑 시스템
- [ ] Context 통합

### Phase 3: 명령어 시스템 개선
- [ ] 통합 명령어 처리기
- [ ] 기존 명령어 호환성 유지
- [ ] 새로운 단축 명령어

### Phase 4: UI/UX 개선
- [ ] 상태 표시 개선
- [ ] 프로젝트 목록 표시
- [ ] 시각적 피드백

## 📊 예상 결과

### Before (현재)
```
프로젝트 정보 → ~/.ai-coding-brain/cache/current_project.json
Flow 정보 → .ai-brain/flows.json
연결 안됨, 수동 관리 필요
```

### After (통합 후)
```
통합 정보 → .ai-brain/unified_system.json
프로젝트 = Flow (자동 연결)
프로젝트 전환 시 Flow 자동 전환
```

## ⚠️ 주의사항

1. **기존 데이터 보존**: 마이그레이션 시 백업 필수
2. **호환성**: 기존 명령어는 계속 작동해야 함
3. **성능**: 파일 I/O 최소화
4. **확장성**: 향후 멀티 Flow per Project 고려

## 🎯 핵심 이점

1. **단순화**: 프로젝트와 Flow 개념 통합
2. **자동화**: 프로젝트 전환 시 모든 것이 자동
3. **일관성**: 하나의 통합된 데이터 구조
4. **Context**: 모든 작업이 자동으로 기록됨
