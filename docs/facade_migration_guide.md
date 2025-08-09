# Facade 패턴 마이그레이션 가이드

## 1. 단계별 전환 계획

### Phase 2-A Week 1: 프로토타입 (현재)
- facade.py 생성
- 네임스페이스 구조 설계
- 하위 호환성 레이어 구현

### Phase 2-A Week 2: 점진적 적용
```python
# __init__.py 수정
from .facade import get_facade

# 새로운 진입점
helpers = get_facade()

# 기존 export 유지 (deprecated)
from .file import read, write  # DeprecationWarning 추가
```

## 2. 사용자 전환 가이드

### 기존 코드 (Phase 1)
```python
import ai_helpers_new as h

content = h.read("file.txt")
h.write("output.txt", content)
h.git_commit("update")
```

### 새 코드 (Phase 2-A)
```python
import ai_helpers_new as h

# 구조화된 네임스페이스
content = h.file.read("file.txt")
h.file.write("output.txt", content)
h.git.commit("update")
```

### 전환 기간 (3개월)
- 기존 코드는 계속 작동 (DeprecationWarning만 발생)
- 새 코드는 네임스페이스 사용 권장
- 문서/예제는 새 방식으로 업데이트

## 3. 장점

### 개발자 경험
- **명확한 카테고리**: `h.file.*`, `h.code.*`
- **IDE 자동완성 개선**: 200개 → 10개씩 그룹
- **문서 구조화**: 카테고리별 문서

### 유지보수
- **내부 리팩토링 자유**: Facade 뒤에서 자유롭게 변경
- **API 버저닝**: 네임스페이스별 독립적 버전 관리
- **테스트 격리**: 카테고리별 독립 테스트

## 4. 예상 질문

### Q: 기존 코드를 꼭 바꿔야 하나요?
A: 아니요. 3-6개월간 기존 코드도 작동합니다. 단, 새 코드는 새 방식을 권장합니다.

### Q: 성능 영향은?
A: 거의 없습니다. 단순 참조 추가일 뿐입니다.

### Q: 언제 기존 API가 제거되나요?
A: 최소 6개월 후, 사용량 모니터링 후 결정합니다.
