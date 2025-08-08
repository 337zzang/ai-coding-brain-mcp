"""통합된 스마트 교체 함수"""

def smart_replace_ultimate(file_path: str, old_text: str, new_text: str, **kwargs) -> dict:
    """특수 문자를 자동 감지하여 최적의 방법으로 교체

    자동으로 선택:
    - 특수 문자가 많으면 → special_char_handler
    - 멀티라인이면 → fuzzy matching  
    - 일반 텍스트면 → 기본 replace
    """
    # 특수 문자 감지
    special_chars = ['{', '}', r'\', '^', '$', '*', '+', '?', '[', ']', '(', ')']
    has_special = any(c in old_text for c in special_chars)

    # f-string 감지
    is_fstring = old_text.startswith(('f"', "f'"))

    # 정규식 패턴 감지
    is_regex = old_text.startswith(('r"', "r'")) or '\\' in old_text

    # 멀티라인 감지
    is_multiline = '\n' in old_text

    if is_fstring or is_regex or (has_special and not is_multiline):
        # 특수 문자 처리기 사용
        from special_char_handler import handle_special_chars_replace
        return handle_special_chars_replace(file_path, old_text, new_text, **kwargs)

    elif is_multiline:
        # Fuzzy matching 사용
        from improved_replace import replace_improved
        return replace_improved(file_path, old_text, new_text, fuzzy=True, **kwargs)

    else:
        # 기본 교체
        from improved_replace import replace_improved
        return replace_improved(file_path, old_text, new_text, fuzzy=False, **kwargs)
