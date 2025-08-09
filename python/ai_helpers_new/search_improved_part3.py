
# Part 3: AST 기반 검색 (Python 3.8+ 지원)

@lru_cache(maxsize=256)
@_register_cache
def _load_ast_cached(file_path: str) -> tuple:
    """파일을 읽어 AST와 소스 텍스트를 캐싱"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, file_path)
        return tree, source
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.debug(f"Cannot parse {file_path}: {e}")
        return None, None

def _find_function_ast(
    file_path: str, 
    name: str,
    strict: bool = False
) -> Generator[Dict[str, Any], None, None]:
    """
    AST를 사용한 함수 검색
    Python 3.8+에서는 ast.get_source_segment 사용
    """
    tree, source = _load_ast_cached(file_path)
    if tree is None:
        return

    pattern = re.compile(name if strict else f".*{name}.*", re.IGNORECASE)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and pattern.search(node.name):
            # Python 3.8+ - 정확한 소스 추출
            if sys.version_info >= (3, 8):
                definition = ast.get_source_segment(source, node)
            else:
                # Python 3.7 이하 - 라인 기반 추출
                start_line = node.lineno - 1
                end_line = start_line + 50  # 합리적인 기본값
                lines = source.split('\n')
                definition = '\n'.join(lines[start_line:end_line])

            # 데코레이터 정보 추가
            decorators = [d.id if hasattr(d, 'id') else str(d) 
                         for d in node.decorator_list]

            yield {
                'file': file_path,
                'name': node.name,
                'line': node.lineno,
                'definition': definition,
                'decorators': decorators,
                'mode': 'ast',  # 수정됨: 'regex' -> 'ast'
                'type': 'function'
            }

def _find_class_ast(
    file_path: str,
    name: str,
    strict: bool = False  
) -> Generator[Dict[str, Any], None, None]:
    """
    AST를 사용한 클래스 검색
    상속 정보 포함
    """
    tree, source = _load_ast_cached(file_path)
    if tree is None:
        return

    pattern = re.compile(name if strict else f".*{name}.*", re.IGNORECASE)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and pattern.search(node.name):
            # Python 3.8+ - 정확한 소스 추출
            if sys.version_info >= (3, 8):
                definition = ast.get_source_segment(source, node)
            else:
                # Python 3.7 이하
                start_line = node.lineno - 1
                end_line = start_line + 100
                lines = source.split('\n')
                definition = '\n'.join(lines[start_line:end_line])

            # 상속 정보 추출
            bases = []
            for base in node.bases:
                if hasattr(base, 'id'):
                    bases.append(base.id)
                elif hasattr(base, 'attr'):
                    bases.append(f"{base.value.id if hasattr(base.value, 'id') else '?'}.{base.attr}")

            yield {
                'file': file_path,
                'name': node.name,
                'line': node.lineno,
                'definition': definition,
                'bases': bases,
                'mode': 'ast',  # 수정됨: 'regex' -> 'ast'
                'type': 'class'
            }
