
def replace_block_ast(file_path: str, block_name: str, new_content: str) -> dict:
    """
    완전한 AST 기반 코드 블록 교체 (들여쓰기 오류 방지)
    
    Args:
        file_path: 대상 파일 경로
        block_name: 교체할 블록 이름
        new_content: 새로운 코드 내용
        
    Returns:
        dict: 성공 여부와 상세 정보
    """
    import ast
    import astor
    import textwrap
    
    try:
        # 1. 원본 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 2. AST로 파싱
        tree = ast.parse(original_content)
        
        # 3. EnhancedFunctionReplacer 사용하여 교체
        from ast_parser_helpers import EnhancedFunctionReplacer
        
        # 새 코드의 상대 들여쓰기 보존
        # 최소 공통 들여쓰기만 제거
        lines = new_content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            min_indent = min(len(line) - len(line.lstrip()) 
                           for line in non_empty_lines)
            # 최소 들여쓰기만큼 왼쪽으로 이동
            processed_lines = []
            for line in lines:
                if line.strip():
                    processed_lines.append(line[min_indent:])
                else:
                    processed_lines.append(line)
            new_content_normalized = '\n'.join(processed_lines)
        else:
            new_content_normalized = new_content
        
        # 4. AST 변환
        replacer = EnhancedFunctionReplacer(block_name, new_content_normalized)
        new_tree = replacer.visit(tree)
        
        if not replacer.found_and_replaced:
            return {
                'success': False,
                'error': f"Block '{block_name}' not found in {file_path}"
            }
        
        # 5. AST를 코드로 변환 (자동 들여쓰기)
        new_code = astor.to_source(new_tree)
        
        # 6. 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        return {
            'success': True,
            'message': f"Successfully replaced '{block_name}' using AST",
            'file': file_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def insert_block_ast(file_path: str, target_name: str, position: str, new_code: str) -> dict:
    """
    AST 기반 코드 삽입 (docstring 및 들여쓰기 스타일 고려)
    
    Args:
        file_path: 대상 파일 경로
        target_name: 삽입 기준 블록 이름
        position: 'before', 'after', 'start', 'end'
        new_code: 삽입할 코드
        
    Returns:
        dict: 성공 여부와 상세 정보
    """
    import ast
    import astor
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 들여쓰기 스타일 감지
        from core.indentation_preprocessor import IndentationPreprocessor
        preprocessor = IndentationPreprocessor()
        indent_size = preprocessor.detect_indent_style(content)
        
        # AST 파싱
        tree = ast.parse(content)
        
        # BlockInsertTransformer 사용
        from ast_parser_helpers import BlockInsertTransformer
        
        # docstring 처리를 위한 개선된 Transformer
        class EnhancedBlockInsertTransformer(BlockInsertTransformer):
            def __init__(self, target_name, position, new_code, indent_size=4):
                super().__init__(target_name, position, new_code)
                self.indent_size = indent_size
                
            def _insert_at_start(self, node):
                """함수/클래스 시작 부분에 삽입 (docstring 고려)"""
                # docstring 확인
                has_docstring = False
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, (ast.Str, ast.Constant)):
                        has_docstring = True
                
                # 새 코드를 AST로 파싱
                new_nodes = ast.parse(self.new_code).body
                
                # docstring 다음에 삽입
                if has_docstring:
                    node.body = [node.body[0]] + new_nodes + node.body[1:]
                else:
                    node.body = new_nodes + node.body
                
                return node
        
        # 변환 적용
        transformer = EnhancedBlockInsertTransformer(
            target_name, position, new_code, indent_size
        )
        new_tree = transformer.visit(tree)
        
        if not transformer.found_and_inserted:
            return {
                'success': False,
                'error': f"Target '{target_name}' not found"
            }
        
        # 코드 생성
        new_content = astor.to_source(new_tree)
        
        # 들여쓰기 스타일 조정 (4칸이 아닌 경우)
        if indent_size != 4:
            lines = new_content.split('\n')
            adjusted_lines = []
            for line in lines:
                if line and line[0] == ' ':
                    # 4칸 들여쓰기를 프로젝트 스타일로 변환
                    indent_level = (len(line) - len(line.lstrip())) // 4
                    new_indent = ' ' * (indent_level * indent_size)
                    adjusted_lines.append(new_indent + line.lstrip())
                else:
                    adjusted_lines.append(line)
            new_content = '\n'.join(adjusted_lines)
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'success': True,
            'message': f"Successfully inserted code at {position} of '{target_name}'",
            'file': file_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
