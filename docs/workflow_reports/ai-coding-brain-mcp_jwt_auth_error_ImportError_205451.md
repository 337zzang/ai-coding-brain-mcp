# 🔧 에러 수정 가이드

## 🚨 에러 정보
- **에러**: ImportError
- **발생 시각**: 2025-07-13 20:54:22
- **긴급도**: 높음 (코드 실행 불가)

## 💊 즉시 조치사항
```bash
# 1. JWT 패키지 설치
pip install PyJWT

# 2. 대안 패키지 (더 많은 기능)
pip install python-jose[cryptography]
```

## 🔍 상세 분석
### 에러 재현
```python
# python/api/auth/jwt_handler.py 라인 5
import jwt  # ModuleNotFoundError
```

### 원인
PyJWT 패키지가 설치되지 않았습니다. 
이는 프로젝트 의존성 관리에서 누락된 것으로 보입니다.

## ✅ 영구 수정
### requirements.txt 업데이트
```txt
# 인증 관련 패키지
PyJWT==2.8.0
cryptography==41.0.7
passlib==1.7.4
```

### 수정 코드
```python
# 파일: python/api/auth/jwt_handler.py
# 라인: 1-10

# 수정 전
import jwt
from datetime import datetime, timedelta

# 수정 후 (에러 처리 추가)
try:
    import jwt
except ImportError:
    print("PyJWT가 설치되지 않았습니다. 다음 명령을 실행하세요:")
    print("pip install PyJWT")
    raise

from datetime import datetime, timedelta
```

### 수정 사유
1. 명확한 에러 메시지로 문제 파악 용이
2. 설치 가이드 제공으로 빠른 해결
3. 의존성 문서화로 재발 방지

## 🧪 검증
### 단위 테스트
```python
def test_jwt_import():
    try:
        import jwt
        assert hasattr(jwt, 'encode')
        assert hasattr(jwt, 'decode')
        print("✅ JWT 모듈 정상 로드")
    except ImportError:
        print("❌ JWT 모듈 설치 필요")
```

## 📋 체크리스트
- [ ] PyJWT 패키지 설치
- [ ] requirements.txt 업데이트
- [ ] 에러 처리 코드 추가
- [ ] 테스트 통과 확인
- [ ] 다른 팀원에게 의존성 변경 공지

## ⚡ 배포 계획
1. 로컬 환경에서 패키지 설치 및 테스트
2. requirements.txt 커밋
3. CI/CD 파이프라인에서 자동 설치 확인

## 📊 모니터링
- 확인할 메트릭: 임포트 성공률
- 알림 설정: ImportError 발생 시 즉시 알림
