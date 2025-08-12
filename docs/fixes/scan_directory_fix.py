
# file.py 수정 제안

def scan_directory(path=".", max_depth=2, format="flat"):
    """
    디렉토리 구조 스캔

    Args:
        path: 스캔할 경로
        max_depth: 최대 깊이
        format: 반환 형식 ('flat' | 'tree')

    Returns:
        flat: {file_path: {type, size}, ...}
        tree: {path: str, structure: list[dict]}
    """
    result = _scan_recursive(path, max_depth)

    if format == "flat":
        return _flatten_structure(result)
    else:
        return {"path": path, "structure": result}

def _flatten_structure(tree_structure):
    """Tree 구조를 평면 dict로 변환"""
    flat = {}

    def traverse(items, prefix=""):
        for item in items:
            full_path = os.path.join(prefix, item["name"])
            flat[full_path] = {
                "type": item["type"],
                "size": item.get("size", 0)
            }
            if "children" in item:
                traverse(item["children"], full_path)

    traverse(tree_structure)
    return flat
