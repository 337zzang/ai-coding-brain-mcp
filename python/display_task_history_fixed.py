# 개선된 display_task_history 함수 (들여쓰기 및 이스케이프 문자 수정)
def display_task_history_fixed(plan_id: str, show_all: bool = False):
    """완료된 Task들의 JSONL 전체 내역을 구조화하여 표시"""
    plan_dir = os.path.join(
        get_manager().project_path,
        ".ai-brain", "flow", "plans", plan_id
    )

    if not os.path.exists(plan_dir):
        return

    print("\n📋 기존 Task 작업 내역:")
    print("="*70)

    jsonl_files = sorted(glob.glob(os.path.join(plan_dir, "*.jsonl")))

    for jsonl_file in jsonl_files:
        task_name = os.path.basename(jsonl_file).replace('.jsonl', '')
        events = []

        # JSONL 파일 읽기
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            continue

        # 완료된 Task만 표시 (또는 전체 표시)
        is_completed = any(
            e.get('event_type') == 'COMPLETE' or e.get('type') == 'COMPLETE' 
            for e in events
        )

        if is_completed or show_all:
            print(f"\n📌 {task_name}")
            print("-"*70)

            # 주요 이벤트만 표시
            for i, event in enumerate(events):
                event_type = event.get('event_type') or event.get('type', 'UNKNOWN')
                timestamp = event.get('timestamp', event.get('ts', ''))[:19]

                # 중요 이벤트만 표시
                if event_type in ['TASK_INFO', 'TODO', 'COMPLETE', 'BLOCKER']:
                    print(f"  [{event_type:<10}] {timestamp}")

                    if event_type == 'TASK_INFO':
                        print(f"    제목: {event.get('title', 'N/A')}")
                        print(f"    예상: {event.get('estimate', 'N/A')}")
                        
                    elif event_type == 'TODO':
                        todos = event.get('todos', [])
                        if todos:
                            print(f"    TODO: {len(todos)}개 항목")
                            for j, todo in enumerate(todos[:5], 1):  # 최대 5개만 표시
                                print(f"      {j}. {todo}")
                            if len(todos) > 5:
                                print(f"      ... 외 {len(todos)-5}개 더")
                        else:
                            print("    TODO: 항목 없음")
                            
                    elif event_type == 'COMPLETE':
                        summary = event.get('summary', '')
                        if summary:
                            print("    완료 요약:")
                            # 이스케이프된 줄바꿈 문자를 실제 줄바꿈으로 변환
                            summary_text = summary.replace('\\n', '\n')
                            lines = summary_text.strip().split('\n')
                            
                            # 최대 10줄까지만 표시
                            for line in lines[:10]:
                                line = line.strip()
                                if line:
                                    # 긴 줄은 80자에서 자르기
                                    if len(line) > 80:
                                        print(f"      {line[:77]}...")
                                    else:
                                        print(f"      {line}")
                            
                            if len(lines) > 10:
                                print(f"      ... ({len(lines)-10}줄 더)")
                                
                    elif event_type == 'BLOCKER':
                        issue = event.get('issue', '')
                        severity = event.get('severity', 'N/A')
                        print(f"    ❌ 이슈: {issue}")
                        print(f"    심각도: {severity}")

            print(f"\n  📊 총 {len(events)}개 이벤트")
