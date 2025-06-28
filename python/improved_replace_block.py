def replace_block(file_path: str, block_name: str, new_content: str) -> dict:
    """
    AST 기반으로 코드 블록(함수/클래스)을 안전하게 교체
    EnhancedFunctionReplacer를 사용하여 들여쓰기 자동 처리
    """
    import ast
    import os
    import sys
    
    # 작업 추적 (있으면 사용)
    try:
        from work_tracking import WorkTracker
        WorkTracker().track_function_edit(file_path, block_name)
    except ImportError:
        pass
    
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # ast_parser_helpers import
        from ast_parser_helpers import EnhancedFunctionReplacer
        
        # AST 파싱
        try:
            tree = ast.parse(original_content)
        except SyntaxError as e:
            return {
                'success': False,
                'error': f'구문 오류: {str(e)}',
                'details': {
                    'line': e.lineno,
                    'offset': e.offset,
                    'text': e.text
                }
            }
        
        # EnhancedFunctionReplacer로 코드 교체
        replacer = EnhancedFunctionReplacer(block_name, new_content)
        new_tree = replacer.visit(tree)
        
        # AST를 다시 코드로 변환 (들여쓰기 자동 처리)
        try:
            new_content = ast.unparse(new_tree)
        except AttributeError:
            # Python 3.8 이하에서는 astor 사용
            try:
                import astor
                new_content = astor.to_source(new_tree)
            except ImportError:
                return {
                    'success': False,
                    'error': 'ast.unparse는 Python 3.9+ 필요, astor도 설치되지 않음'
                }
        
        # 파일 쓰기
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 성공 응답
        return {
            'success': True,
            'message': f'{block_name} 블록이 성공적으로 교체되었습니다',
            'details': {
                'file': file_path,
                'block': block_name,
                'original_size': len(original_content),
                'new_size': len(new_content),
                'ast_based': True
            }
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }