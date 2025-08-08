# Task 2: TaskLogger 통합 구현 예시

## execute_code() 함수 수정 예시

```python
def execute_code(code: str) -> Dict[str, Any]:
    """Python 코드 실행 (TaskLogger 통합)"""
    global execution_count, repl_globals, helpers
    execution_count += 1

    # === TaskLogger 통합 시작 ===
    pre_snapshot = None
    start_time = None

    if ENABLE_TASK_LOGGING and REPL_LOGGER:
        try:
            # 실행 전 스냅샷 캡처
            start_time = time.perf_counter()
            pre_snapshot = {
                'vars': set(repl_globals.keys()),
                'modules': set(sys.modules.keys()),
                'execution_count': execution_count
            }
        except Exception as e:
            print(f"[TaskLogger] Pre-snapshot 오류: {e}", file=sys.stderr)

    # === 기존 코드 실행 로직 ===
    # 헬퍼 로드 확인
    if not HELPERS_AVAILABLE:
        if load_helpers():
            repl_globals['helpers'] = helpers
            repl_globals['h'] = helpers

    result = {
        'success': True,
        'language': 'python',
        'session_mode': 'JSON_REPL',
        'stdout': '',
        'stderr': '',
        'variable_count': 0,
        'note': 'JSON REPL Session - Variables persist between executions',
        'debug_info': {
            'repl_process_active': True,
            'repl_ready': True
        }
    }

    # stdout/stderr 캡처
    with capture_output() as (stdout, stderr):
        try:
            # 코드 실행
            exec(code, repl_globals)
            result['debug_info']['execution'] = 'success'
        except Exception as e:
            result['success'] = False
            result['stderr'] = f"❌ Runtime Error: {type(e).__name__}: {str(e)}"
            result['debug_info']['execution'] = 'error'

            # 상세 에러 정보
            with io.StringIO() as error_details:
                traceback.print_exc(file=error_details)
                result['stderr'] += '\n' + error_details.getvalue()

    result['stdout'] = stdout.getvalue()
    result['stderr'] += stderr.getvalue()

    # 사용자 정의 변수 카운트
    user_vars = [k for k in repl_globals.keys() 
                if not k.startswith('_') and 
                k not in ['helpers', 'sys', 'os', 'json', 'Path', 'dt', 'time', 'platform']]
    result['variable_count'] = len(user_vars)

    # === TaskLogger 통합 종료 ===
    if ENABLE_TASK_LOGGING and REPL_LOGGER and pre_snapshot:
        try:
            # 실행 시간 계산
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # 실행 후 diff 계산
            post_vars = set(repl_globals.keys())
            post_modules = set(sys.modules.keys())

            added_vars = sorted(post_vars - pre_snapshot['vars'])
            added_modules = sorted(post_modules - pre_snapshot['modules'])

            # TaskLogger에 기록
            log_data = {
                'action': 'execute',
                'code': code,
                'success': result['success'],
                'stdout': result['stdout'][:500],  # 처음 500자만
                'stderr': result['stderr'][:500],  # 처음 500자만
                'elapsed_ms': round(elapsed_ms, 2),
                'added_vars': added_vars,
                'added_modules': added_modules[:10],  # 처음 10개만
                'execution_count': execution_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

            # code 메서드로 기록
            REPL_LOGGER.code(
                action='execute',
                file='<repl>',
                content=code,
                summary=f"Execution #{execution_count} - {'Success' if result['success'] else 'Failed'}",
                details=log_data
            )

            # debug_info에 추가 정보 포함
            result['debug_info'].update({
                'logged': True,
                'elapsed_ms': round(elapsed_ms, 2),
                'added_vars': len(added_vars),
                'added_modules': len(added_modules)
            })

        except Exception as e:
            # 로깅 실패해도 실행은 계속
            print(f"[TaskLogger] 로깅 오류: {e}", file=sys.stderr)
            result['debug_info']['logged'] = False

    return result
```

## 주요 변경사항

1. **실행 전 스냅샷**
   - 현재 변수 목록
   - 로드된 모듈 목록
   - 실행 카운트

2. **실행 시간 측정**
   - time.perf_counter() 사용
   - 밀리초 단위로 기록

3. **실행 후 diff**
   - 추가된 변수 계산
   - 새로 import된 모듈 추적

4. **TaskLogger 기록**
   - code() 메서드 사용
   - 구조화된 데이터 전달
   - 실패 시에도 실행 계속

5. **debug_info 확장**
   - 로깅 성공 여부
   - 실행 시간
   - 변경사항 요약
