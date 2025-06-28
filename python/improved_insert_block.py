def insert_block(file_path: str, target_name: str, position: str, new_code: str) -> dict:
    """
    AST 기반으로 코드 블록을 안전하게 삽입
    BlockInsertTransformer를 사용하여 들여쓰기 자동 처리

    Args:
        file_path: 대상 파일 경로
        target_name: 삽입 위치 기준이 되는 블록 이름
        position: 'before', 'after', 'start', 'end' 중 하나
        new_code: 삽입할 새로운 코드

    Returns:
        dict: 성공 여부와 상세 정보
    """
    import ast
    import os
    import sys
    
    # 작업 추적 (있으면 사용)
    try:
        from work_tracking import WorkTracker
        WorkTracker().track_function_edit(file_path, f"{target_name}:{position}")
    except ImportError:
        pass
    
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # ast_parser_helpers import
        from ast_parser_helpers import BlockInsertTransformer
        
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
        
        # BlockInsertTransformer로 코드 삽입
        inserter = BlockInsertTransformer(target_name, position, new_code)
        new_tree = inserter.visit(tree)
        
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
            'message': f'{target_name}의 {position} 위치에 코드가 삽입되었습니다',
            'details': {
                'file': file_path,
                'target': target_name,
                'position': position,
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