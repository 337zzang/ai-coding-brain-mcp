#!/usr/bin/env python3
"""
Plan.tasks 마이그레이션 스크립트
Dict[str, Task] → OrderedDict[str, Task] 변환
"""

import json
import os
from collections import OrderedDict
from datetime import datetime
import shutil

def migrate_plan_files(flow_dir=".ai-brain/flow/plans"):
    """모든 Plan 파일을 새 형식으로 마이그레이션"""

    if not os.path.exists(flow_dir):
        print(f"❌ Flow 디렉토리가 없습니다: {flow_dir}")
        return

    # 백업 디렉토리 생성
    backup_dir = f"{flow_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(flow_dir, backup_dir)
    print(f"✅ 백업 생성됨: {backup_dir}")

    migrated_count = 0
    error_count = 0

    # 모든 plan.json 파일 찾기
    for root, dirs, files in os.walk(flow_dir):
        for file in files:
            if file == "plan.json":
                file_path = os.path.join(root, file)
                try:
                    # JSON 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # tasks가 dict인 경우 OrderedDict로 변환
                    if 'tasks' in data and isinstance(data['tasks'], dict):
                        # 생성 시간 기준으로 정렬 (있는 경우)
                        sorted_tasks = sorted(
                            data['tasks'].items(),
                            key=lambda x: x[1].get('created_at', ''),
                        )

                        # OrderedDict로 재구성
                        data['tasks'] = OrderedDict(sorted_tasks)

                        # 다시 저장 (JSON은 순서를 유지)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        migrated_count += 1
                        print(f"✅ 마이그레이션됨: {file_path}")

                except Exception as e:
                    error_count += 1
                    print(f"❌ 오류 발생: {file_path} - {str(e)}")

    print(f"\n📊 마이그레이션 완료:")
    print(f"  - 성공: {migrated_count}개")
    print(f"  - 실패: {error_count}개")
    print(f"  - 백업: {backup_dir}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        flow_dir = sys.argv[1]
    else:
        # 현재 프로젝트의 flow 디렉토리 사용
        flow_dir = os.path.join(os.getcwd(), ".ai-brain/flow/plans")

    print("🚀 Plan.tasks 마이그레이션 시작")
    print(f"대상 디렉토리: {flow_dir}")

    migrate_plan_files(flow_dir)
