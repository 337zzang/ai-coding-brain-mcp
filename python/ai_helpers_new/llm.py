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


# 전역 o3 작업 저장소
o3_tasks = {}  # 작업 ID를 키로 하는 딕셔너리

# OpenAI 설정
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 패키지가 설치되지 않았습니다. pip install openai")

# 전역 작업 관리
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
            model="o3",
            messages=messages,
            reasoning_effort=reasoning_effort,
            max_completion_tokens=36000
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
        print(f"❌ o3 API 에러: {error_msg}")
        return {"error": error_msg}


def _run_o3_task(task_id: str, question: str, context: Optional[str] = None,
                 api_key: Optional[str] = None, reasoning_effort: str = "high"):
    """백그라운드에서 o3 작업 실행"""
    # 상태 업데이트
    with _task_lock:
        _tasks[task_id]['status'] = 'running'
        _tasks[task_id]['start_time'] = datetime.now()

    try:
        # API 호출
        result = _call_o3_api(question, context, api_key, reasoning_effort)

        # 결과 저장
        with _task_lock:
            if 'error' in result:
                _tasks[task_id]['status'] = 'error'
                _tasks[task_id]['error'] = result['error']
            else:
                _tasks[task_id]['status'] = 'completed'
                _tasks[task_id]['result'] = result

    except Exception as e:
        with _task_lock:
            _tasks[task_id]['status'] = 'error'
            _tasks[task_id]['error'] = str(e)

    finally:
        with _task_lock:
            _tasks[task_id]['end_time'] = datetime.now()


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

    print(f"🚀 작업 {task_id} 시작됨")
    return ok(task_id)
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
        if task['start_time']:
            if task['end_time']:
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


def get_o3_result(task_id: str) -> dict:
    """o3 작업 결과 가져오기

    Args:
        task_id: 작업 ID

    Returns:
        결과 딕셔너리
    """
    with _task_lock:
        task = _tasks.get(task_id)

    if not task:
        return err(f"Task {task_id} not found")

    if task['status'] != 'completed':
        return err(f"Task {task_id} is {task['status']}, not completed")

    # 결과 반환
    result = task.get('result')
    if not result:
        return err(f"No result found for task {task_id}")

    return ok(result)

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


def show_o3_progress() -> Dict[str, Any]:
    """모든 작업의 진행 상황을 보기 좋게 표시"""
    tasks = list_o3_tasks()['data']

    if not tasks:
        print("📭 현재 진행 중인 o3 작업이 없습니다.")
        return ok("No tasks")

    print("\n🤖 o3 작업 현황:")
    print("="*60)

    status_icons = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'error': '❌'
    }

    for task in tasks:
        icon = status_icons.get(task['status'], '❓')
        print(f"{icon} [{task['id']}] {task['status']:<10} - {task['question']}")

    # 요약
    by_status = {}
    for task in tasks:
        status = task['status']
        by_status[status] = by_status.get(status, 0) + 1

    print("\n📊 요약:", end="")
    for status, count in by_status.items():
        print(f" {status}={count}", end="")
    print()

    return ok(f"Total {len(tasks)} tasks")


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
