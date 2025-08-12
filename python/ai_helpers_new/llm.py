"""
AI Helpers LLM Module
LLM 작업을 위한 백그라운드 실행 가능한 모듈
"""
import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from .util import ok, err
from .wrappers import safe_execution
from .file import read, read_json, write, exists


# 전역 o3 작업 저장소
o3_tasks = {}

# ============ O3 작업 관리 시스템 통합 ============
try:
    from .o3_task_manager import (
        save_o3_task, load_o3_task, delete_o3_task,
        cleanup_o3_tasks, get_o3_statistics, archive_o3_tasks
    )
    O3_MANAGER_AVAILABLE = True
except ImportError:
    O3_MANAGER_AVAILABLE = False
    print("⚠️ O3 작업 관리 시스템 사용 불가")

def _save_task_with_manager(task_id: str, data: Dict[str, Any]):
    """작업 관리 시스템을 통한 저장"""
    if O3_MANAGER_AVAILABLE:
        save_o3_task(task_id, data)

    # 메모리에도 저장 (하위 호환성)
    with _task_lock:
        _tasks[task_id] = data

def _load_task_with_manager(task_id: str) -> Optional[Dict[str, Any]]:
    """작업 관리 시스템을 통한 로드"""
    if O3_MANAGER_AVAILABLE:
        task_data = load_o3_task(task_id)
        if task_data:
            return task_data

    # 메모리에서 확인
    with _task_lock:
        return _tasks.get(task_id)

# 관리 명령어들
def cleanup_old_o3_tasks(days: int = 7) -> Dict[str, Any]:
    """오래된 O3 작업 정리

    Args:
        days: 보관 기간 (기본 7일)

    Returns:
        정리 결과
    """
    if not O3_MANAGER_AVAILABLE:
        return err("O3 작업 관리 시스템 사용 불가")

    deleted = cleanup_o3_tasks(days)
    return ok({
        'deleted_count': deleted,
        'message': f'{deleted}개 파일 정리 완료'
    })

def get_o3_task_statistics() -> Dict[str, Any]:
    """O3 작업 통계 조회"""
    if not O3_MANAGER_AVAILABLE:
        return err("O3 작업 관리 시스템 사용 불가")

    stats = get_o3_statistics()

    # 포맷팅
    if stats['oldest_file']:
        oldest_time = datetime.fromtimestamp(stats['oldest_file'][1])
        stats['oldest_file'] = f"{stats['oldest_file'][0]} ({oldest_time.strftime('%Y-%m-%d %H:%M')})"

    if stats['newest_file']:
        newest_time = datetime.fromtimestamp(stats['newest_file'][1])
        stats['newest_file'] = f"{stats['newest_file'][0]} ({newest_time.strftime('%Y-%m-%d %H:%M')})"

    # 크기 포맷팅
    if stats['total_size'] > 1024 * 1024:
        stats['total_size_formatted'] = f"{stats['total_size'] / (1024*1024):.2f} MB"
    elif stats['total_size'] > 1024:
        stats['total_size_formatted'] = f"{stats['total_size'] / 1024:.2f} KB"
    else:
        stats['total_size_formatted'] = f"{stats['total_size']} bytes"

    return ok(stats)

def archive_completed_o3_tasks() -> Dict[str, Any]:
    """완료된 O3 작업 아카이브"""
    if not O3_MANAGER_AVAILABLE:
        return err("O3 작업 관리 시스템 사용 불가")

    archived = archive_o3_tasks()
    return ok({
        'archived_count': archived,
        'message': f'{archived}개 작업 아카이브 완료'
    })

def delete_o3_task_by_id(task_id: str) -> Dict[str, Any]:
    """특정 O3 작업 삭제"""
    if not O3_MANAGER_AVAILABLE:
        return err("O3 작업 관리 시스템 사용 불가")

    if delete_o3_task(task_id):
        # 메모리에서도 삭제
        with _task_lock:
            _tasks.pop(task_id, None)

        return ok({'message': f'Task {task_id} 삭제 완료'})
    else:
        return err(f'Task {task_id} 삭제 실패')

_tasks = {}  # 작업 ID를 키로 하는 딕셔너리

# OpenAI 설정
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI 패키지가 설치되지 않았습니다. pip install openai")

# 전역 작업 관리

# ============ 파일 기반 상태 관리 (비동기 처리 개선) ============
import json
import os

# 작업 상태 저장 경로
TASK_STORAGE_DIR = ".ai-brain/o3_tasks"

def _ensure_storage_dir():
    """작업 저장소 디렉토리 생성"""
    os.makedirs(TASK_STORAGE_DIR, exist_ok=True)

def _get_task_file_path(task_id: str) -> str:
    """작업 파일 경로 반환"""
    return os.path.join(TASK_STORAGE_DIR, f"{task_id}.json")

def save_task_state(task_id: str, state: Dict[str, Any]):
    """작업 상태를 파일로 저장"""
    _ensure_storage_dir()
    file_path = _get_task_file_path(task_id)

    # datetime 객체를 문자열로 변환
    state_copy = state.copy()
    for key in ['start_time', 'end_time', 'last_update']:
        if key in state_copy and isinstance(state_copy[key], datetime):
            state_copy[key] = state_copy[key].isoformat()

    try:
        with _task_lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state_copy, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 작업 상태 저장 실패: {e}")
        return False

def load_task_state(task_id: str) -> Optional[Dict[str, Any]]:
    """파일에서 작업 상태 로드"""
    file_path = _get_task_file_path(task_id)

    if not os.path.exists(file_path):
        # 메모리에서 먼저 확인 (하위 호환성)
        with _task_lock:
            if task_id in _tasks:
                return _tasks[task_id]
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # 문자열을 datetime으로 변환
        for key in ['start_time', 'end_time', 'last_update']:
            if key in state and state[key]:
                state[key] = datetime.fromisoformat(state[key])

        return state
    except Exception as e:
        print(f"❌ 작업 상태 로드 실패: {e}")
        # 메모리에서 확인
        with _task_lock:
            return _tasks.get(task_id)

def update_task_status(task_id: str, status: str, **kwargs):
    """작업 상태 업데이트"""
    # 기존 상태 로드
    state = load_task_state(task_id)
    if not state:
        state = {'id': task_id}

    # 상태 업데이트
    state['status'] = status
    state['last_update'] = datetime.now()

    # 추가 필드 업데이트
    for key, value in kwargs.items():
        state[key] = value

    # 파일로 저장
    save_task_state(task_id, state)

    # 메모리에도 업데이트 (하위 호환성)
    with _task_lock:
        _tasks[task_id] = state

_tasks = {}
_task_counter = 0
_task_lock = threading.Lock()

def _generate_task_id() -> str:
    """고유한 작업 ID 생성"""
    global _task_counter
    with _task_lock:
        _task_counter += 1
        return f"o3_task_{_task_counter:04d}"


def _call_o3_api(question: str, context: Optional[str] = None, 
                 api_key: Optional[str] = None, reasoning_effort: str = "high") -> Dict[str, Any]:
    """실제 o3 API 호출 (내부 함수)"""
    if not OPENAI_AVAILABLE:
        return {"error": "OpenAI package not installed"}

    # API 키 설정
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not found"}

    try:
        client = OpenAI(api_key=api_key)

        # 메시지 구성
        messages = [{"role": "user", "content": question}]
        if context:
            messages.insert(0, {"role": "system", "content": context})

        print(f"🤔 o3 모델 호출 중... (reasoning_effort: {reasoning_effort})")

        # API 호출
        response = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            reasoning_effort=reasoning_effort
        )

        # 결과 파싱
        answer = response.choices[0].message.content
        usage = response.usage

        return {
            "answer": answer,
            "reasoning_effort": reasoning_effort,
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "reasoning_tokens": getattr(usage, 'reasoning_tokens', 0) if hasattr(usage, 'reasoning_tokens') else 0
            } if usage else None
        }

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[ERROR] o3 API 에러: {error_msg}")
        return {"error": error_msg}


def _run_o3_task(task_id: str, question: str, context: Optional[str] = None,
                 api_key: Optional[str] = None, reasoning_effort: str = "high"):
    """백그라운드에서 o3 작업 실행 (개선 버전)"""

    # 초기 상태를 파일과 메모리에 저장
    initial_state = {
        'id': task_id,
        'status': 'running',
        'question': question[:200] if len(question) > 200 else question,
        'start_time': datetime.now(),
        'reasoning_effort': reasoning_effort
    }

    # 파일로 저장
    save_task_state(task_id, initial_state)

    # 메모리에도 저장 (하위 호환성)
    with _task_lock:
        _tasks[task_id] = initial_state.copy()

    try:
        # API 호출
        result = _call_o3_api(question, context, api_key, reasoning_effort)

        # 결과에 따라 상태 업데이트
        if 'error' in result:
            update_task_status(task_id, 'error', 
                             error=result['error'],
                             end_time=datetime.now())
        else:
            update_task_status(task_id, 'completed',
                             result=result,
                             end_time=datetime.now())

    except Exception as e:
        update_task_status(task_id, 'error',
                         error=str(e),
                         end_time=datetime.now())
def ask_o3_async(question: str, context: Optional[str] = None, 
                 reasoning_effort: Union[str, None] = "high", 
                 _api_key: Optional[str] = None) -> Dict[str, Any]:
    """o3 모델에 비동기로 질문 (백그라운드 실행)

    Args:
        question: 질문 내용
        context: 추가 컨텍스트 (선택)
        reasoning_effort: 추론 수준 - "high", "medium", "low" (기본: "high")
        _api_key: API 키 (선택, 환경변수 사용 권장) - deprecated

    Returns:
        성공 시: {"ok": True, "data": task_id}
        실패 시: {"ok": False, "error": 에러_메시지}
    """
    # 역호환성 처리: 3번째 인자가 API 키인 경우
    if reasoning_effort and isinstance(reasoning_effort, str):
        # API 키의 특징: sk-로 시작하거나 길이가 40자 이상
        if reasoning_effort.startswith('sk-') or len(reasoning_effort) > 40:
            _api_key = reasoning_effort
            reasoning_effort = "high"
        # "low", "medium", "high"가 아닌 경우도 API 키로 간주
        elif reasoning_effort not in ["low", "medium", "high"]:
            _api_key = reasoning_effort
            reasoning_effort = "high"

    # 작업 생성
    task_id = _generate_task_id()

    with _task_lock:
        _tasks[task_id] = {
            'id': task_id,
            'question': question,
            'context': context,
            'status': 'pending',
            'started_at': datetime.now().isoformat(),
            'error': None,
            'reasoning_effort': reasoning_effort
        }

    # 백그라운드 스레드에서 실행
    thread = threading.Thread(
        target=_run_o3_task,
        args=(task_id, question, context, _api_key, reasoning_effort),
        name=f"o3-{task_id}"
    )
    thread.daemon = True
    thread.start()

    print(f"[START] 작업 {task_id} 시작됨")
    return ok(task_id)
@safe_execution
def check_o3_status(task_id: str) -> Dict[str, Any]:
    """작업 상태 확인

    Returns:
        {
            'ok': True,
            'data': {
                'id': 'task_id',
                'status': 'pending|running|completed|error',
                'question': '질문 일부...',
                'duration': '실행 시간',
                'reasoning_effort': 'high'
            }
        }
    """
    with _task_lock:
        if task_id not in _tasks:
            return err(f"Task {task_id} not found")

        task = _tasks[task_id]

        # 실행 시간 계산
        duration = None
        if task.get('start_time'):
            if task.get('end_time'):
                duration = (task['end_time'] - task['start_time']).total_seconds()
            else:
                duration = (datetime.now() - task['start_time']).total_seconds()

        return ok({
            'id': task_id,
            'status': task['status'],
            'question': task['question'][:100] + ('...' if len(task['question']) > 100 else ''),
            'duration': f"{duration:.1f}초" if duration else None,
            'reasoning_effort': task.get('reasoning_effort', 'high')
        })


@safe_execution
def get_o3_result(task_id: str) -> dict:
    """o3 작업 결과 가져오기 (개선 버전)

    파일에서 먼저 확인, 없으면 메모리 확인
    """
    # 파일에서 상태 로드
    state = load_task_state(task_id)

    if not state:
        return err(f"Task {task_id} not found")

    if state.get('status') != 'completed':
        status = state.get('status', 'unknown')
        return err(f"Task {task_id} is {status}, not completed")

    # 결과 반환
    result = state.get('result')
    if not result:
        return err(f"No result found for task {task_id}")

    return ok(result)
@safe_execution
def save_o3_result(task_id: str) -> dict:
    """o3 작업 결과를 파일로 저장

    Args:
        task_id: 작업 ID

    Returns:
        {'ok': True, 'data': 'filepath'} or {'ok': False, 'error': 'message'}
    """
    from datetime import datetime
    import os

    with _task_lock:
        task = _tasks.get(task_id)

    if not task:
        return err(f"Task {task_id} not found")

    if task['status'] != 'completed':
        return err(f"Task {task_id} is {task['status']}, not completed")

    result = task.get('result')
    if not result:
        return err(f"No result found for task {task_id}")

    # llm 디렉토리 생성
    llm_dir = "llm"
    if not os.path.exists(llm_dir):
        os.makedirs(llm_dir)

    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"llm/o3_{task_id}_{timestamp}.md"

    # 내용 구성
    content = f"""# o3 Analysis Result

## Task ID: {task_id}

### Question
{task['question']}

### Context
{task.get('context', 'No context provided')}

### Answer
{result.get('answer', 'No answer')}

### Metadata
- Reasoning Effort: {task.get('reasoning_effort', 'N/A')}

- Start Time: {task.get('start_time', 'N/A')}
- End Time: {task.get('end_time', 'N/A')}
"""

    # Duration 계산
    if task.get('start_time') and task.get('end_time'):
        duration = (task['end_time'] - task['start_time']).total_seconds()
        content += f"- Duration: {duration:.1f}초\n"

    # Token usage
    usage = result.get('usage', {})
    if usage:
        content += f"""
### Token Usage
- Prompt Tokens: {usage.get('prompt_tokens', 0):,}
- Completion Tokens: {usage.get('completion_tokens', 0):,}
- Reasoning Tokens: {usage.get('reasoning_tokens', 0):,}
- Total Tokens: {usage.get('total_tokens', 0):,}
"""

    # 파일 저장
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return ok(filename)
    except Exception as e:
        return err(f"Failed to save result: {str(e)}")

@safe_execution
def list_o3_tasks(status_filter: Optional[str] = None) -> Dict[str, Any]:
    """모든 o3 작업 목록

    Args:
        status_filter: 특정 상태만 필터링 ('pending', 'running', 'completed', 'error')

    Returns:
        {'ok': True, 'data': [작업 목록]}
    """
    with _task_lock:
        tasks = []

        for task_id, task in _tasks.items():
            if status_filter and task['status'] != status_filter:
                continue

            tasks.append({
                'id': task_id,
                'status': task['status'],
                'question': task['question'][:50] + ('...' if len(task['question']) > 50 else ''),
                'start_time': task['start_time'].isoformat() if task['start_time'] else None
            })

        # 최신 것부터 정렬
        tasks.sort(key=lambda x: x['id'], reverse=True)

        return ok(tasks, count=len(tasks))


@safe_execution
def show_o3_progress() -> Dict[str, Any]:
    """모든 작업의 진행 상황을 보기 좋게 표시"""
    tasks = list_o3_tasks()['data']

    if not tasks:
        print("📭 현재 진행 중인 o3 작업이 없습니다.")
        return ok("No tasks")

    print("\n[AI] o3 작업 현황:")
    print("="*60)

    status_icons = {
        'pending': '[PENDING]',
        'running': '[IN_PROGRESS]',
        'completed': '[OK]',
        'error': '[ERROR]'
    }

    for task in tasks:
        icon = status_icons.get(task['status'], '❓')
        print(f"{icon} [{task['id']}] {task['status']:<10} - {task['question']}")

    # 요약
    by_status = {}
    for task in tasks:
        status = task['status']
        by_status[status] = by_status.get(status, 0) + 1

    print("\n[STATS] 요약:", end="")
    for status, count in by_status.items():
        print(f" {status}={count}", end="")
    print()

    return ok(f"Total {len(tasks)} tasks")


@safe_execution
def clear_completed_tasks() -> Dict[str, Any]:
    """완료되거나 에러난 작업들 정리"""
    with _task_lock:
        to_remove = []

        for task_id, task in _tasks.items():
            if task['status'] in ['completed', 'error']:
                to_remove.append(task_id)

        for task_id in to_remove:
            del _tasks[task_id]

        return ok(f"Cleared {len(to_remove)} tasks")


@safe_execution
def prepare_o3_context(topic: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """o3를 위한 구조화된 컨텍스트 준비

    Args:
        topic: 주제 또는 문제 설명
        files: 포함할 파일 경로 리스트

    Returns:
        구조화된 컨텍스트 딕셔너리
    """
    from datetime import datetime
    from pathlib import Path

    context_parts = []
    included_files = []

    if files:
        from .file import read

        for file_path in files:
            # pathlib 사용 (o3 권장)
            path = Path(file_path)

            result = read(str(path))
            if result.get('ok'):
                content = result['data']
                # 큰 파일은 일부만
                if len(content) > 5000:
                    content = content[:5000] + "\n... (truncated)"

                context_parts.append(f"=== File: {path.name} ===\n{content}\n")
                included_files.append({
                    'path': str(path),
                    'name': path.name,
                    'lines': len(content.splitlines()),
                    'truncated': len(result['data']) > 5000
                })
            else:
                context_parts.append(f"=== File: {path.name} (Error: {result.get('error', 'Unknown')}) ===\n")

    # 프로젝트 정보 추가
    project_info = None
    try:
        from .file import read_json
        proj_result = read_json(".ai-brain.config.json")
        if proj_result.get('ok'):
            project_info = proj_result['data'].get('name', 'Unknown')
            context_parts.append(f"\nProject: {project_info}")
    except:
        pass

    # 구조화된 dict 반환 (o3 권장사항)
    return {
        'topic': topic,
        'context': '\n'.join(context_parts),
        'files': included_files,
        'timestamp': datetime.now().isoformat(),
        'total_files': len(included_files),
        'project': project_info
    }


@safe_execution
def ask_o3_practical(question: str, file_content: str = "", error_info: str = "", 
                    max_lines: int = 10, reasoning_effort: str = "medium") -> Dict[str, Any]:
    """
    O3에게 실용적인 답변을 요청하는 헬퍼 함수

    Args:
        question: 질문 내용
        file_content: 관련 파일 내용 (선택)
        error_info: 에러 정보 (선택)
        max_lines: 최대 코드 수정 라인 수 (기본 10)
        reasoning_effort: 추론 강도 (low/medium/high)

    Returns:
        O3의 답변을 포함한 딕셔너리
    """
    # 실용적 가이드라인을 포함한 컨텍스트 구성
    context_parts = []

    if file_content:
        context_parts.append(f"=== 파일 내용 ===\n{file_content}")

    if error_info:
        context_parts.append(f"=== 에러 정보 ===\n{error_info}")

    # 실용적 가이드라인 추가
    context_parts.append(f"""
=== 답변 규칙 ===
- {max_lines}줄 이내의 코드 수정만 제안
- 기존 코드 구조와 패턴 유지
- 외부 라이브러리 추가 금지
- 즉시 복사-붙여넣기 가능한 코드
- 과도한 리팩토링이나 디자인 패턴 금지
- dataclass, async/await 등 불필요한 개선 금지
""")

    context = "\n\n".join(context_parts)

    # O3 비동기 호출
    result = ask_o3_async(question, context, reasoning_effort)
    if not result['ok']:
        return result

    task_id = result['data']

    # 결과 대기 (최대 60초)
    import time
    max_wait = 60
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status_result = check_o3_status(task_id)
        if not status_result['ok']:
            return status_result

        if status_result['data']['status'] == 'completed':
            return get_o3_result(task_id)
        elif status_result['data']['status'] == 'failed':
            return {'ok': False, 'error': 'O3 작업 실패'}

        time.sleep(3)

    return {'ok': False, 'error': 'O3 응답 시간 초과 (60초)'}


def O3ContextBuilder():
    """
    O3 컨텍스트 빌더 클래스 (간단한 구현)
    파일 내용, 에러 정보 등을 체계적으로 구성
    """
    class _O3ContextBuilder:
        def __init__(self):
            self.context_parts = []
            self.files = []

        def add_file(self, file_path: str, max_lines: int = 100):
            """파일 내용 추가"""
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:max_lines]
                        content = ''.join(lines)
                        self.context_parts.append(f"=== 파일: {file_path} ===\n{content}")
                        self.files.append(file_path)
            except Exception as e:
                self.context_parts.append(f"=== 파일 읽기 오류: {file_path} ===\n{str(e)}")
            return self

        def add_error(self, error_msg: str, file_path: str = "", line_num: int = 0):
            """에러 정보 추가"""
            error_info = f"=== 에러 정보 ===\n에러: {error_msg}"
            if file_path:
                error_info += f"\n파일: {file_path}"
            if line_num:
                error_info += f"\n라인: {line_num}"
            self.context_parts.append(error_info)
            return self

        def add_context(self, title: str, content: str):
            """커스텀 컨텍스트 추가"""
            self.context_parts.append(f"=== {title} ===\n{content}")
            return self

        def build(self) -> str:
            """최종 컨텍스트 문자열 생성"""
            return "\n\n".join(self.context_parts)

        def ask(self, question: str, practical: bool = True, reasoning_effort: str = "medium") -> Dict[str, Any]:
            """컨텍스트를 포함하여 O3에게 질문"""
            context = self.build()

            if practical:
                context += """\n\n=== 실용적 가이드라인 ===
- 5-10줄 이내의 간단한 수정만 제안
- 기존 패턴과 구조 유지
- 즉시 적용 가능한 실용적 해결책
- 과도한 리팩토링 금지"""

            result = ask_o3_async(question, context, reasoning_effort)
            if not result['ok']:
                return result

            # 동기적으로 결과 대기
            task_id = result['data']
            import time
            max_wait = 60
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status_result = check_o3_status(task_id)
                if not status_result['ok']:
                    return status_result

                if status_result['data']['status'] == 'completed':
                    return get_o3_result(task_id)
                elif status_result['data']['status'] == 'failed':
                    return {'ok': False, 'error': 'O3 작업 실패'}

                time.sleep(3)

            return {'ok': False, 'error': 'O3 응답 시간 초과'}

    return _O3ContextBuilder()


def quick_o3_context(error_msg: str, file_path: str = "", line_num: int = 0) -> 'O3ContextBuilder':
    """
    에러 해결을 위한 빠른 컨텍스트 생성

    Args:
        error_msg: 에러 메시지
        file_path: 에러가 발생한 파일 경로
        line_num: 에러가 발생한 라인 번호

    Returns:
        설정된 O3ContextBuilder 인스턴스
    """
    builder = O3ContextBuilder()
    builder.add_error(error_msg, file_path, line_num)

    if file_path and os.path.exists(file_path):
        # 에러 주변 코드 추출
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start_line = max(0, line_num - 10)
                end_line = min(len(lines), line_num + 10)

                context_lines = []
                for i in range(start_line, end_line):
                    prefix = ">>> " if i == line_num - 1 else "    "
                    context_lines.append(f"{i+1:4d} {prefix}{lines[i].rstrip()}")

                builder.add_context("에러 주변 코드", "\n".join(context_lines))
        except Exception:
            pass

    return builder