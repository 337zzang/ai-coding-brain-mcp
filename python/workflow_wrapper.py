"""
WorkflowV2 Wrapper - helpers와의 완전한 통합
"""
import sys
import os

# workflow 모듈 경로 추가
workflow_path = os.path.join(os.path.dirname(__file__), 'workflow')
if workflow_path not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

# workflow 모듈 import
try:
    # Python 경로에 추가
    import sys
    import os
    if 'python' not in sys.path:
        sys.path.insert(0, 'python')

    # workflow 모듈에서 필요한 것들 import
    from workflow import task, done, status, report
    from workflow.manager import WorkflowV2Manager
    from workflow.integration import workflow_integrated

    # manager 인스턴스 생성 (필요한 경우)
    _manager = None

    def start():
        """다음 태스크 시작"""
        global _manager
        if _manager is None:
            _manager = WorkflowV2Manager()
        return _manager.start_next_task() if hasattr(_manager, 'start_next_task') else "태스크를 시작합니다"

    def wf(cmd):
        """워크플로우 명령 실행"""
        return workflow_integrated(cmd)

    # 전역으로 노출
    globals().update({
        'wf_task': task,
        'wf_start': start,
        'wf_done': done,
        'wf_status': status,
        'wf_report': report,
        'wf': wf,
        'workflow': workflow_integrated
    })

    _workflow_loaded = True
    print("✅ WorkflowV2 로드 성공")

except Exception as e:
    print(f"⚠️ WorkflowV2 로드 실패: {e}")
    import traceback
    traceback.print_exc()
    _workflow_loaded = False
# helpers 메서드로 추가
class WorkflowHelpers:
    """helpers 객체에 추가할 workflow 메서드들"""

    @staticmethod
    def wf_task(name: str, tags: list = None) -> str:
        """태스크 추가"""
        if _workflow_loaded:
            return task(name, tags)
        return "❌ WorkflowV2가 로드되지 않았습니다"

    @staticmethod
    def wf_start() -> str:
        """다음 태스크 시작"""
        if _workflow_loaded:
            return start()
        return "❌ WorkflowV2가 로드되지 않았습니다"

    @staticmethod
    def wf_done(summary: str = None) -> str:
        """현재 태스크 완료"""
        if _workflow_loaded:
            return done(summary)
        return "❌ WorkflowV2가 로드되지 않았습니다"

    @staticmethod
    def wf_status() -> str:
        """워크플로우 상태"""
        if _workflow_loaded:
            return status()
        return "❌ WorkflowV2가 로드되지 않았습니다"

    @staticmethod
    def wf_report() -> str:
        """워크플로우 리포트"""
        if _workflow_loaded:
            return report()
        return "❌ WorkflowV2가 로드되지 않았습니다"

    @staticmethod
    def workflow(command: str) -> str:
        """통합 워크플로우 명령어"""
        if _workflow_loaded:
            return workflow_integrated(command)
        return "❌ WorkflowV2가 로드되지 않았습니다"

# 자동 추적을 위한 헬퍼 후크
def hook_file_creation(original_func):
    """파일 생성 함수 후크"""
    def wrapper(path, *args, **kwargs):
        result = original_func(path, *args, **kwargs)
        if _workflow_loaded and result:
            try:
                auto_track_file_creation(path)
            except:
                pass
        return result
    return wrapper

def hook_git_commit(original_func):
    """Git 커밋 함수 후크"""
    def wrapper(*args, **kwargs):
        result = original_func(*args, **kwargs)
        if _workflow_loaded and result:
            try:
                auto_track_git_commit()
            except:
                pass
        return result
    return wrapper

# REPL에서 사용하기 쉽도록 짧은 함수명 제공
def wt(name: str, tags: list = None):
    """워크플로우 태스크 추가 (짧은 버전)"""
    return task(name, tags) if _workflow_loaded else "❌ WorkflowV2 미로드"

def ws():
    """워크플로우 상태 (짧은 버전)"""
    return status() if _workflow_loaded else "❌ WorkflowV2 미로드"

def wd(summary: str = None):
    """워크플로우 완료 (짧은 버전)"""
    return done(summary) if _workflow_loaded else "❌ WorkflowV2 미로드"

print(f"✅ WorkflowV2 Wrapper 로드 {'성공' if _workflow_loaded else '실패'}")
