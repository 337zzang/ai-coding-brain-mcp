"""워크플로우 상태 표시 함수"""
from pathlib import Path
import json
import textwrap

def show_workflow_status_improved():
    """workflow.json 기반 워크플로우 진행 현황 표시"""
    wf_path = Path('memory/workflow.json')
    if not wf_path.exists():
        print('ℹ️  워크플로우가 아직 설정되지 않았습니다.')
        print('   💡 /plan 명령으로 새 계획을 시작할 수 있습니다.')
        return
        
    try:
        data = json.loads(wf_path.read_text(encoding='utf-8'))
        current_id = data.get('current_plan_id')
        
        if not current_id:
            print('ℹ️  활성 플랜이 없습니다.')
            print('   💡 /plan 명령으로 새 계획을 시작할 수 있습니다.')
            return
            
        # plans는 배열이므로 직접 탐색
        plan = next((p for p in data.get('plans', []) if p['id'] == current_id), None)
        if not plan:
            print('⚠️  플랜 정보가 손상되었습니다.')
            return
            
        tasks = plan.get('tasks', [])
        done = sum(1 for t in tasks if t.get('status') == 'completed')
        
        # 출력
        bar = '━' * 50
        print(f"\n{bar}")
        print(f"📋 워크플로우: {plan['name']} ({done}/{len(tasks)} 완료)")
        
        if plan.get('description'):
            print(f"📝 설명: {textwrap.shorten(plan['description'], 70)}")
            
        if tasks:
            print("\n📌 작업 목록:")
            for i, t in enumerate(tasks, 1):
                status_icon = '✅' if t.get('status') == 'completed' else '🔧' if t.get('status') == 'in_progress' else '⏳'
                approval = ' (승인됨)' if t.get('approval_status') == 'approved' else ''
                print(f"   {i}. {status_icon} {t['title']}{approval}")
                
        print(f"{bar}")
        print("💡 /status로 상세 정보, /next로 다음 작업 진행\n")
    except Exception as e:
        print(f'⚠️  워크플로우 상태 표시 중 오류: {e}')
