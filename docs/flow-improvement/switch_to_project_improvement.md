# _switch_to_project 메서드 개선안

## 현재 코드 (Line 915-954)
최신 Plan만 표시하고 있음

## 개선된 코드
모든 Plan 리스트를 상태 아이콘과 함께 표시

```python

        # 6. 모든 Plan 리스트 표시 (개선된 부분)
        if self.current_flow.get('plans'):
            result_lines.append(f"\n📋 Plan 목록 ({len(self.current_flow['plans'])}개):\n")

            for i, plan in enumerate(self.current_flow['plans']):
                plan_id = plan.get('id', 'N/A')
                plan_name = plan.get('name', 'Unnamed')
                tasks = plan.get('tasks', [])
                total_tasks = len(tasks)
                completed_tasks = sum(1 for t in tasks if t.get('status') in ['completed', 'reviewing'])

                # Plan 완료 상태 확인
                plan_completed = plan.get('completed', False)

                # 상태 아이콘 결정
                if plan_completed:
                    status_icon = "✅"  # Plan 완료됨
                elif total_tasks == 0:
                    status_icon = "📋"  # Task가 없음
                elif completed_tasks == total_tasks and total_tasks > 0:
                    status_icon = "🔄"  # 모든 Task 완료했지만 Plan은 미완료
                elif completed_tasks > 0:
                    status_icon = "⏳"  # 진행중
                else:
                    status_icon = "📝"  # 시작 전

                result_lines.append(f"{i+1}. {status_icon} Plan: {plan_name}")
                result_lines.append(f"   - ID: {plan_id}")
                result_lines.append(f"   - Tasks: {total_tasks}개 (완료: {completed_tasks}개)")

                # 진행률 표시
                if total_tasks > 0:
                    progress = (completed_tasks / total_tasks) * 100
                    progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
                    result_lines.append(f"   - 진행률: [{progress_bar}] {progress:.0f}%")

                # Plan 설명이 있으면 표시
                if plan.get('description'):
                    result_lines.append(f"   - 설명: {plan['description']}")

                result_lines.append("")  # 빈 줄 추가

            # Plan 선택 가이드 추가
            result_lines.append("\n💡 Plan을 선택하려면 번호를 입력하거나 'Plan X 선택' 형식으로 입력하세요.")
            result_lines.append("   예: '2' 또는 'Plan 2 선택'")

```

## 수정 위치
- 파일: `python/ai_helpers_new/flow_manager_unified.py`
- Line 915의 "# 6. 최신 플랜 확인" 부분을 위 코드로 교체

## 예상 출력
```
📋 'ai-coding-brain-mcp' 프로젝트의 Plan 목록 (5개):

1. 📝 Plan: 테스트 및 검증
   - ID: plan_20250721_161610
   - Tasks: 4개 (완료: 0개)
   - 진행률: [░░░░░░░░░░] 0%

2. ⏳ Plan: Flow 시스템 코드 분석 및 문제 진단
   - ID: plan_1753149197141390900_b925ef
   - Tasks: 4개 (완료: 2개)
   - 진행률: [█████░░░░░] 50%

...

💡 Plan을 선택하려면 번호를 입력하거나 'Plan X 선택' 형식으로 입력하세요.
   예: '2' 또는 'Plan 2 선택'
```
