#!/usr/bin/env python3
"""
FastAPI 사용자 관리 API 실행 스크립트
"""
import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from api.users import app
    import uvicorn

    if __name__ == "__main__":
        print("🚀 FastAPI 사용자 관리 API 시작 중...")
        print("📝 API 문서: http://localhost:8000/docs")
        print("🔍 ReDoc 문서: http://localhost:8000/redoc")
        print("❤️ 헬스체크: http://localhost:8000/health")
        print("👥 사용자 API: http://localhost:8000/api/users")

        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            reload=True,
            log_level="info"
        )

except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("💡 다음 명령어로 의존성을 설치하세요:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ 서버 시작 오류: {e}")
    sys.exit(1)
