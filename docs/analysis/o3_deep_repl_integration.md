# JSON REPL Session 통합 - O3 상세 분석

## O3 분석 결과
아래 답변은  
① json_repl_session.execute_code 를 “한 군데만” 고치면 전체 요구사항이 자동으로 충족되도록 설계하고  
② TaskLogger + Sub-process Worker를 옵션으로 켜거나 끌 수 있게 구성하며  
③ Flow API(Plan/Task) 와 연결하여 실행-히스토리(JSONL) 를 남기는 “끝-까지-동작” 예시 코드를 포함합니다.  

────────────────────────────────────────
0.  전체 아키텍처 요약
────────────────────────────────────────
• json_repl_session.py  
  └─ Session(=메인 프로세스)  
       └─ execute_code() – 필수 수정 부분  
            · 코드 실행 경로 결정  
            · 실행 전/후 컨텍스트 diff 계산  
            · Worker Process 와 통신(선택)  
            · EnhancedTaskLogger 로 ❶ 로그 작성, ❷ 히스토리 파일 flush  

• repl_kernel/manager.py  
  (간단한 queue-based runner. 이미 존재 → 그대로 사용)

• repl_kernel/worker.py  
  (고립된 파이썬 프로세스. globals 유지 → 세션 상태는 worker 쪽에서 지속)

환경변수
  USE_SUBPROCESS_WORKER = { "0" | "1" }            (기본:0, 1 이면 worker 사용)
  FLOW_PLAN_ID          = "P-xxxx"                 – Flow 백엔드가 주입
  FLOW_TASK_ID          = "T-xxxx"
  FLOW_TASK_NAME        = "user login bug fix"     (가독용)

────────────────────────────────────────
1.  EnhancedTaskLogger 1-회 초기화
────────────────────────────────────────
json_repl_session.py 모듈 레벨에서

from task_logger import EnhancedTaskLogger, normalize_task_name

PLAN_ID  = os.getenv("FLOW_PLAN_ID")  or "local"
TASK_ID  = os.getenv("FLOW_TASK_ID")  or "unknown"
TNAME    = os.getenv("FLOW_TASK_NAME") or "adhoc"

LOGGER   = EnhancedTaskLogger(
             plan_id      = PLAN_ID,
             task_number  = int(TASK_ID.split("-")[-1]) if TASK_ID.startswith("T-") else 0,
             task_name    = normalize_task_name(TNAME)
           )

logger 인스턴스는 세션-전역으로 한번만 만들어 둡니다.

────────────────────────────────────────
2.  execute_code() 수정 포인트
────────────────────────────────────────
(1) 실행 경로 선택  
    use_worker = os.getenv("USE_SUBPROCESS_WORKER", "0") == "1"

(2) 실행 전 스냅샷  
    pre_vars    = set(repl_globals.keys())
    pre_imports = set(sys.modules.keys())
    t0 = time.perf_counter()

(3-A) 메인 프로세스 실행 (=기존 코드)  
      result = _run_locally(code)

(3-B) Worker 경로  
      result = manager.run_in_worker(code)

(4) 실행 후 스냅샷 / diff  
    t1          = time.perf_counter()
    post_vars   = set(repl_globals.keys())   # 로컬 실행이면 세션 globals 가 변함
    post_import = set(sys.modules.keys())

    added_vars  = sorted(post_vars   - pre_vars)
    added_imps  = sorted(post_import - pre_imports)

(5) JSONL 로그 작성  
    log_line = {
        "plan_id"       : PLAN_ID,
        "task_id"       : TASK_ID,
        "timestamp"     : datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "elapsed_ms"    : round((t1 - t0)*1000, 2),
        "code"          : code,
        "stdout"        : result["stdout"],
        "stderr"        : result["stderr"],
        "success"       : result["success"],
        "added_vars"    : added_vars,
        "added_imports" : added_imps
    }
    LOGGER.write(log_line)      # EnhancedTaskLogger 가 한 줄씩 append & flush

(6) result["debug_info"] 에 diff 를 넣어 REPL 프런트에도 노출  
    result["debug_info"].update({
        "added_vars"    : added_vars,
        "added_imports" : added_imps,
        "elapsed_ms"    : log_line["elapsed_ms"]
    })

────────────────────────────────────────
3.  Worker 통신(manager.run_in_worker) 예시
────────────────────────────────────────
def run_in_worker(code:str) -> dict:
    """
    manager.py 내부 함수 예시.
    1) 이미 fork 된 worker 있으면 pipe 로 전송
    2) 없으면 subprocess.Popen(["python", "-m", "repl_kernel.worker"])
    3) JSON {code:<str>} 보내고 stdout 받은 뒤 json.loads 로 결과 반환
    4) worker 가 죽으면 재시작하여 오류 복구
    """
    ...

json 스펙은 메인-실행 결과 dict 와 동일하게 맞춰 두면
execute_code() 쪽 추가 분기 필요 없음.

────────────────────────────────────────
4.  Error Handling & 복구 전략
────────────────────────────────────────
• execute_code() 레벨에서 예외가 올라오면:
    ① result["success"]=False, stderr 에 traceback 추가  
    ② LOGGER.write() 는 try/except 로 감싸서 “로깅-실패가 REPL 를 죽이지 않게”

• Worker 경로 실패 시
    manager.run_in_worker ⇒ CalledProcessError or Timeout
        → worker 프로세스 kill & 신규 spawn,  
        → result = {success:False, stdout:"", stderr:"worker crash …"}

• 로컬 실행 실패(ImportError 등) 도 동일 포맷으로 전달 → 한 곳에서 공통 로깅.

────────────────────────────────────────
5.  성능 영향 최소화
────────────────────────────────────────
• logger.write() 내부에서
    with open(self.path, "a", buffering=1)  # line-buffered
  를 이용 → flush 비용 최소.

• diff 계산은 set 연산 O(n). n ≃ 수백 개 수준이므로 무시 가능.

• USE_SUBPROCESS_WORKER=1 이더라도
    – worker 를 keep-alive 하여 재사용(커다란 import 를 한 번만 하도록)  
    – 큰 stdout/stderr 는 64 KB 단위 chunk 로 전달 (manager/worker 가 이미 구현)

────────────────────────────────────────
6.  최종 patch (execute_code 핵심부) – 축약 예시
────────────────────────────────────────
import os, sys, json, traceback, time
from datetime import datetime
from repl_kernel import manager     # worker manager
from task_logger import LOGGER

def execute_code(code:str) -> dict:
    global repl_globals
    use_worker = os.getenv("USE_SUBPROCESS_WORKER","0") == "1"

    pre_vars, pre_mod = set(repl_globals), set(sys.modules)
    t0 = time.perf_counter()

    try:
        if use_worker:
            result = manager.run_in_worker(code)
        else:
            result = _run_locally(code)    # 기존 내부 함수

    except Exception as e:
        result = {
            "success": False,
            "stdout" : "",
            "stderr" : f"❌ Runtime Error: {type(e).__name__}: {e}\n" + traceback.format_exc(),
            "debug_info": {"execution":"error"}
        }

    t1 = time.perf_counter()
    added_vars  = sorted(set(repl_globals) - pre_vars)
    added_imps  = sorted(set(sys.modules)   - pre_mod)

    result.setdefault("debug_info",{}).update({
        "added_vars"   : added_vars,
        "added_imports": added_imps,
        "elapsed_ms"   : round((t1-t0)*1000,2)
    })

    # ---------- JSONL Log ----------
    try:
        LOGGER.write({
            "plan_id"      : PLAN_ID,
            "task_id"      : TASK_ID,
            "timestamp"    : datetime.utcnow().isoformat(timespec="milliseconds")+"Z",
            "elapsed_ms"   : result["debug_info"]["elapsed_ms"],
            "code"         : code,
            "stdout"       : result.get("stdout",""),
            "stderr"       : result.get("stderr",""),
            "success"      : result["success"],
            "added_vars"   : added_vars,
            "added_imports": added_imps
        })
    except Exception as log_err:
        print(f"[TaskLogger-ERROR] {log_err}", file=sys.stderr)

    return result

────────────────────────────────────────
7.  Flow 시스템에서 Plan/Task ID 전달 방식
────────────────────────────────────────
Flow 백엔드가 REPL 세션을 띄울 때

env = os.environ.copy()
env.update({
    "FLOW_PLAN_ID"  : plan.id,
    "FLOW_TASK_ID"  : task.id,
    "FLOW_TASK_NAME": task.title,           # UI 표기 제목
    "USE_SUBPROCESS_WORKER": "1"            # 필요 시
})
subprocess.Popen(["python","-m","json_repl_session"], env=env, ...)

즉, 별도 API 호출 없이 환경변수로 연결.

────────────────────────────────────────
8.  통계/패턴 분석
────────────────────────────────────────
Task 당 1 개의 .jsonl 파일로 완결되므로  
• jq · sqlite import · pandas 등으로 간단히 집계  
• 같은 plan_id 안의 파일만 glob("*/*.jsonl") 하면 cron 통계 가능

────────────────────────────────────────
결론
────────────────────────────────────────
– execute_code() 에서 “경로 선택 → 실행 → 컨텍스트 diff → 로그 남기기” 네 줄기를
  추가하면 3 개의 요구사항(로거 통합, 서브프로세스 격리, 영구 히스토리)이 모두 충족됩니다.  
– 나머지 파일(task_logger.py, manager.py, worker.py) 는 기존 기능 그대로 재사용하며,  
  Worker Manager 만 최소한의 JSON 통신 함수(run_in_worker) 를 노출하면 됩니다.

## 추론 정보
- Reasoning Effort: high
- Usage: {'prompt_tokens': 1163, 'completion_tokens': 3205, 'total_tokens': 4368, 'reasoning_tokens': 0}
