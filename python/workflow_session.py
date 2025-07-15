# REPL 세션용 통합 워크플로우 래퍼
import os
import sys

# python 디렉토리를 path에 추가
python_path = os.path.join(os.getcwd(), 'python')
if python_path not in sys.path:
    sys.path.insert(0, python_path)

# ai_helpers_v2 경로 추가
helpers_path = os.path.join(python_path, 'ai_helpers_v2')
if helpers_path not in sys.path:
    sys.path.insert(0, helpers_path)

# 통합 워크플로우 임포트
try:
    from integrated_workflow_protocol import flow_project, run_workflow, init_workflow
    print("✅ 통합 워크플로우 로드 완료")
except ImportError as e:
    print(f"❌ 통합 워크플로우 로드 실패: {e}")
    flow_project = None
    run_workflow = None
    init_workflow = None

# AI Helpers v2 직접 임포트
try:
    import ai_helpers_v2 as helpers
    print("✅ AI Helpers v2 로드 완료")
except ImportError as e:
    print(f"❌ AI Helpers v2 로드 실패: {e}")
    helpers = None
