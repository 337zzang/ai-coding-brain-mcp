
# llm_patch.py - 비동기 작업 파일 저장 패치
"""
LLM 비동기 작업을 파일로 저장하는 monkey patch
"""

import json
import os
from datetime import datetime

def patch_llm_module():
    """llm 모듈에 파일 저장 기능 추가"""
    import ai_helpers_new.llm as llm_module

    # 원래 함수들 백업
    original_run_task = llm_module._run_o3_task
    original_get_result = llm_module.get_o3_result

    # 작업 저장 디렉토리
    TASK_DIR = ".ai-brain/o3_tasks"

    def save_task_json(task_id, data):
        """작업 상태를 JSON 파일로 저장"""
        os.makedirs(TASK_DIR, exist_ok=True)
        file_path = os.path.join(TASK_DIR, f"{task_id}.json")

        # datetime 변환
        data_copy = data.copy()
        for key in ['start_time', 'end_time']:
            if key in data_copy and hasattr(data_copy[key], 'isoformat'):
                data_copy[key] = data_copy[key].isoformat()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_copy, f, indent=2, ensure_ascii=False)

    def load_task_json(task_id):
        """JSON 파일에서 작업 상태 로드"""
        file_path = os.path.join(TASK_DIR, f"{task_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def patched_run_task(task_id, question, context=None, api_key=None, reasoning_effort="high"):
        """개선된 _run_o3_task"""
        # 시작 상태 저장
        save_task_json(task_id, {
            'id': task_id,
            'status': 'running',
            'question': question[:200],
            'start_time': datetime.now(),
            'reasoning_effort': reasoning_effort
        })

        # 원래 함수 실행
        result = original_run_task(task_id, question, context, api_key, reasoning_effort)

        # 완료 상태 저장
        task_data = load_task_json(task_id) or {'id': task_id}
        task_data['status'] = 'completed'
        task_data['end_time'] = datetime.now()
        save_task_json(task_id, task_data)

        return result

    def patched_get_result(task_id):
        """개선된 get_o3_result"""
        # 파일에서 먼저 확인
        task_data = load_task_json(task_id)
        if task_data:
            if task_data.get('status') == 'completed':
                # 원래 함수로 결과 가져오기
                return original_get_result(task_id)

        # 원래 함수 실행
        return original_get_result(task_id)

    # Monkey patching
    llm_module._run_o3_task = patched_run_task
    llm_module.get_o3_result = patched_get_result

    print("✅ LLM 모듈 패치 완료")

# 패치 적용
if __name__ == "__main__":
    patch_llm_module()
