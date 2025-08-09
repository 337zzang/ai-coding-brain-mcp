
# Part 2: 파일 탐색 제너레이터

def search_files_generator(
    path: str, 
    pattern: str = "*",
    max_depth: Optional[int] = None,
    exclude_patterns: Optional[set] = None
) -> Generator[str, None, None]:
    """
    파일을 발견하는 즉시 yield하는 제너레이터
    메모리 효율적이고 조기 종료 가능
    """
    exclude_patterns = exclude_patterns or {'.git', '__pycache__', 'node_modules'}
    base_path = Path(path).resolve()

    def should_exclude(file_path: Path) -> bool:
        for part in file_path.parts:
            if any(pattern in part for pattern in exclude_patterns):
                return True
        return False

    def walk_with_depth(current_path: Path, current_depth: int = 0):
        if max_depth is not None and current_depth > max_depth:
            return

        try:
            for item in current_path.iterdir():
                if should_exclude(item):
                    continue

                if item.is_file():
                    if pattern == "*" or item.match(pattern):
                        yield str(item)
                elif item.is_dir():
                    yield from walk_with_depth(item, current_depth + 1)
        except (PermissionError, OSError) as e:
            logger.debug(f"Cannot access {current_path}: {e}")

    yield from walk_with_depth(base_path)
