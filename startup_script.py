# q_tools 자동 로드 스크립트
import sys
import os

# python 폴더를 path에 추가
current_dir = os.getcwd()
python_path = os.path.join(current_dir, "python")
if python_path not in sys.path:
    sys.path.insert(0, python_path)

# q_tools 모든 함수 로드
try:
    from q_tools import *
    print("✅ q_tools 함수들이 자동으로 로드되었습니다!")
    print(f"📊 사용 가능한 q함수: {len([name for name in globals() if name.startswith('q') and callable(globals()[name])])}개")
    print("🚀 이제 qp(), ql(), qv() 등을 바로 사용할 수 있습니다!")
except Exception as e:
    print(f"❌ q_tools 로드 실패: {e}")
