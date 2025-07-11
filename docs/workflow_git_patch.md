# WorkflowCommands Git 연계 개선 패치

## 1. complete_current_task 메서드 개선

    def complete_current_task(self, summary: str, details: list = None, 
                            outputs: dict = None, issues: list = None, 
                            next_steps: list = None) -> Dict[str, Any]:
        """현재 작업 완료 (Git 연계 개선)"""
        current_task = self.workflow.get_current_task()
        if not current_task:
            return {'error': '현재 작업이 없습니다.'}

        # 결과 데이터 구성
        result = {
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }

        if details:
            result['details'] = details
        if outputs:
            result['outputs'] = outputs
        if issues:
            result['issues'] = issues
        if next_steps:
            result['next_steps'] = next_steps

        # Git 상태 확인 및 관련 파일 추가
        try:
            from ..utils.git_task_helpers import get_task_related_files
            git_files = get_task_related_files()
            if any(git_files.values()):
                result['git_changes'] = git_files
                print(f"  📁 변경된 파일: {sum(len(v) for v in git_files.values())}개")
        except:
            pass

        # 작업 완료 처리
        current_task.status = TaskStatus.COMPLETED
        current_task.completed_at = datetime.now().isoformat()
        current_task.result = result

        self.workflow.complete_task(current_task.id, summary)

        # Git 자동 커밋 (환경변수 확인)
        auto_commit = os.getenv('AUTO_GIT_COMMIT', 'false').lower() == 'true'
        if auto_commit:
            try:
                from ..utils.git_task_helpers import create_task_commit, push_commits

                # 커밋 생성
                commit_result = create_task_commit(
                    task_title=current_task.title,
                    task_id=current_task.id,
                    summary=summary
                )

                if commit_result['success']:
                    # 커밋 ID를 작업 결과에 추가
                    current_task.result['commit_id'] = commit_result['commit_id']
                    result['commit_id'] = commit_result['commit_id']
                    print(f"  🔗 Git 커밋: {commit_result['commit_id'][:8]}")

                    # Push 시도
                    if push_commits():
                        print("  📤 원격 저장소에 푸시 완료")
                    else:
                        print("  ⚠️ 푸시 실패 (수동으로 푸시 필요)")
                else:
                    print(f"  ⚠️ 커밋 실패: {commit_result['message']}")

            except Exception as e:
                print(f"  ❌ Git 연동 오류: {e}")
        else:
            print("  ℹ️ 자동 커밋 비활성화 (AUTO_GIT_COMMIT=true로 활성화)")

        # 워크플로우 저장
        self.workflow.save_data()

        return {
            'task_id': current_task.id,
            'title': current_task.title,
            'completed': True,
            'result': result
        }


## 2. handle_done 메서드 개선  

    def handle_done(self, *args) -> Dict[str, Any]:
        """작업 완료 명령 (/done, /complete)"""
        # 요약 정보 파싱
        summary = ' '.join(args) if args else "작업 완료"

        # Git 상태 표시
        try:
            from ..utils.git_task_helpers import get_task_related_files
            git_files = get_task_related_files()
            total_changes = sum(len(v) for v in git_files.values())
            if total_changes > 0:
                print(f"\n📊 Git 변경사항:")
                if git_files['modified']:
                    print(f"  수정: {len(git_files['modified'])}개")
                if git_files['added']:
                    print(f"  추가: {len(git_files['added'])}개")
                if git_files['untracked']:
                    print(f"  미추적: {len(git_files['untracked'])}개")
        except:
            pass

        # 작업 완료 처리
        result = self.complete_current_task(summary)

        if 'error' not in result:
            print(f"\n✅ 작업 완료: {result['title']}")
            if result['result'].get('commit_id'):
                print(f"   커밋 ID: {result['result']['commit_id'][:8]}")
        else:
            print(f"\n❌ {result['error']}")

        return result


## 추가 필요 import:
- from ..utils.git_task_helpers import get_task_related_files, create_task_commit, push_commits
