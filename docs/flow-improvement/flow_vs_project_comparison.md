# 명령어 체계 비교: /project vs /flow

## 📊 비교표

| 기능 | /project 체계 | /flow 체계 | 
|------|--------------|------------|
| 전환 | `/project name` | `/flow name` |
| 목록 | `/projects` | `/flows` |
| 생성 | `/create name` | `/flow create name` |
| 상태 | `/status` | `/flow status` |
| 삭제 | `/delete name` | `/flow delete name` |
| 단축키 | 없음 | `/f`, `/fs` |

## 🌊 /flow 체계의 장점

### 1. **개념적 일관성**
- Flow는 "작업 흐름"을 의미 → 더 직관적
- 이미 사용 중인 개념 확장
- Plan, Task와 자연스럽게 연결

### 2. **명령어 일관성**
```bash
# 모든 것이 /flow로 시작
/flow                 # 현재 상태
/flow name           # 전환
/flow create         # 생성
/flow status         # 상세 상태
/flow archive        # 보관
```

### 3. **기존 사용자 친화적**
- 이미 /flow에 익숙한 사용자들
- 학습 곡선 최소화
- 자연스러운 확장

### 4. **확장성**
```bash
# 미래 기능 추가 용이
/flow clone          # Flow 복제
/flow merge          # Flow 병합
/flow branch         # Flow 분기
/flow template       # 템플릿 관리
```

### 5. **타이핑 효율성**
- `/f` 단축키 (2글자)
- `/flow` (5글자) vs `/project` (8글자)
- Tab 자동완성 더 빠름

## 💡 사용 시나리오 비교

### /project 체계
```bash
/project ai-coding-brain-mcp
/projects
/create new-app
/status
```

### /flow 체계 (더 직관적)
```bash
/flow ai-coding-brain-mcp
/flows
/flow create new-app
/flow status
```

## 🎯 결론

**/flow 체계를 채택하는 것이 더 좋은 이유:**

1. **통일성**: 모든 명령이 flow로 시작
2. **직관성**: Flow = 작업 흐름
3. **호환성**: 기존 시스템과 자연스럽게 통합
4. **효율성**: 더 짧고 빠른 명령어
5. **확장성**: 미래 기능 추가 용이

## 📝 마이그레이션 전략

```python
# 기존 명령어 자동 리다이렉트
LEGACY_MAPPING = {
    '/project': '/flow',
    '/projects': '/flows',
    '/fp': '/flow',
    '/create': '/flow create'
}

# 사용자가 기존 명령어 사용 시
# 1. 자동으로 새 명령어로 실행
# 2. 안내 메시지 표시
# "💡 Tip: /project는 이제 /flow로 사용하세요"
```
