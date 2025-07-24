"""
Flow 데이터 마이그레이션
레거시 5단계 상태를 3단계로 변환
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path


def migrate_flows_data(input_path: str = '.ai-brain/flows.json',
                      output_path: str = None,
                      backup: bool = True):
    """Flow 데이터 마이그레이션"""

    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ 파일이 없습니다: {input_path}")
        return False

    # 백업
    if backup:
        backup_path = input_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        shutil.copy(input_path, backup_path)
        print(f"📁 백업 생성: {backup_path}")

    # 데이터 로드
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"🔍 {len(data)} 개의 Flow 발견")

    # 상태 변환 매핑
    status_map = {
        'todo': 'todo',
        'planning': 'doing',
        'in_progress': 'doing', 
        'reviewing': 'doing',
        'completed': 'done',
        'done': 'done',
        'archived': 'archived'
    }

    # 마이그레이션
    migrated = 0
    for flow_id, flow in data.items():
        if isinstance(flow, dict):
            # Plans 처리
            if 'plans' in flow and isinstance(flow['plans'], dict):
                for plan_id, plan in flow['plans'].items():
                    if isinstance(plan, dict) and 'tasks' in plan:
                        # Tasks 처리
                        if isinstance(plan['tasks'], dict):
                            for task_id, task in plan['tasks'].items():
                                if isinstance(task, dict) and 'status' in task:
                                    old_status = task['status']
                                    new_status = status_map.get(old_status, 'todo')

                                    if old_status != new_status:
                                        task['status'] = new_status
                                        task['_migrated'] = True
                                        task['_old_status'] = old_status
                                        migrated += 1
                                        print(f"  ✅ {task_id}: {old_status} → {new_status}")

    # 저장
    output_path = output_path or input_path
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 마이그레이션 완료: {migrated}개 Task 상태 변환")
    print(f"📄 저장: {output_path}")

    return True


if __name__ == '__main__':
    # 직접 실행시
    migrate_flows_data()
