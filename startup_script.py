"""
AI Coding Brain MCP - Startup Script
프로젝트 시작 시 자동으로 실행되는 스크립트
"""

print("🚀 AI Coding Brain MCP 시작...")

# Flow Project 개선 적용
try:
    from flow_project_fix import patch_helpers
    if 'helpers' in globals():
        helpers = patch_helpers(helpers)
        fp = helpers.flow_project
        print("✅ flow_project 개선 적용 완료")
    else:
        print("⚠️ helpers 객체를 찾을 수 없음")
except ImportError:
    print("⚠️ flow_project_fix.py를 찾을 수 없음")
except Exception as e:
    print(f"⚠️ flow_project 패치 오류: {e}")
    import traceback
    traceback.print_exc()

# 워크플로우 시스템 초기화
try:
    from workflow_wrapper import wf
    print("✅ 워크플로우 시스템 준비 완료")
except ImportError:
    print("⚠️ workflow_wrapper를 찾을 수 없음")

# 현재 프로젝트 표시
try:
    if 'helpers' in globals():
        current = helpers.get_current_project()
        if current:
            print(f"\n📂 현재 프로젝트: {current.get('name', 'Unknown')}")
            print(f"📍 경로: {current.get('path', 'Unknown')}")
except:
    pass

print("\n✅ 시작 완료!\n")
