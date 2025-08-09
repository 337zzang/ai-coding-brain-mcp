"""
LLM (o3) 통합 모듈 - 개선 버전
파일 기반 작업 상태 관리로 비동기 처리 문제 해결
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from ..util import ok, err, is_ok, get_data, get_error

# 작업 상태 저장 경로
TASK_STORAGE_DIR = ".ai-brain/o3_tasks"

# Thread 안전 잠금
_task_lock = threading.Lock()

def _ensure_storage_dir():
    """작업 저장소 디렉토리 생성"""
    os.makedirs(TASK_STORAGE_DIR, exist_ok=True)

def _get_task_file_path(task_id: str) -> str:
    """작업 파일 경로 반환"""
    return os.path.join(TASK_STORAGE_DIR, f"{task_id}.json")

def save_task_state(task_id: str, state: Dict[str, Any]):
    """작업 상태를 파일로 저장

    Args:
        task_id: 작업 ID
        state: 저장할 상태 딕셔너리
    """
    _ensure_storage_dir()
    file_path = _get_task_file_path(task_id)

    # datetime 객체를 문자열로 변환
    if 'start_time' in state and isinstance(state['start_time'], datetime):
        state['start_time'] = state['start_time'].isoformat()
    if 'end_time' in state and isinstance(state['end_time'], datetime):
        state['end_time'] = state['end_time'].isoformat()
    if 'last_update' in state and isinstance(state['last_update'], datetime):
        state['last_update'] = state['last_update'].isoformat()

    try:
        with _task_lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ 작업 상태 저장 실패: {e}")

def load_task_state(task_id: str) -> Optional[Dict[str, Any]]:
    """파일에서 작업 상태 로드

    Args:
        task_id: 작업 ID

    Returns:
        상태 딕셔너리 또는 None
    """
    file_path = _get_task_file_path(task_id)

    if not os.path.exists(file_path):
        return None

    try:
        with _task_lock:
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

        # 문자열을 datetime으로 변환
        if 'start_time' in state and state['start_time']:
            state['start_time'] = datetime.fromisoformat(state['start_time'])
        if 'end_time' in state and state['end_time']:
            state['end_time'] = datetime.fromisoformat(state['end_time'])
        if 'last_update' in state and state['last_update']:
            state['last_update'] = datetime.fromisoformat(state['last_update'])

        return state
    except Exception as e:
        print(f"❌ 작업 상태 로드 실패: {e}")
        return None

def update_task_status(task_id: str, status: str, **kwargs):
    """작업 상태 업데이트

    Args:
        task_id: 작업 ID
        status: 새 상태
        **kwargs: 추가 필드
    """
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

    # 저장
    save_task_state(task_id, state)

def list_all_tasks() -> List[Dict[str, Any]]:
    """모든 작업 목록 반환"""
    _ensure_storage_dir()
    tasks = []

    try:
        for filename in os.listdir(TASK_STORAGE_DIR):
            if filename.endswith('.json'):
                task_id = filename[:-5]  # .json 제거
                state = load_task_state(task_id)
                if state:
                    tasks.append(state)
    except Exception as e:
        print(f"❌ 작업 목록 조회 실패: {e}")

    return tasks

# ========== 기존 함수 수정 ==========

def _run_o3_task_improved(task_id: str, question: str, context: Optional[str] = None,
                         api_key: Optional[str] = None, reasoning_effort: str = "high"):
    """백그라운드에서 o3 작업 실행 (개선 버전)"""

    # 초기 상태 저장
    initial_state = {
        'id': task_id,
        'status': 'running',
        'question': question[:200],  # 질문 일부만 저장
        'start_time': datetime.now(),
        'reasoning_effort': reasoning_effort
    }
    save_task_state(task_id, initial_state)

    try:
        # API 호출 (기존 _call_o3_api 사용)
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

def get_o3_result_improved(task_id: str) -> dict:
    """o3 작업 결과 가져오기 (개선 버전)"""

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

def check_o3_status_improved(task_id: str) -> Dict[str, Any]:
    """작업 상태 확인 (개선 버전)"""

    state = load_task_state(task_id)

    if not state:
        return err(f"Task {task_id} not found")

    # 실행 시간 계산
    duration = None
    if state.get('start_time'):
        if state.get('end_time'):
            duration = (state['end_time'] - state['start_time']).total_seconds()
        else:
            duration = (datetime.now() - state['start_time']).total_seconds()

    return ok({
        'id': task_id,
        'status': state.get('status', 'unknown'),
        'duration': duration,
        'error': state.get('error'),
        'start_time': state.get('start_time'),
        'end_time': state.get('end_time')
    })
