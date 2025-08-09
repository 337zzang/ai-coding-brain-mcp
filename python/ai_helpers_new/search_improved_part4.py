
# Part 4: 코드 검색 함수들 (성능 최적화)

def search_code(
    pattern: str,
    path: str = ".",
    file_pattern: str = "*.py",
    max_results: int = 100,
    context_lines: int = 0,
    use_regex: bool = True,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    개선된 코드 검색 - 제너레이터 기반으로 조기 종료 지원
    grep 기능 통합 (context_lines, case_sensitive 옵션)
    """
    results = []

    # 패턴 컴파일
    if use_regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {'ok': False, 'error': f"Invalid regex: {e}"}
    else:
        # 리터럴 검색
        search_pattern = pattern if case_sensitive else pattern.lower()

    # 제너레이터 기반 파일 탐색
    for file_path in search_files_generator(path, file_pattern):
        if is_binary_file(file_path):
            continue

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for line_num, line in enumerate(f, 1):
                    lines.append(line.rstrip())

                    # 매치 확인
                    matched = False
                    if use_regex:
                        matched = regex.search(line)
                    else:
                        test_line = line if case_sensitive else line.lower()
                        matched = search_pattern in test_line

                    if matched:
                        # 컨텍스트 수집
                        start = max(0, line_num - context_lines - 1)
                        end = min(len(lines), line_num + context_lines)

                        results.append({
                            'file': file_path,
                            'line': line_num,
                            'match': line.rstrip(),
                            'context': lines[start:end] if context_lines > 0 else None
                        })

                        # 조기 종료
                        if len(results) >= max_results:
                            return {'ok': True, 'data': results}

        except (PermissionError, UnicodeDecodeError, IOError) as e:
            logger.debug(f"Cannot read {file_path}: {e}")
            continue

    return {'ok': True, 'data': results}

def find_in_file(
    file_path: str,
    pattern: str,
    context_lines: int = 2
) -> Dict[str, Any]:
    """
    단일 파일 내 검색 (수정됨: h.search_code 대신 search_code 호출)
    """
    # 파일이 존재하는지 확인
    if not os.path.isfile(file_path):
        return {'ok': False, 'error': f"File not found: {file_path}"}

    # search_code를 직접 호출 (h.search_code 대신)
    result = search_code(
        pattern,
        os.path.dirname(file_path) or '.',
        os.path.basename(file_path),
        context_lines=context_lines
    )

    return result

def grep(
    pattern: str,
    path: str = ".",
    context: int = 2,
    file_pattern: str = "*.py",
    use_regex: bool = False
) -> Dict[str, Any]:
    """
    grep 스타일 검색 - search_code로 리다이렉트
    """
    return search_code(
        pattern=pattern,
        path=path,
        file_pattern=file_pattern,
        context_lines=context,
        use_regex=use_regex,
        case_sensitive=False
    )
