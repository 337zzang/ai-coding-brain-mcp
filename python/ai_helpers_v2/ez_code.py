"""
초간단 코드 파싱 및 교체 도구 (Easy Code Tools)
REPL 환경에서 쉽게 사용할 수 있는 최소한의 코드 수정 도구
"""
import ast
import shutil
from datetime import datetime

def ez_parse(filepath):
    """파일의 함수/클래스 구조를 파싱"""
    import ast

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        lines = content.split('\n')

        # 최상위 클래스 노드 수집
        class_nodes = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_nodes[node.name] = node

        items = {}

        # 모든 함수/클래스 찾기
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # 부모 클래스 찾기
                parent_class = None
                for class_name, class_node in class_nodes.items():
                    if node != class_node and _is_node_in_class(node, class_node):
                        parent_class = class_name
                        break

                # 이름 결정
                if parent_class and isinstance(node, ast.FunctionDef):
                    name = f"{parent_class}.{node.name}"
                else:
                    name = node.name

                # 위치 계산
                start = node.lineno - 1
                end = _find_block_end(lines, start)

                items[name] = (start, end)

        return items

    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
        return {}


def _is_node_in_class(node, class_node):
    """노드가 클래스 내부에 있는지 확인"""
    for child in ast.walk(class_node):
        if child == node:
            return True
    return False


def _find_block_end(lines, start_line):
    """블록의 끝 찾기"""
    if start_line >= len(lines):
        return start_line

    start_indent = len(lines[start_line]) - len(lines[start_line].lstrip())

    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        if not line.strip() or line.strip().startswith('#'):
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent <= start_indent:
            return i - 1

    return len(lines) - 1


def ez_replace(filepath, target_name, new_code, backup=True):
    """초간단 코드 교체 - 자동 백업 포함

    Args:
        filepath: 대상 파일
        target_name: 교체할 함수/클래스 이름 (예: "func" 또는 "Class.method")
        new_code: 새로운 코드
        backup: 백업 생성 여부

    Returns:
        str: 결과 메시지
    """
    # 백업 생성
    if backup:
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
    else:
        backup_path = None

    # 파싱
    items = ez_parse(filepath)
    if target_name not in items:
        available = ', '.join(sorted(items.keys()))
        return f"❌ '{target_name}' not found. Available: {available}"

    # 교체 준비
    start, end = items[target_name]

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 들여쓰기 계산
    indent = len(lines[start]) - len(lines[start].lstrip())
    new_lines = []

    # 새 코드 처리
    for i, line in enumerate(new_code.strip().split('\n')):
        if i == 0:
            # 첫 줄은 원본 들여쓰기 사용
            new_lines.append(' ' * indent + line.lstrip() + '\n')
        else:
            # 나머지는 상대적 들여쓰기 유지
            new_lines.append(' ' * indent + line + '\n')

    # 교체 실행
    lines[start:end+1] = new_lines

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    msg = f"✅ Replaced {target_name} ({end-start+1} → {len(new_lines)} lines)"
    if backup_path:
        msg += f"\n   Backup: {backup_path}"

    return msg


def ez_view(filepath, target_name=None):
    """코드 요소 보기

    Args:
        filepath: 파일 경로
        target_name: 특정 요소 이름 (None이면 전체 목록)

    Returns:
        str: 코드 또는 목록
    """
    items = ez_parse(filepath)

    if target_name:
        if target_name not in items:
            return f"❌ '{target_name}' not found"

        start, end = items[target_name]
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        code = ''.join(lines[start:end+1])
        return f"📍 {target_name} (L{start+1}-{end+1}):\n{code}"
    else:
        # 전체 목록
        result = f"📄 {filepath} - {len(items)} items:\n"
        for name, (start, end) in sorted(items.items()):
            result += f"  - {name}: L{start+1}-{end+1}\n"
        return result


# 사용 예시
if __name__ == "__main__":
    print("🚀 Easy Code Tools")
    print("=" * 50)
    print("Usage:")
    print("  items = ez_parse('file.py')")
    print("  result = ez_replace('file.py', 'function_name', new_code)")
    print("  code = ez_view('file.py', 'function_name')")

# 안전한 교체 함수 (문법 검증 포함)
def ez_replace_safe(filepath, target_name, new_code, backup=True, validate=True):
    """안전한 코드 교체 - 문법 검증 및 자동 롤백 지원"""
    try:
        from .safe_code_modifier import SafeCodeModifier
    except ImportError:
        from safe_code_modifier import SafeCodeModifier

    modifier = SafeCodeModifier(auto_backup=backup, validate_syntax=validate)
    result = modifier.safe_replace(filepath, target_name, new_code)

    if result['success']:
        msg = f"✅ Replaced {target_name} ({result['lines_changed']} → {result['new_lines']} lines)"
        if result['backup_path']:
            msg += f"\n   Backup: {result['backup_path']}"
        return msg
    else:
        return f"❌ 교체 실패: {result['error']}"
