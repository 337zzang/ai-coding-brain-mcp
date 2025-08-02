# Task 4: 데이터 추출 기능 고도화 - 최종 설계 (v3)

## 📋 개요
- **목표**: 실무에서 가장 많이 사용되는 데이터 추출 패턴을 빠르고 안정적으로 지원
- **핵심 전략**: 즉시 가치 제공에 집중, Playwright 네이티브 API와 page.evaluate() 전략적 활용
- **예상 소요시간**: 2일

## 🏗️ 아키텍처 통합 방안 (명확화)

### 계층별 역할 분담
```
1. web_automation_helpers.py (사용자 인터페이스)
   └─> 2. web_automation_integrated.py (중간 관리자: 기록, 통합)
       └─> 3. web_automation_extraction.py (실무자: 실제 추출 로직)
```

### 역할 정의
1. **helpers**: 최종 사용자가 호출하는 간단한 인터페이스
   - `web_extract_batch()`, `web_extract_attributes()`, `web_extract_form()`

2. **integrated (REPLBrowserWithRecording)**: 
   - helpers의 요청을 받아 AdvancedExtractionManager 호출
   - 액션 기록 (recorder.record_action)
   - 에러 처리 통합

3. **extraction (AdvancedExtractionManager)**:
   - page 객체를 직접 받아 실제 추출 로직 수행
   - Locator API와 page.evaluate() 전략적 사용

## 📊 구현 우선순위 (실용주의적 재조정)

### 🔴 Phase 1: 핵심 기능 (Day 1)

#### 1. 배치 추출 (최우선 - 가장 큰 성능 향상)
```python
def web_extract_batch(configs: List[Dict]) -> Dict[str, Any]:
    """여러 요소를 단일 호출로 추출 - 300-500% 성능 향상"""
    # 단일 page.evaluate()로 모든 데이터 수집
    # 예: [
    #   {"selector": "h1", "name": "title", "type": "text"},
    #   {"selector": ".price", "name": "price", "type": "text", "transform": "float"}
    # ]
```

#### 2. 속성 추출 (실무 최다 사용)
```python
def web_extract_attributes(selector: str, attributes: List[str]) -> Dict[str, Any]:
    """여러 속성을 한번에 추출"""
    # Locator API 활용 (단일 요소일 때 효율적)
    # 예: web_extract_attributes(".product", ["id", "data-price", "data-sku"])
```

#### 3. 폼 데이터 추출 (로그인/회원가입 필수)
```python
def web_extract_form(form_selector: str) -> Dict[str, Any]:
    """폼의 모든 입력 필드 자동 수집"""
    # input, select, textarea, checkbox, radio 처리
    # name 속성 기반 자동 매핑
```

#### 4. extract_type 실제 구현 완성
- text, value, href, src, html (기존)
- attributes, data-* (신규)

### 🟡 Phase 2: 확장 기능 (Day 2)

#### 5. 고급 테이블 추출
```python
def web_extract_table_advanced(selector: str, options: Dict) -> Dict[str, Any]:
    """헤더 자동 인식, 데이터 타입 변환"""
    # auto_headers, convert_numbers 옵션
```

#### 6. 구조화 데이터 추출 (딕셔너리 기반)
```python
def web_extract_structured(selector: str, schema: Dict) -> Dict[str, Any]:
    """스키마 기반 복잡한 구조 추출"""
    # 반복되는 요소 자동 처리
```

### ⏸️ 연기/단순화 항목
- Locator 캐싱 → 추후 성능 이슈 시
- 스트리밍 추출 → 메모리 이슈 시
- 병렬 처리 → Phase 3
- 네트워크 JSON 캡처 → 별도 Task
- Chainable API → 장기 로드맵

## 🔧 핵심 구현 전략

### 1. Locator API vs page.evaluate() 전략적 사용
```python
class AdvancedExtractionManager:
    def extract_single(self, selector: str, extract_type: str):
        """단일 요소: Locator API 사용 (빠르고 안정적)"""
        locator = self.page.locator(selector)
        if extract_type == "text":
            return locator.text_content()
        elif extract_type == "value":
            return locator.input_value()
        # ...

    def extract_batch(self, configs: List[Dict]):
        """배치 추출: page.evaluate() 사용 (네트워크 왕복 최소화)"""
        js_function = """...(최적화된 JavaScript)..."""
        return self.page.evaluate(js_function, configs)
```

### 2. 에러 처리 통합
```python
# Task 2의 safe_execute 활용
@safe_execute(default_return={'ok': False, 'data': None})
def web_extract_batch(configs):
    # 구현...
```

### 3. 타입 변환 지원
```python
TRANSFORMERS = {
    'int': lambda x: int(re.sub(r'[^0-9-]', '', str(x))),
    'float': lambda x: float(re.sub(r'[^0-9.-]', '', str(x))),
    'bool': lambda x: str(x).lower() in ['true', '1', 'yes'],
    'json': lambda x: json.loads(x) if x else {}
}
```

## 📋 TODO 분해 (실행 가능한 단위)

### Day 1: 핵심 기능 구현
1. [ ] TODO #1: AdvancedExtractionManager 클래스 기본 구조 생성
2. [ ] TODO #2: extract_batch 핵심 로직 구현 (page.evaluate 최적화)
3. [ ] TODO #3: extract_attributes 구현 (Locator API 활용)
4. [ ] TODO #4: extract_form 구현 (모든 입력 타입 지원)
5. [ ] TODO #5: 타입 변환 시스템 구현
6. [ ] TODO #6: helpers.py에 새 함수 추가 및 통합
7. [ ] TODO #7: 기본 단위 테스트 작성

### Day 2: 확장 및 안정화
8. [ ] TODO #8: extract_type 미구현 옵션 완성
9. [ ] TODO #9: 고급 테이블 추출 구현
10. [ ] TODO #10: 에러 처리 및 재시도 로직
11. [ ] TODO #11: 성능 테스트 및 최적화
12. [ ] TODO #12: 문서화 및 사용 가이드

## ⚠️ 구현 시 주의사항
1. **배치 추출 안정성**: 가장 중요한 기능이므로 충분한 테스트
2. **하위 호환성**: 기존 API 동작에 영향 없도록
3. **메모리 관리**: 대량 추출 시 결과 크기 제한
4. **타입 안전성**: 변환 실패 시 원본 값 유지

## 🎯 성공 지표
- 배치 추출: 10개 요소 기준 300% 이상 성능 향상
- 속성 추출: 다중 속성 한 번에 추출 성공
- 폼 추출: HTML5 모든 입력 타입 지원
- 테스트 커버리지: 핵심 기능 90% 이상

## 📝 구현 노트
- Phase 1 완료 후 즉시 사용 가능한 가치 제공
- 복잡한 최적화는 실제 성능 병목 확인 후 진행
- 구조화 추출은 간단한 딕셔너리 스키마로 구현
