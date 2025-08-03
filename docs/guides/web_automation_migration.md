
# 웹 자동화 전역 변수 제거 마이그레이션 가이드

## 변경 사항
- `_web_instance` 전역 변수가 제거되었습니다
- 모든 브라우저 인스턴스는 BrowserManager를 통해 관리됩니다

## 마이그레이션 방법

### 이전 코드
```python
global _web_instance
if _web_instance:
    _web_instance.goto(url)
```

### 새 코드
```python
instance = _get_web_instance()
if instance:
    instance.goto(url)
```

## 주요 변경점
1. 전역 변수 직접 접근 금지
2. 항상 `_get_web_instance()` 사용
3. BrowserManager가 모든 인스턴스 관리

## 테스트
- 모든 web_* 함수는 기존과 동일하게 작동
- 내부적으로 BrowserManager 사용
- 스레드 안전성 향상

## 추가된 기능
- `BrowserManager.close_instance()`: 안전한 브라우저 종료
- 프로젝트별 브라우저 관리 지원
