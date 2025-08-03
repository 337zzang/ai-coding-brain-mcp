
# 🌐 웹 자동화 모듈 구조 개선 최종 설계

## 📋 개요
O3와 Claude의 병렬 분석을 통해 웹 자동화 모듈의 구조 개선 방향을 확정했습니다. 
Phase 1-3에서 발견된 .h.append 버그가 BrowserManager에도 존재하며, 이미 부분적인 통합이 진행되어 있음을 확인했습니다.

## 🔍 주요 발견사항

### 1. 치명적 버그 발견
- **BrowserManager Line 82**: `instances.h.append` → `instances.append` 수정 필요
- Phase 1과 동일한 패턴의 오류

### 2. 이미 진행된 통합
- ai_helpers_new가 이미 19개 web 함수를 import 중
- 전역 변수 _web_instance는 BrowserManager로 점진적 마이그레이션 중

### 3. 순환 의존성 위험
- web 모듈이 Flow 기능을 호출할 경우 순환 의존 발생
- 런타임 import 또는 의존성 역전 필요

## 📐 수정된 구현 계획

### Phase 1: 긴급 버그 수정 및 준비 (30분)
#### TODO
1. BrowserManager의 .h.append 버그 수정
2. list_instances 메서드 동작 검증
3. 단위 테스트 작성

### Phase 2: 전역 변수 단계적 제거 (2시간)
#### 2단계 접근법
1. **Stage 1 (Soft Deprecation)**
   - _get_web_instance()가 BrowserManager 우선, 전역 변수 폴백
   - _set_web_instance()가 양쪽 모두 업데이트
   - Deprecation 경고 추가

2. **Stage 2 (완전 제거)**
   - 모든 web_* 함수에서 BrowserManager 직접 호출
   - 전역 변수 완전 제거
   - 테스트 격리성 확보

#### TODO
1. _get/_set_web_instance 함수 수정 (Soft Deprecation)
2. 60개 호출 지점 점진적 마이그레이션
3. BrowserManager에 close_instance() 메서드 추가
4. WeakValueDictionary 고려 (메모리 누수 방지)
5. 전체 테스트 실행 및 검증

### Phase 3: AI Helpers 통합 완성 (1시간)
#### 접근 방법
- **Option A 채택**: 기존 import 구조 활용
- 이미 import된 19개 함수 유지
- 누락된 5개 함수 추가 (총 24개)

#### TODO
1. 누락된 web_* 함수 확인 및 추가
2. __all__ 리스트 업데이트
3. 문서 업데이트 (h.web_* 사용법)
4. 호환성 테스트

### Phase 4: 프로젝트 경로 통합 (1시간)
#### 목표
- 스크린샷/다운로드를 프로젝트별 폴더에 저장
- Flow 시스템과 일관된 경로 구조

#### TODO
1. ContextualPathProvider 유틸리티 클래스 생성
2. web_screenshot() 함수 개선
   - 기본: `{project}/.ai-brain/screenshots/`
   - 폴백: `./screenshots/`
3. 순환 의존 방지를 위한 런타임 import
4. 경로 마이그레이션 가이드 작성

## 🛡️ 위험 관리

### 1. 순환 의존성 방지
```python
# ❌ 위험: 최상위 import
from ai_helpers_new import get_current_project

# ✅ 안전: 함수 내부 import
def get_screenshot_path():
    from ai_helpers_new import get_current_project
    project = get_current_project()
    ...
```

### 2. 스레드 안전성
- BrowserManager와 REPLBrowser의 락 순서 문서화
- 데드락 방지를 위한 타임아웃 설정

### 3. 호환성 유지
- 기존 web_* 함수 시그니처 유지
- Deprecation 기간 최소 2개월
- 마이그레이션 가이드 제공

## 📊 검증 계획

### 단위 테스트
1. BrowserManager 싱글톤 동작
2. 전역 변수 제거 후 기능 동작
3. 프로젝트 경로 해석

### 통합 테스트
1. 웹 자동화 전체 시나리오
2. 다중 프로젝트 전환
3. 에러 복구 시나리오

### 성능 테스트
1. BrowserManager.get_instance() 오버헤드
2. 메모리 누수 검증

## 📅 일정
- **Day 1**: Phase 1-2 (긴급 수정 + 전역 변수 제거)
- **Day 2**: Phase 3-4 (통합 완성 + 경로 시스템)
- **Day 3**: 테스트 및 문서화

## ✅ 예상 효과
1. **즉시 효과**: .h.append 버그 수정으로 안정성 확보
2. **단기 효과**: 전역 상태 제거로 테스트 용이성 증가
3. **장기 효과**: 확장 가능한 구조, 멀티 브라우저 지원 가능

## 🚀 Plan 생성 준비 완료

### Plan: 웹 자동화 모듈 구조 개선
- **Task 1**: 긴급 버그 수정 및 준비 (30분)
- **Task 2**: 전역 변수 단계적 제거 (2시간)
- **Task 3**: AI Helpers 통합 완성 (1시간)
- **Task 4**: 프로젝트 경로 통합 (1시간)

**총 예상 시간**: 4.5시간

이 설계대로 Plan을 생성하시겠습니까? (Y/N)
