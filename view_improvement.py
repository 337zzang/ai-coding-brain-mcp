
def view(path: str, name: str) -> Dict[str, Any]:
    """
    개선된 view 함수 - 더 안전하고 명확한 인터페이스

    기존 code.view를 래핑하여 더 나은 사용성 제공

    Args:
        path: 파일 경로
        name: 함수 또는 클래스 이름

    Returns:
        성공 시:
        {
            'ok': True,
            'data': str,  # 기존 호환성을 위해 유지
            'code': str,  # 더 명확한 이름 (data와 동일)
            'lines': List[str],  # 라인별 리스트
            'line_start': int,
            'line_end': int,
            'line_count': int,  # 총 라인 수
            'type': str  # 'function' or 'class'
        }

        실패 시:
        {
            'ok': False,
            'error': str
        }
    """
    from . import code as code_module

    try:
        # 원본 view 함수 호출
        result = code_module.view(path, name)

        if not isinstance(result, dict):
            return {
                'ok': False,
                'error': f'Unexpected return type from view: {type(result)}'
            }

        if result.get('ok'):
            code_content = result.get('data', '')
            lines = code_content.splitlines() if code_content else []

            # 개선된 반환값 구조
            enhanced_result = {
                'ok': True,
                'data': code_content,  # 기존 호환성
                'code': code_content,  # 더 명확한 이름
                'lines': lines,  # 라인별 리스트
                'line_start': result.get('line_start'),
                'line_end': result.get('line_end'),
                'line_count': len(lines),
                'type': result.get('type', 'unknown')
            }

            # 추가 유용한 정보
            if lines:
                enhanced_result['first_line'] = lines[0] if lines else ''
                enhanced_result['signature'] = lines[0].strip() if lines else ''

            return enhanced_result
        else:
            return result  # 오류는 그대로 반환

    except Exception as e:
        return {
            'ok': False,
            'error': f'View wrapper error: {type(e).__name__}: {str(e)}'
        }


def view_code(path: str, name: str) -> Optional[str]:
    """
    간단한 헬퍼 - 코드만 반환 (오류 시 None)

    Example:
        code = h.view_code("main.py", "process_data")
        if code:
            print(code)
    """
    result = view(path, name)
    return result.get('code') if result.get('ok') else None
