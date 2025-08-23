# Web 모듈 통합 전략

## 1. 현황 분석

### Web Core 모듈
- `python/ai_helpers_new/web_new.py` (10.7 KB) - 메인 구현
- `python/ai_helpers_new/web.py` (582 bytes) - 거의 빈 파일
- `python/ai_helpers_new/web/` - 모듈화된 구조

### Browser Overlay Automation
- 독립적이고 완성도 높은 모듈
- AI 통합, 패턴 분석 등 고급 기능 포함
- 테스트 코드 포함

### 백업 및 중복 파일
- 4개의 .backup 파일
- improved_web_automation 버전들
- 구버전 overlay_automation.py

## 2. 통합 전략

### Phase 1: 정리 (10분)
1. 백업 파일 제거
2. 빈 파일 삭제
3. 중복 파일 백업 후 제거

### Phase 2: 통합 (30분)
1. web_new.py와 web/__init__.py 통합
   - 중복 함수 제거
   - 단일 진입점 생성

2. Overlay 버전 통합
   - v2를 메인으로 설정
   - v1 고유 기능만 이식

### Phase 3: 구조화 (2시간)
1. browser_overlay_automation을 web/overlay/로 이동
2. 통합 API 생성
3. 테스트 작성

## 3. 위험 관리

### 잠재 위험
- 기존 코드 의존성 파괴
- API 호환성 문제
- 테스트 부재로 인한 회귀

### 완화 방안
- 모든 변경사항 백업
- 단계별 테스트
- 롤백 계획 수립
