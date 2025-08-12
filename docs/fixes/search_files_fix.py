
# search.py 수정 제안

def search_files(pattern, path="."):
    """파일 검색 (경로 처리 개선)"""
    try:
        # 경로 정규화
        if not os.path.isabs(path):
            path = os.path.join(get_project_root(), path)

        # 패턴 정규화
        if not pattern.startswith("*"):
            pattern = f"*{pattern}*"

        # glob 검색
        search_path = os.path.join(path, "**", pattern)
        files = glob.glob(search_path, recursive=True)

        # 상대 경로로 변환
        project_root = get_project_root()
        relative_files = [
            os.path.relpath(f, project_root) 
            for f in files
        ]

        return HelperResult(
            ok=True,
            data=relative_files
        )
    except Exception as e:
        return HelperResult(
            ok=False,
            error=str(e),
            data=[]
        )
