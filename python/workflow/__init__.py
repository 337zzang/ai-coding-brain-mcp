"""
WorkflowV2 시스템 - 체계적인 작업 관리 및 추적
"""

# 편의를 위한 함수들을 먼저 정의
def task(name: str, tags: list = None):
    """태스크 추가"""
    from .integration import v2_task
    return v2_task(name, tags)

def start():
    """다음 태스크 시작"""
    from .integration import v2_start
    return v2_start()

def done(summary: str = None):
    """현재 태스크 완료"""
    from .integration import v2_done
    return v2_done(summary)

def status():
    """상태 확인"""
    from .integration import v2_status
    return v2_status()

def report():
    """리포트 생성"""
    from .integration import v2_report
    return v2_report()

def wf(command: str):
    """워크플로우 명령어"""
    from .helper import workflow_v2
    return workflow_v2(command)

def init():
    """WorkflowV2 초기화"""
    from .helper import init_workflow_v2
    return init_workflow_v2()

def check_v2_files():
    """v2 파일 위치 확인"""
    from .integration import check_v2_files as _check
    return _check()

def help():
    """WorkflowV2 사용법 안내"""
    return """
📚 WorkflowV2 사용법

1. 기본 사용:
   from workflow import task, start, done, status, report

   task("작업명", ["태그1", "태그2"])  # 태스크 추가
   start()                              # 다음 태스크 시작
   done("완료 요약")                    # 현재 태스크 완료
   status()                             # 상태 확인
   report()                             # 전체 리포트

2. 명령어 방식:
   from workflow import wf

   wf("task add 작업명 #태그1 #태그2")
   wf("task list")
   wf("start 1")
   wf("complete 1 작업 완료")
   wf("search 키워드")
   wf("help")

3. 자동 추적:
   파일 생성/수정과 Git 커밋이 자동으로 추적됩니다.

4. 데이터 위치:
   memory/workflow_v2.json
"""

# 필요시 명시적으로 import할 수 있도록
__all__ = [
    'task', 'start', 'done', 'status', 'report', 'wf', 'init', 'help', 'check_v2_files'
]

# 자동 초기화 시도 (오류 무시)
try:
    init()
    print("✅ WorkflowV2 자동 초기화 성공")
except:
    pass  # 조용히 무시
