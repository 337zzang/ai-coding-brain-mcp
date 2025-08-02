def flow_project_with_workflow(
    project: str,
    auto_read_docs: bool = True,
    readme_lines: int = 9999,
    file_dir_lines: int = 9999
) -> Dict[str, Any]:
    """
    프로젝트 전환 & 워크플로우 초기화 + README / file_directory 자동 출력

    개선사항:
    1. 환경변수 PROJECT_BASE_PATH 지원
    2. 다양한 기본 경로 시도
    3. os.chdir 제거 (향후 구현)
    """
    import os
    import platform
    from pathlib import Path

    # 1) 프로젝트 기본 경로 결정
    # 우선순위: 환경변수 > 플랫폼별 기본값
    base_paths = []

    # 환경변수 확인
    if os.environ.get('PROJECT_BASE_PATH'):
        base_paths.append(Path(os.environ['PROJECT_BASE_PATH']))

    # 플랫폼별 기본 경로 추가
    home = Path.home()
    system = platform.system()

    if system == 'Windows':
        base_paths.extend([
            home / "Desktop",
            home / "바탕화면",
            home / "Documents",
            home / "문서"
        ])
    elif system == 'Darwin':  # macOS
        base_paths.extend([
            home / "Desktop",
            home / "Documents",
            home / "Developer"
        ])
    else:  # Linux 및 기타
        base_paths.extend([
            home / "Desktop",
            home / "Documents",
            home / "projects",
            home
        ])

    # 2) 프로젝트 찾기
    project_path = None
    searched_paths = []

    for base_path in base_paths:
        if base_path.exists():
            candidate = base_path / project
            searched_paths.append(str(base_path))
            if candidate.exists() and candidate.is_dir():
                project_path = candidate
                break

    if not project_path:
        print(f"❌ 프로젝트를 찾을 수 없습니다: {project}")
        print(f"   검색한 경로들:")
        for path in searched_paths:
            print(f"   - {path}")
        print("\n💡 팁: PROJECT_BASE_PATH 환경변수를 설정하여 기본 경로를 지정할 수 있습니다.")
        return err(f"프로젝트를 찾을 수 없습니다: {project}")

    # 3) 디렉토리 이동 (향후 제거 예정)
    try:
        previous_dir = os.getcwd()
        os.chdir(str(project_path))
    except OSError as e:
        return err(f"디렉토리 이동 실패: {e}")

    # ... 나머지 코드는 동일
