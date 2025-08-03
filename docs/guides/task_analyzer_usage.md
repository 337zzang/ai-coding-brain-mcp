# Task Analyzer 사용 가이드

## 📋 사용 예시 1: 특정 Task의 로그 분석
```python
# Task 로그 조회
log_result = h.get_task_log(plan_id, task_id)

if log_result['ok']:
    data = log_result['data']
    print(f"Task 완료 메시지: {data['completion_message']}")
    print(f"총 이벤트 수: {data['summary']['total_events']}")
    print(f"코드 변경: {len(data['summary']['code_changes'])}건")
    print(f"생성된 파일: {', '.join(data['created_files'])}")
    
    # 주요 의사결정 확인
    for decision in data['summary']['decisions']:
        print(f"결정: {decision['title']} → {decision['choice']}")
```

## 📋 사용 예시 2: 이전 Task 컨텍스트 확인
```python
# 현재 Task 시작 전에 이전 작업 확인
context = h.get_previous_task_context(plan_id, current_task_id)

if context['ok']:
    prev = context['data']
    
    if prev['previous_task']:
        print(f"\n📍 이전 Task: {prev['previous_task']['title']}")
        print(f"✅ 완료: {prev['log_summary']['completion_message']}")
        print(f"📊 작업량: {prev['log_summary']['code_changes']}개 파일 수정")
        
        # Git 변경사항
        if prev['git_changes']['modified_files']:
            print(f"\n📝 변경된 파일:")
            for file in prev['git_changes']['modified_files']:
                print(f"  - {file}")
        
        # 미완료 사항
        if prev['unfinished_items']:
            print(f"\n⚠️ 주의사항:")
            for item in prev['unfinished_items']:
                print(f"  - {item['description']}")
    else:
        print("첫 번째 Task입니다.")
```

## 📋 Task 시작 시 자동 컨텍스트 표시
```python
def start_task_with_context(task_id):
    # 현재 Plan 정보
    manager = h.get_flow_manager()
    current_plan = manager.get_current_plan()
    
    if not current_plan:
        print("❌ 현재 선택된 Plan이 없습니다.")
        return
    
    # 이전 Task 컨텍스트 로드
    context = h.get_previous_task_context(current_plan.id, task_id)
    
    if context['ok'] and context['data']['previous_task']:
        prev = context['data']
        
        print("\n" + "="*60)
        print(f"🌿 Task 시작: 이전 작업 컨텍스트")
        print("="*60)
        print(f"\n📍 이전 Task: {prev['previous_task']['title']}")
        print(f"✅ 완료 메시지: {prev['log_summary']['completion_message']}")
        print(f"📊 코드 변경: {prev['log_summary']['code_changes']}건")
        
        if prev['log_summary']['decisions']:
            print(f"\n💡 주요 결정사항:")
            for decision in prev['log_summary']['decisions']:
                print(f"  - {decision['title']}: {decision['choice']}")
        
        if prev['git_changes']['created_files']:
            print(f"\n📄 생성된 파일:")
            for file in prev['git_changes']['created_files']:
                print(f"  - {file}")
        
        print("\n" + "="*60)
        print("위 컨텍스트를 바탕으로 Task를 진