"""특수 문자 처리를 위한 개선 모듈"""

import re
import ast
from typing import Tuple, Optional
import difflib


def normalize_escape_sequences(text: str) -> str:
    """이스케이프 시퀀스 정규화"""
    escape_map = {
        '\\n': '\n',
        '\\t': '\t',
        '\\r': '\r',
        '\\"': '"',
        "\\'": "'",
        '\\\\': '\\'
    }
    
    result = text
    for escaped, actual in escape_map.items():
        result = result.replace(escaped, actual)
    
    return result


def handle_fstring_matching(pattern: str, source: str) -> bool:
    """f-string 패턴 매칭"""
    if not (pattern.startswith('f"') or pattern.startswith("f'")):
        return pattern in source
    
    # {} 내부를 정규식 패턴으로 변환
    regex_pattern = re.escape(pattern)
    
    # {} 내부를 와일드카드로
    regex_pattern = re.sub(r'\\{[^}]+\\}', r'\\{[^}]+\\}', regex_pattern)
    
    return bool(re.search(regex_pattern, source))


def smart_pattern_match(source: str, pattern: str, threshold: float = 0.8) -> Tuple[bool, float, Optional[str]]:
    """스마트 패턴 매칭"""
    # 1. 정확한 매칭
    if pattern in source:
        return True, 1.0, pattern
    
    # 2. 줄바꿈 정규화
    pattern_normalized = pattern.replace('\r\n', '\n')
    source_normalized = source.replace('\r\n', '\n')
    
    if pattern_normalized in source_normalized:
        return True, 0.95, pattern_normalized
    
    # 3. 공백 정규화
    pattern_stripped = ' '.join(pattern.split())
    source_lines = source.split('\n')
    
    for i, line in enumerate(source_lines):
        line_stripped = ' '.join(line.split())
        if pattern_stripped in line_stripped:
            return True, 0.9, line
    
    # 4. f-string 특별 처리
    if 'f"' in pattern or "f'" in pattern:
        if handle_fstring_matching(pattern, source):
            return True, 0.85, None
    
    # 5. 유사도 기반 매칭
    pattern_lines = pattern.split('\n')
    best_match = None
    best_ratio = 0.0
    
    for i in range(len(source_lines) - len(pattern_lines) + 1):
        window = source_lines[i:i + len(pattern_lines)]
        window_text = '\n'.join(window)
        
        matcher = difflib.SequenceMatcher(None, pattern, window_text)
        ratio = matcher.ratio()
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = window_text
    
    if best_ratio >= threshold:
        return True, best_ratio, best_match
    
    return False, best_ratio, best_match


def handle_special_chars_replace(file_path: str, old_text: str, new_text: str, fuzzy: bool = True) -> dict:
    """특수 문자를 고려한 안전한 교체"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        matched, similarity, found_text = smart_pattern_match(
            content, old_text, threshold=0.7 if fuzzy else 0.99
        )
        
        if not matched:
            result = {
                'ok': False,
                'error': f'Pattern not found (best similarity: {similarity:.1%})'
            }
            if found_text and fuzzy:
                result['suggestion'] = found_text
            return result
        
        # 교체 수행
        if found_text:
            new_content = content.replace(found_text, new_text, 1)
        else:
            new_content = content.replace(old_text, new_text, 1)
        
        if new_content == content:
            return {
                'ok': False,
                'error': 'Replacement did not change content'
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'ok': True,
            'similarity': similarity,
            'replaced': 1
        }
        
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


def detect_string_type(text: str) -> str:
    """문자열 타입 감지"""
    if text.startswith('"""') or text.startswith("'''"):
        return 'triple'
    elif text.startswith('f"') or text.startswith("f'"):
        return 'fstring'
    elif text.startswith('r"') or text.startswith("r'"):
        return 'raw'
    elif text.startswith('b"') or text.startswith("b'"):
        return 'bytes'
    elif text.startswith('"') or text.startswith("'"):
        return 'normal'
    else:
        return 'unknown'


def extract_string_content(text: str) -> str:
    """문자열 리터럴에서 내용만 추출"""
    string_type = detect_string_type(text)
    
    if string_type == 'triple':
        if text.startswith('"""'):
            return text[3:-3] if text.endswith('"""') else text[3:]
        else:
            return text[3:-3] if text.endswith("'''") else text[3:]
    
    elif string_type in ['fstring', 'raw', 'bytes']:
        text = text[1:]
    
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    elif text.startswith("'") and text.endswith("'"):
        return text[1:-1]
    
    return text
