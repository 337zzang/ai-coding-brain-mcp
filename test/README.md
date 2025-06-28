# Test Directory

이 디렉토리는 프로젝트의 모든 테스트 코드를 포함합니다.

## 구조

- `conftest.py` - pytest 공통 설정 및 fixture
- `test_*.py` - 각 모듈별 테스트 파일

## 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 파일만 실행
pytest test/test_example.py

# 상세 출력과 함께 실행
pytest -v

# 커버리지와 함께 실행
pytest --cov=.
```

## 테스트 작성 규칙

1. 모든 테스트 파일은 `test_` 접두사로 시작
2. 모든 테스트 함수는 `test_` 접두사로 시작
3. 관련 테스트는 클래스로 그룹화 가능
4. fixture는 conftest.py에 정의
