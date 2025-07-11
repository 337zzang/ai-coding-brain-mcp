# 개선된 워크플로우 명령어 메서드들 (v2.0 구조 지원)

def handle_list(self, *args) -> Dict[str, Any]:
    """플랜 목록 조회 (/list)
    - 현재 플랜과 히스토리 표시
    """
    try:
        # 현재 플랜
        current_plan = self.workflow.get_current_plan()

        # 히스토리
        history = self.workflow.get_history()

        # 출력 구성
        output = []
        output.append("📋 워크플로우 플랜 목록\n")

        # 현재 플랜
        if current_plan:
            output.append("✅ 현재 활성 플랜:")
            output.append(f"   - {current_plan.name}")
            output.append(f"   - 진행률: {current_plan.get_progress():.1f}%")
            output.append(f"   - 작업: {len(current_plan.tasks)}개")
            output.append(f"   - ID: {current_plan.id[:8]}...")
        else:
            output.append("⚠️ 활성 플랜이 없습니다.")

        # 히스토리
        if history:
            output.append("\n📚 히스토리 (최근 5개):")
            for i, hist in enumerate(history[-5:]):
                if isinstance(hist, dict) and 'plan' in hist:
                    plan_data = hist['plan']
                    archived_at = hist.get('archived_at', 'Unknown')
                    output.append(f"   {i+1}. {plan_data.get('name', 'Unknown')}")
                    output.append(f"      - 보관일: {archived_at[:10]}")
                    output.append(f"      - 이유: {hist.get('reason', 'unknown')}")
        else:
            output.append("\n📚 히스토리가 비어있습니다.")

        result = '\n'.join(output)
        print(result)

        return {
            'plans': [{
                'id': current_plan.id if current_plan else None,
                'name': current_plan.name if current_plan else None,
                'active': True,
                'progress': current_plan.get_progress() if current_plan else 0
            }] if current_plan else [],
            'history_count': len(history)
        }

    except Exception as e:
        error_msg = f"플랜 목록 조회 중 오류: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}


def handle_current(self, *args) -> Dict[str, Any]:
    """현재 활성 플랜 정보 (/current)"""
    try:
        current_plan = self.workflow.get_current_plan()

        if not current_plan:
            print("⚠️ 현재 활성 플랜이 없습니다.")
            return {'error': '활성 플랜이 없습니다.'}

        # 출력 구성
        output = []
        output.append(f"📌 현재 플랜: {current_plan.name}")
        output.append(f"\n📝 설명: {current_plan.description}")
        output.append(f"\n📊 진행 상황:")
        output.append(f"   - 전체 작업: {len(current_plan.tasks)}개")

        completed = sum(1 for t in current_plan.tasks if t.completed)
        in_progress = sum(1 for t in current_plan.tasks if t.status.value == 'in_progress')
        todo = len(current_plan.tasks) - completed - in_progress

        output.append(f"   - 완료: {completed}개")
        output.append(f"   - 진행중: {in_progress}개")
        output.append(f"   - 대기: {todo}개")
        output.append(f"   - 진행률: {current_plan.get_progress():.1f}%")

        # 현재 작업
        current_task = current_plan.get_current_task()
        if current_task:
            output.append(f"\n🔄 진행 중인 작업:")
            output.append(f"   - {current_task.title}")
            output.append(f"   - ID: {current_task.id[:8]}...")

        # 다음 작업
        next_task = current_plan.get_next_task()
        if next_task and next_task != current_task:
            output.append(f"\n⏭️ 다음 작업:")
            output.append(f"   - {next_task.title}")

        result = '\n'.join(output)
        print(result)

        return {
            'plan': {
                'id': current_plan.id,
                'name': current_plan.name,
                'description': current_plan.description,
                'progress': current_plan.get_progress(),
                'task_count': len(current_plan.tasks),
                'completed_count': completed,
                'in_progress_count': in_progress,
                'todo_count': todo
            },
            'current_task': {
                'id': current_task.id,
                'title': current_task.title
            } if current_task else None,
            'next_task': {
                'id': next_task.id,
                'title': next_task.title
            } if next_task else None
        }

    except Exception as e:
        error_msg = f"현재 플랜 조회 중 오류: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}


def handle_tasks(self, *args) -> Dict[str, Any]:
    """현재 플랜의 작업 목록 (/tasks)"""
    try:
        current_plan = self.workflow.get_current_plan()

        if not current_plan:
            print("⚠️ 활성 플랜이 없습니다.")
            return {'error': '활성 플랜이 없습니다.'}

        # 출력 구성
        output = []
        output.append(f"📋 작업 목록 - {current_plan.name}")
        output.append(f"\n전체 {len(current_plan.tasks)}개 작업:\n")

        for i, task in enumerate(current_plan.tasks):
            # 상태 아이콘
            if task.completed:
                icon = "✅"
            elif task.status.value == 'in_progress':
                icon = "🔄"
            elif task.status.value == 'blocked':
                icon = "🚫"
            else:
                icon = "⏳"

            output.append(f"{icon} {i+1}. {task.title}")

            # 상세 정보
            if task.description:
                output.append(f"      설명: {task.description}")

            # 시간 정보
            if task.started_at:
                output.append(f"      시작: {task.started_at[:16]}")
            if task.completed_at:
                output.append(f"      완료: {task.completed_at[:16]}")

            # Git 커밋 정보 (있으면)
            if task.result and task.result.get('commit_id'):
                output.append(f"      커밋: {task.result['commit_id'][:8]}")

            output.append("")  # 줄바꿈

        # 요약
        completed = sum(1 for t in current_plan.tasks if t.completed)
        output.append(f"\n📊 요약:")
        output.append(f"   - 완료: {completed}/{len(current_plan.tasks)}")
        output.append(f"   - 진행률: {current_plan.get_progress():.1f}%")

        result = '\n'.join(output)
        print(result)

        return {
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'status': task.status.value,
                    'completed': task.completed,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'commit_id': task.result.get('commit_id') if task.result else None
                }
                for task in current_plan.tasks
            ],
            'summary': {
                'total': len(current_plan.tasks),
                'completed': completed,
                'progress': current_plan.get_progress()
            }
        }

    except Exception as e:
        error_msg = f"작업 목록 조회 중 오류: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}
