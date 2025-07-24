# Flow 중심 통합 명령어 체계 설계

## 🌊 /flow 명령어 체계

### 📋 기본 원칙
- **Flow = Project** (사용자에게는 Flow로 통일)
- 기존 /flow 명령어 확장
- 직관적이고 일관된 명령어 구조

### 🔧 핵심 명령어

#### 1. /flow [name] - Flow/프로젝트 전환
```bash
/flow ai-coding-brain-mcp
# → 프로젝트 디렉토리로 이동
# → 해당 Flow 활성화
# → Context 자동 전환

# 자동 완성 지원
/flow ai<TAB>  # → ai-coding-brain-mcp
```

#### 2. /flows - 전체 Flow 목록
```bash
/flows
# 출력 예시:
🌊 Flow 목록:
┌─────────────────────────┬──────────┬─────────┬─────────┐
│ Flow Name               │ Status   │ Plans   │ Tasks   │
├─────────────────────────┼──────────┼─────────┼─────────┤
│ 🟢 ai-coding-brain-mcp  │ Active   │ 4       │ 12      │
│ ⚪ another-project      │ Inactive │ 2       │ 5       │
│ 🔵 test-project         │ Archived │ 1       │ 3       │
└─────────────────────────┴──────────┴─────────┴─────────┘

# 필터 옵션
/flows --active     # 활성 Flow만
/flows --recent     # 최근 사용 순
/flows --archived   # 아카이브된 것 포함
```

#### 3. /flow create [name] - 새 Flow 생성
```bash
/flow create my-new-project
# → 바탕화면에 프로젝트 디렉토리 생성
# → 기본 구조 생성
# → Flow 자동 생성 및 전환

# 템플릿 옵션
/flow create my-app --template=react
/flow create my-api --template=fastapi
/flow create my-lib --template=python-package
```

#### 4. /flow status - 현재 상태
```bash
/flow status
# 출력:
🌊 Current Flow: ai-coding-brain-mcp
📂 Location: ~/Desktop/ai-coding-brain-mcp
📊 Statistics:
  - Plans: 4 (2 completed)
  - Tasks: 12 (5 completed, 3 in progress)
  - Progress: 42%
⏰ Last Activity: 5 minutes ago
📝 Context: 156 events recorded
```

#### 5. /flow delete [name] - Flow 삭제
```bash
/flow delete old-project
# → 확인 프롬프트
# → Flow 아카이브 (완전 삭제 X)
# → 디렉토리는 유지

/flow delete old-project --force
# → 완전 삭제 (주의!)
```

#### 6. /flow archive [name] - Flow 아카이브
```bash
/flow archive completed-project
# → Flow를 아카이브 상태로 변경
# → /flows에서 기본적으로 숨김
# → 언제든 복원 가능
```

#### 7. /flow restore [name] - Flow 복원
```bash
/flow restore archived-project
# → 아카이브에서 복원
# → 다시 활성 상태로
```

### 🎯 추가 편의 명령어

#### 단축 명령어
```bash
/f              # /flow의 별칭
/fs             # /flows의 별칭
/fc [name]      # /flow create의 별칭
```

#### 빠른 전환
```bash
/flow -         # 이전 Flow로 전환 (cd - 같은 개념)
/flow ..        # 상위 카테고리의 Flow로 (미래 기능)
```

#### 검색 및 필터
```bash
/flows python   # python이 포함된 Flow 검색
/flows /react   # 정규식 검색
/flows >10      # 10개 이상의 Task가 있는 Flow
```

### 📊 명령어 매핑 (기존 → 새로운)

| 기존 명령어 | 새 명령어 | 설명 |
|------------|----------|------|
| /project [name] | /flow [name] | Flow 전환 |
| /projects | /flows | 목록 보기 |
| /create [name] | /flow create [name] | 생성 |
| /fp [name] | /flow [name] | 기존 fp 대체 |
| - | /flow status | 상태 확인 |
| - | /flow archive | 아카이브 |
| - | /flow restore | 복원 |

### 💡 사용 시나리오

#### 시나리오 1: 새 프로젝트 시작
```bash
/flow create todo-app --template=react
# ✅ Created flow 'todo-app' with React template
# 📂 Location: ~/Desktop/todo-app
# 🌊 Switched to flow 'todo-app'

/plan add "프론트엔드 개발"
/plan add "백엔드 API"
/task add "React 컴포넌트 설계"
```

#### 시나리오 2: 프로젝트 전환
```bash
/flows
# ... 목록 확인 ...

/flow ai-coding-brain-mcp
# ✅ Switched to flow 'ai-coding-brain-mcp'
# 📂 Changed directory to ~/Desktop/ai-coding-brain-mcp
# 📊 4 plans, 12 tasks (42% complete)
```

#### 시나리오 3: 프로젝트 정리
```bash
/flow archive old-project-2023
# ✅ Flow 'old-project-2023' archived
# 💾 Data preserved in archives

/flows --archived  # 아카이브 포함 목록
```

### 🔧 구현 시 고려사항

1. **자동 완성**: Tab 키로 Flow 이름 자동 완성
2. **퍼지 매칭**: 정확한 이름 몰라도 검색 가능
3. **별칭 시스템**: 자주 쓰는 Flow에 별칭 설정
4. **히스토리**: 최근 사용한 Flow 우선 표시
5. **통합 검색**: Flow, Plan, Task 통합 검색

### ✨ 장점

1. **일관성**: 모든 것이 /flow로 시작
2. **직관성**: Flow라는 용어가 작업 흐름을 잘 표현
3. **확장성**: 추가 기능을 /flow 하위로 계속 추가 가능
4. **호환성**: 기존 /flow 사용자들이 자연스럽게 적응
