
## 📋 웹 자동화 단순 통합 - 실행 계획

### Phase 1: 준비 (즉시 실행)
```bash
# 1. 백업
python -c "
import shutil, datetime
backup_dir = f'backups/web_{datetime.datetime.now():%Y%m%d_%H%M}'
shutil.copytree('api', f'{backup_dir}/api')
shutil.copytree('python/api', f'{backup_dir}/python_api')
"

# 2. 폴더 생성
mkdir python/web_automation
```

### Phase 2: 파일 이동 및 수정
1. **browser.py 생성**
   - api/browser_manager.py 복사
   - SessionRegistry 클래스 통합
   - WebAutomation 래퍼 추가

2. **helpers.py 생성**
   - python/api/web_automation_helpers.py 복사
   - import 경로 수정
   - 불필요한 의존성 제거

3. **errors.py 생성**
   - python/api/web_automation_errors.py 복사
   - 새 에러 타입 추가

4. **__init__.py 작성**
   - 공개 API 정의
   - 하위 호환성 별칭

### Phase 3: 테스트
```python
# 테스트 스크립트
from python.web_automation import WebAutomation

web = WebAutomation("test_session")
web.start(headless=True)
web.goto("https://example.com")
title = web.extract("title")
print(f"Title: {title}")
web.close()
```

### Phase 4: 정리
- 테스트 통과 후 기존 폴더 제거
- 문서 업데이트
- Git 커밋

### 예상 결과
- **파일 수**: 99개 → 5개
- **코드 양**: 99KB → 약 70KB
- **복잡도**: 대폭 감소
- **성능**: 동일 또는 향상

### 위험 요소
- import 경로 변경 필요
- 일부 내부 함수 조정 필요
- 테스트 커버리지 확보 필수
