#!/usr/bin/env python3
"""
LLM 비동기 처리 개선 테스트
"""

import sys
import time
sys.path.insert(0, 'python')

import ai_helpers_new as h

print("\n🧪 LLM 비동기 처리 테스트 시작")
print("=" * 60)

# 1. 비동기 작업 시작
print("\n1️⃣ 비동기 작업 시작")
question = "Python에서 파일을 읽는 간단한 방법은?"
result = h.llm.ask_async(question)

if result['ok']:
    task_id = result['data']
    print(f"✅ 작업 시작: {task_id}")

    # 2. 즉시 상태 확인
    print("\n2️⃣ 즉시 상태 확인")
    status = h.llm.check_status(task_id)
    if status['ok']:
        print(f"상태: {status['data'].get('status', 'unknown')}")
    else:
        print(f"상태 확인 실패: {status.get('error')}")

    # 3. 잠시 대기
    print("\n3️⃣ 5초 대기...")
    time.sleep(5)

    # 4. 결과 확인
    print("\n4️⃣ 결과 확인")
    for i in range(10):  # 최대 10번 시도
        result = h.llm.get_result(task_id)
        if result['ok']:
            print("✅ 결과 받기 성공!")
            answer = result['data'].get('answer', 'No answer')
            print(f"답변 (일부): {answer[:200]}...")
            break
        else:
            status_msg = result.get('error', '')
            if 'running' in status_msg:
                print(f"⏳ 아직 실행 중... ({i+1}/10)")
                time.sleep(3)
            else:
                print(f"❌ 실패: {status_msg}")
                break

    # 5. 파일 확인
    print("\n5️⃣ 저장된 파일 확인")
    import os
    task_file = f".ai-brain/o3_tasks/{task_id}.json"
    if os.path.exists(task_file):
        print(f"✅ 작업 파일 존재: {task_file}")
        with open(task_file, 'r') as f:
            import json
            data = json.load(f)
            print(f"  상태: {data.get('status')}")
            print(f"  시작: {data.get('start_time')}")
    else:
        print(f"❌ 작업 파일 없음: {task_file}")

else:
    print(f"❌ 작업 시작 실패: {result.get('error')}")

print("\n" + "=" * 60)
print("✅ 테스트 완료!")
