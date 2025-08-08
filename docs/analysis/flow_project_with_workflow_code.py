def flow_project_with_workflow(
    project: str,
    *,
    auto_read_docs: bool = True,
    readme_lines: int = 60,
    file_dir_lines: int = 120
) -> Dict[str, Any]:
    """
    프로젝트 전환 & 워크플로우 초기화 + README / file_directory 자동 출력

    # 이제 os.chdir를 사용하지 않고 Session을 통해 프로젝트를 관리합니다.

    Parameters
    ----------
    project : str
        프로젝트 디렉토리 이름 (바탕화면에서 검색)
    auto_read_docs : bool
        True 이면 README.md 와 file_directory.md 를 자동 출력
    readme_lines / file_dir_lines : int
        각각 출력할 최대 줄 수
    """
    # Import here to avoid circular imports
    from .session import get_current_session
    from .flow_context import ProjectContext, find_project_path

    # 1) 프로젝트 찾기
    project_path = find_project_path(project)

    if not project_path:
        print(f"❌ 프로젝트를 찾을 수 없습니다: {project}")
        print(f"\n💡 팁: PROJECT_BASE_PATH 환경변수를 설정하여 기본 경로를 지정할 수 있습니다.")
        return err(f"프로젝트를 찾을 수 없습니다: {project}")

    # # 2) Session을 통해 프로젝트 설정 (os.chdir 없이)
    session = get_current_session()
    previous_project = session.get_project_name()

    try:
        # 프로젝트 설정
        project_ctx = session.set_project(project, str(project_path))
    except Exception as e:
        return err(f"프로젝트 설정 실패: {e}")

    # 캐시 리셋
    global _current_project_cache
    _current_project_cache = None

    # 3) 프로젝트 정보 수집
    proj_info = project_ctx.get_project_info()

    # 캐시 파일 업데이트
    try:
        cache_dir = Path.home() / ".ai-coding-brain" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = proj_info.copy()
        cache_data['switched_at'] = datetime.now().isoformat()
        cache_data['previous_project'] = previous_project

        with open(cache_dir / "current_project.json", 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except:
        pass  # 캐시 실패는 무시

    # 4) 기본 정보 출력
    print(f"✅ 프로젝트 전환: {project}")
    print(f"📍 경로: {project_path}")
    print(f"📁 Flow 저장소: {project}/.ai-brain/flow/")
    if previous_project and previous_project != project:
        print(f"   (이전: {previous_project})")

    # 5) 문서 자동 읽기
    docs: Dict[str, str] = {}
    if auto_read_docs:
        # ProjectContext의 read_file 메서드 사용
        readme_txt = project_ctx.read_file("readme.md")
        if readme_txt:
            # 줄 수 제한
            lines = readme_txt.split('\n')[:readme_lines]
            readme_txt = '\n'.join(lines)
            docs["readme.md"] = readme_txt
            print("\n📖 README.md 내용:")
            print("=" * 70)
            print(readme_txt)

        fd_txt = project_ctx.read_file("file_directory.md")
        if fd_txt:
            # 줄 수 제한
            lines = fd_txt.split('\n')[:file_dir_lines]
            fd_txt = '\n'.join(lines)
            docs["file_directory.md"] = fd_txt
            print("\n📁 프로젝트 구조 (file_directory.md):")
            print("=" * 70)
            print(fd_txt)

        # 5.5) 최신 플랜 표시 (v75.0)
    try:
        from .flow_api import FlowAPI
        flow_api = FlowAPI()

        # 최신 플랜 3개 가져오기
        plans_result = flow_api.list_plans(limit=3)
        if plans_result['ok'] and plans_result['data']:
            plans = plans_result['data']
            print(f"\n📋 최신 플랜 {len(plans)}개:")
            print("=" * 60)

            for i, plan in enumerate(plans, 1):
                # 플랜은 dict 형태로 반환됨
                print(f"\n{i}. {plan['name']}")
                print(f"   ID: {plan['id']}")
                print(f"   생성일: {plan['created_at']}")
                print(f"   상태: {plan.get('status', 'active')}")

                # Task 상태 분석
                tasks = plan.get('tasks', {})
                if tasks:
                    task_statuses = {}
                    for task_id, task in tasks.items():
                        # Task도 dict 형태
                        status = task.get('status', 'todo')
                        # TaskStatus enum 값 처리
                        if hasattr(status, 'value'):
                            status = str(status)
                        task_statuses[status] = task_statuses.get(status, 0) + 1

                    print(f"   Tasks: {len(tasks)}개", end="")
                    if task_statuses:
                        status_str = ", ".join([f"{status}: {count}" for status, count in task_statuses.items()])
                        print(f" ({status_str})")
                    else:
                        print()
                else:
                    print("   Tasks: 0개")
        elif plans_result['ok']:
            print("\n📋 생성된 플랜이 없습니다.")
    except Exception as e:
        # 플랜 표시 실패는 전체 함수 실패로 이어지지 않도록
        print(f"\n⚠️ 플랜 표시 중 오류 발생: {type(e).__name__}: {e}")
        pass

    print("\n✅ 플랜 섹션 완료, Git 섹션으로 이동...")

                # 6) Git 상태 (프로젝트 경로 기준)
    print("\n🔍 Git 섹션 시작...")
    git_info = None
    try:
        # git_status는 이미 ai_helpers_new에서 사용 가능
        import ai_helpers_new as helpers
        print("Helpers import 성공")
        git_result = helpers.git_status()
        print(f"Git status 결과: {git_result['ok']}")

        if git_result['ok']:
            git_data = git_result['data']
            files = git_data.get('files', [])
            branch = git_data.get('branch', 'unknown')
            clean = git_data.get('clean', False)

            git_info = {
                'branch': branch,
                'files': files,
                'count': len(files),
                'clean': clean
            }

            print(f"\n🔀 Git 상태:")
            print("============================================================")
            print(f"브랜치: {branch}")
            print(f"변경 파일: {len(files)}개")
            print(f"상태: {'Clean' if clean else 'Modified'}")
    except Exception as e:
        # Git 상태 실패는 전체 함수 실패로 이어지지 않도록
        print(f"\n⚠️ Git 상태 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        pass


    # 7) Flow 상태
    flow_info = None
    try:
        from .simple_flow_commands import flow as flow_cmd
        flow_status = flow_cmd("/status")
        if flow_status and flow_status.get('ok'):
            flow_info = flow_status.get('data')
            # Flow 상태는 이미 출력되므로 추가 출력 불필요
    except:
        pass

    # 8) 결과 반환
    result_data = {
        'project': project,
        'project_name': project,  # 일관성을 위해 추가
        'path': str(project_path),
        'info': proj_info,
        'docs': docs,
        'git': git_info,
        'flow': flow_info,
        'switched_from': previous_project
    }

    return ok(result_data)
# 나머지 함수들은 그대로 유지
@safe_execution