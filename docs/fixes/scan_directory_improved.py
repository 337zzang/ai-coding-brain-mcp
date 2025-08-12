def scan_directory(path='.', max_depth=None, format='tree'):
    """재귀적 디렉토리 스캔 (깊이 제한 포함)

    Args:
        path: 스캔할 경로
        max_depth: 최대 깊이 (None = 무제한)
        format: 반환 형식 ('tree'|'flat'|'list')
            - tree: {'path': str, 'structure': list[dict]} (기존)
            - flat: {path: {'type': str, 'size': int}, ...} (새로운)
            - list: [path1, path2, ...] (간단)

    Returns:
        HelperResult with scan data
    """
    try:
        p = resolve_project_path(path)

        if not p.exists():
            return err(f"Directory not found: {path}")

        def scan_recursive(dir_path, current_depth=0):
            items = []

            if max_depth is not None and current_depth >= max_depth:
                return items

            try:
                for item in sorted(dir_path.iterdir()):
                    try:
                        stat = item.stat()
                        item_info = {
                            'name': item.name,
                            'type': 'directory' if item.is_dir() else 'file',
                            'size': stat.st_size,
                            'path': str(item.relative_to(p))
                        }

                        if item.is_dir() and not item.name.startswith('.'):
                            children = scan_recursive(item, current_depth + 1)
                            if children:
                                item_info['children'] = children

                        items.append(item_info)
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                pass

            return items

        structure = scan_recursive(p)

        # 형식별 반환
        if format == 'flat':
            # 평면 dict 형식으로 변환
            flat_result = {}

            def flatten(items, prefix=''):
                for item in items:
                    full_path = item['path'] if prefix == '' else f"{prefix}/{item['name']}"
                    flat_result[full_path] = {
                        'type': item['type'],
                        'size': item.get('size', 0)
                    }
                    if 'children' in item:
                        flatten(item['children'], full_path)

            flatten(structure)
            return ok(flat_result)

        elif format == 'list':
            # 단순 경로 리스트
            path_list = []

            def collect_paths(items):
                for item in items:
                    path_list.append(item['path'])
                    if 'children' in item:
                        collect_paths(item['children'])

            collect_paths(structure)
            return ok(path_list)

        else:  # format == 'tree' (기본)
            return ok({'path': str(p), 'structure': structure})

    except Exception as e:
        return err(f"Scan directory error: {str(e)}")
