def flow_project_with_workflow(project_name: str):
    """프로젝트 전환 및 컨텍스트 정보 자동 표시"""
    from pathlib import Path
    import json
    from datetime import datetime

    # 바탕화면 경로 찾기 (간소화)
    desktop_path = Path.home() / "Desktop"
    if not desktop_path.exists():
        desktop_path = Path.home() / "바탕화면"

    if not desktop_path.exists():
        return {
            "ok": False,
            "error": "바탕화면 경로를 찾을 수 없습니다"
        }

    # 프로젝트 경로 확인
    project_path = desktop_path / project_name
    if not project_path.exists() or not project_path.is_dir():
        print(f"❌ 프로젝트를 찾을 수 없음: {project_name}")
        print(f"   검색 경로: {desktop_path}")
        return {
            "ok": False,
            "error": f"프로젝트를 찾을 수 없음: {project_name}"
        }

    try:
        # 현재 디렉토리 저장 및 전환
        previous_dir = os.getcwd()
        os.chdir(str(project_path))

        # 프로젝트 정보 수집
        project_info = {
            "name": project_name,
            "path": str(project_path),
            "type": "node" if (project_path / "package.json").exists() else "python",
            "has_git": (project_path / ".git").exists(),
            "switched_at": datetime.now().isoformat()
        }

        # 캐시 업데이트
        cache_dir = Path.home() / ".ai-coding-brain" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        with open(cache_dir / "current_project.json", 'w', encoding='utf-8') as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)

        # 기본 정보 출력
        print(f"✅ 프로젝트 전환: {project_name}")
        print(f"📍 경로: {project_path}")
        print(f"📁 Flow 저장소: {project_name}/.ai-brain/flow/")

        # 🆕 README.md 자동 읽기 및 출력
        readme_path = project_path / "readme.md"
        if readme_path.exists():
            print("\n📖 README.md 내용:")
            print("=" * 70)
            try:
                # ai_helpers_new 임포트하여 사용
                import ai_helpers_new as h
                readme_content = h.read(str(readme_path), length=50)
                if readme_content['ok']:
                    print(readme_content['data'])
            except:
                # 폴백: 직접 읽기
                with open(readme_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:50]
                    print(''.join(lines))

        # 🆕 file_directory.md 자동 읽기 및 출력
        file_dir_path = project_path / "file_directory.md"
        if file_dir_path.exists():
            print("\n📁 프로젝트 구조:")
            print("=" * 70)
            try:
                import ai_helpers_new as h
                file_dir_content = h.read(str(file_dir_path), length=100)
                if file_dir_content['ok']:
                    print(file_dir_content['data'])
            except:
                with open(file_dir_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:100]
                    print(''.join(lines))

        # 🆕 Git 상태 표시
        if project_info["has_git"]:
            print("\n🔀 Git 상태:")
            print("=" * 70)
            try:
                import ai_helpers_new as h
                git_status = h.git_status()
                if git_status['ok']:
                    data = git_status['data']
                    print(f"브랜치: {data['branch']}")
                    print(f"변경 파일: {data['count']}개")
                    print(f"상태: {'Clean' if data['clean'] else 'Modified'}")
            except:
                pass

        # 🆕 Flow 상태 간단히 표시
        try:
            from .ultra_simple_flow_manager import UltraSimpleFlowManager
            manager = UltraSimpleFlowManager()
            plans = manager.list_plans()
            if plans:
                print(f"\n📊 Flow 시스템: {len(plans)}개 Plan 존재")
        except:
            pass

        return {
            "ok": True,
            "data": {
                "project": project_info,
                "previous": previous_dir
            }
        }

    except Exception as e:
        print(f"❌ 프로젝트 전환 실패: {e}")
        return {
            "ok": False,
            "error": str(e)
        }
