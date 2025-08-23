# Web 모듈 통합 구현 계획

## 📅 실행 일정

### Day 1: 즉시 정리 (10분)
```bash
# 백업 디렉토리 생성
mkdir -p backups/web_backups_20250823

# 백업 파일 이동
mv python/ai_helpers_new/web.py.backup* backups/web_backups_20250823/
mv improved_web_automation_backup_*.py backups/web_backups_20250823/

# 빈 파일 제거
rm python/ai_helpers_new/web.py
```

### Day 2: 모듈 통합 (30분)

#### Step 1: Web Core 통합
```python
# web_new.py를 메인으로 설정
# web/__init__.py의 고유 기능만 이식

1. 중복 함수 목록 작성
2. web_new.py에 없는 기능만 추가
3. import 경로 통일
```

#### Step 2: Overlay 통합
```python
# overlay_automation_v2.py를 메인으로
# v1의 고유 기능 이식

1. 기능 비교 분석
2. v2에 없는 v1 기능 추가
3. 테스트 실행
```

### Day 3: 구조 개선 (2시간)

#### 새로운 구조
```
python/ai_helpers_new/web/
├── __init__.py          # 통합 API
├── browser.py           # 브라우저 관리
├── session.py           # 세션 관리
├── overlay/             # overlay_automation 이동
│   ├── __init__.py
│   ├── automation.py
│   ├── ai_integration/
│   └── security/
└── tests/              # 통합 테스트
```

## 🧪 테스트 계획

### 단위 테스트
- 각 모듈별 기능 테스트
- 중복 제거 후 동일성 검증

### 통합 테스트
- 전체 워크플로우 테스트
- API 호환성 테스트

### 성능 테스트
- 리팩토링 전/후 비교
- 메모리 사용량 측정

## 📊 성공 지표

- ✅ 파일 수 40% 감소
- ✅ 코드 중복 80% 제거
- ✅ 테스트 커버리지 90% 달성
- ✅ 성능 저하 5% 미만
