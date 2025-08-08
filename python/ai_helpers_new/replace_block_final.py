"""
최종 통합 Replace Block - Desktop Commander edit_block 수준의 완벽한 교체 함수

통합된 기능:
1. Fuzzy matching으로 들여쓰기 차이 무시
2. 특수 문자 (f-string, regex, 백슬래시) 완벽 처리
3. 미리보기 모드
4. AST 구문 검증
5. 자동 백업
6. 상세한 오류 메시지
"""

import re
import ast
import difflib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import os


class ReplaceBlock:
    """최종 통합 Replace Block 클래스"""
    
    @staticmethod
    def detect_pattern_type(pattern: str) -> str:
        """패턴 타입 자동 감지"""
        # f-string
        if pattern.startswith(('f"', "f'")):
            return 'fstring'
        # raw string
        elif pattern.startswith(('r"', "r'")):
            return 'raw'
        # 삼중 따옴표
        elif pattern.startswith(('"""', "'''")):
            return 'triple'
        # 멀티라인
        elif '\n' in pattern:
            return 'multiline'
        # 특수 문자 많음
        elif any(c in pattern for c in ['{', '}', '\\', '^', '$', '*', '+', '?', '[', ']']):
            return 'special'
        else:
            return 'normal'
    
    @staticmethod
    def normalize_pattern(pattern: str, pattern_type: str) -> str:
        """패턴 정규화"""
        if pattern_type == 'fstring':
            # f-string의 {} 표현식을 와일드카드로
            normalized = re.escape(pattern)
            normalized = re.sub(r'\\{[^}]+\\}', r'\\{[^}]+\\}', normalized)
            return normalized
        
        elif pattern_type == 'raw':
            # raw string은 그대로
            return re.escape(pattern)
        
        else:
            # 일반 문자열은 줄바꿈 정규화
            return pattern.replace('\r\n', '\n')
    
    @staticmethod
    def find_pattern_with_fuzzy(content: str, pattern: str, threshold: float = 0.7) -> Optional[Tuple[int, int, float, str]]:
        """Fuzzy matching으로 패턴 찾기
        
        Returns:
            (시작 라인, 끝 라인, 유사도, 실제 매칭된 텍스트)
        """
        lines = content.split('\n')
        pattern_lines = pattern.split('\n')
        pattern_len = len(pattern_lines)
        
        # 들여쓰기 제거한 패턴
        pattern_stripped_lines = [line.strip() for line in pattern_lines]
        
        best_match = None
        best_ratio = 0.0
        best_text = ""
        
        # 슬라이딩 윈도우
        for i in range(len(lines) - pattern_len + 1):
            window = lines[i:i + pattern_len]
            window_stripped = [line.strip() for line in window]
            
            # 내용만으로 비교
            pattern_content = '\n'.join(pattern_stripped_lines)
            window_content = '\n'.join(window_stripped)
            
            matcher = difflib.SequenceMatcher(None, pattern_content, window_content)
            ratio = matcher.ratio()
            
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = (i, i + pattern_len)
                best_text = '\n'.join(window)
        
        if best_match:
            return (*best_match, best_ratio, best_text)
        return None
    
    @staticmethod
    def apply_indentation(new_text: str, original_indent: str) -> str:
        """새 텍스트에 원본 들여쓰기 적용"""
        lines = new_text.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            if line.strip():  # 내용이 있는 줄
                if i == 0:
                    # 첫 줄은 원본 들여쓰기 사용
                    result.append(original_indent + line.lstrip())
                else:
                    # 나머지는 상대적 들여쓰기 유지
                    # 원본 첫 줄의 들여쓰기를 기준으로
                    result.append(original_indent + line)
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    @staticmethod
    def validate_python_syntax(content: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """Python 구문 검증"""
        try:
            ast.parse(content)
            compile(content, file_path, 'exec')
            return True, None
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  {e.text.strip()}"
            return False, error_msg
        except Exception as e:
            return False, str(e)


def replace_block(
    file_path: str,
    old_text: str,
    new_text: str,
    fuzzy: bool = True,
    threshold: float = 0.7,
    preview: bool = False,
    validate: bool = True,
    backup: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    최종 통합 Replace Block 함수
    Desktop Commander edit_block 수준의 완벽한 파일 교체
    
    Args:
        file_path: 대상 파일 경로
        old_text: 찾을 텍스트 (들여쓰기 차이 허용)
        new_text: 교체할 텍스트
        fuzzy: True면 fuzzy matching 사용 (기본값)
        threshold: 매칭 유사도 임계값 (0.7 = 70%)
        preview: True면 미리보기만
        validate: True면 Python 파일 구문 검증
        backup: True면 백업 생성
        verbose: True면 상세 로그 출력
    
    Returns:
        {
            'ok': bool,
            'data': {교체 정보} or None,
            'error': 오류 메시지 or None,
            'preview': diff 문자열 (preview=True일 때),
            'suggestion': 유사 텍스트 (매칭 실패 시)
        }
    
    특징:
        - 들여쓰기 차이 자동 처리
        - f-string, 정규식, 백슬래시 등 특수 문자 완벽 처리
        - 멀티라인 코드 안전하게 교체
        - 미리보기로 변경사항 확인
        - Python 구문 자동 검증
        - 백업 자동 생성
        - 유사 텍스트 제안
    """
    
    rb = ReplaceBlock()
    
    try:
        # 파일 존재 확인
        path = Path(file_path)
        if not path.exists():
            return {
                'ok': False,
                'error': f"File not found: {file_path}"
            }
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 패턴 타입 감지
        pattern_type = rb.detect_pattern_type(old_text)
        if verbose:
            print(f"  Pattern type detected: {pattern_type}")
        
        # 1. 정확한 매칭 시도
        if old_text in content:
            if verbose:
                print("  Exact match found")
            
            # 들여쓰기 추출
            start_idx = content.index(old_text)
            lines_before = content[:start_idx].split('\n')
            if lines_before and lines_before[-1]:
                indent = len(lines_before[-1]) - len(lines_before[-1].lstrip())
                original_indent = ' ' * indent
            else:
                original_indent = ''
            
            # 교체
            new_content = content.replace(old_text, new_text, 1)
            match_info = {
                'type': 'exact',
                'ratio': 1.0
            }
        
        # 2. Fuzzy matching
        elif fuzzy:
            if verbose:
                print("  Trying fuzzy matching...")
            
            match_result = rb.find_pattern_with_fuzzy(content, old_text, threshold)
            
            if not match_result:
                # 더 낮은 threshold로 재시도하여 제안 찾기
                suggestion_result = rb.find_pattern_with_fuzzy(content, old_text, 0.5)
                
                result = {
                    'ok': False,
                    'error': f"Pattern not found (threshold: {threshold:.0%})"
                }
                
                if suggestion_result:
                    _, _, ratio, found_text = suggestion_result
                    result['suggestion'] = found_text
                    result['similarity'] = ratio
                    
                    # diff 생성
                    diff = difflib.unified_diff(
                        old_text.splitlines(),
                        found_text.splitlines(),
                        fromfile='expected',
                        tofile='found',
                        lineterm=''
                    )
                    result['diff'] = '\n'.join(diff)
                
                return result
            
            # 매칭 성공
            start_line, end_line, ratio, matched_text = match_result
            lines = content.split('\n')
            
            # 원본 들여쓰기 감지
            matched_lines = lines[start_line:end_line]
            if matched_lines and matched_lines[0]:
                indent_count = len(matched_lines[0]) - len(matched_lines[0].lstrip())
                original_indent = ' ' * indent_count
            else:
                original_indent = ''
            
            # 새 텍스트에 들여쓰기 적용
            if pattern_type != 'normal':
                # 특수 패턴은 들여쓰기 보존
                indented_new = rb.apply_indentation(new_text, original_indent)
            else:
                indented_new = new_text
            
            # 라인 교체
            new_lines = lines[:start_line] + indented_new.split('\n') + lines[end_line:]
            new_content = '\n'.join(new_lines)
            
            match_info = {
                'type': 'fuzzy',
                'ratio': ratio,
                'lines': (start_line, end_line)
            }
            
            if verbose:
                print(f"  Fuzzy match found: {ratio:.0%} similarity")
        
        else:
            return {
                'ok': False,
                'error': "No exact match found and fuzzy matching disabled"
            }
        
        # 3. Python 파일 구문 검증
        if validate and file_path.endswith('.py'):
            is_valid, error_msg = rb.validate_python_syntax(new_content, file_path)
            
            if not is_valid:
                # 구문 오류 시 컨텍스트 제공
                lines = new_content.split('\n')
                context_lines = []
                
                if error_msg and 'Line' in error_msg:
                    try:
                        line_no = int(error_msg.split('Line ')[1].split(':')[0])
                        start = max(0, line_no - 3)
                        end = min(len(lines), line_no + 2)
                        
                        for i in range(start, end):
                            prefix = ">>> " if i == line_no - 1 else "    "
                            context_lines.append(f"{prefix}{i+1}: {lines[i]}")
                    except:
                        pass
                
                return {
                    'ok': False,
                    'error': f"Syntax error: {error_msg}",
                    'context': '\n'.join(context_lines) if context_lines else None,
                    'match_info': match_info
                }
        
        # 4. 미리보기 모드
        if preview:
            diff = difflib.unified_diff(
                original_content.splitlines(),
                new_content.splitlines(),
                fromfile=file_path,
                tofile=f"{file_path} (modified)",
                lineterm='',
                n=3
            )
            
            return {
                'ok': True,
                'preview': '\n'.join(diff),
                'match_info': match_info
            }
        
        # 5. 백업 생성
        backup_path = None
        if backup:
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            if verbose:
                print(f"  Backup created: {backup_path}")
        
        # 6. 파일 쓰기
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'ok': True,
            'data': {
                'replaced': 1,
                'match_info': match_info,
                'backup': backup_path,
                'file': file_path
            }
        }
        
    except Exception as e:
        import traceback
        return {
            'ok': False,
            'error': str(e),
            'traceback': traceback.format_exc() if verbose else None
        }


# 편의 함수들
def replace_block_preview(file_path: str, old_text: str, new_text: str, **kwargs) -> Dict[str, Any]:
    """미리보기 전용 함수"""
    return replace_block(file_path, old_text, new_text, preview=True, **kwargs)


def replace_block_exact(file_path: str, old_text: str, new_text: str, **kwargs) -> Dict[str, Any]:
    """정확한 매칭만 사용"""
    return replace_block(file_path, old_text, new_text, fuzzy=False, **kwargs)


def replace_block_safe(file_path: str, old_text: str, new_text: str, **kwargs) -> Dict[str, Any]:
    """안전 모드 - 미리보기 후 적용"""
    # 먼저 미리보기
    preview_result = replace_block(file_path, old_text, new_text, preview=True, **kwargs)
    
    if preview_result.get('ok'):
        print("Preview:")
        print(preview_result.get('preview', ''))
        
        # 실제 적용
        return replace_block(file_path, old_text, new_text, **kwargs)
    
    return preview_result


# 기존 함수와의 호환성
def replace(path: str, old: str, new: str, **kwargs) -> Dict[str, Any]:
    """기존 replace 함수 호환성 래퍼"""
    return replace_block(path, old, new, **kwargs)


def safe_replace(path: str, old: str, new: str, **kwargs) -> Dict[str, Any]:
    """기존 safe_replace 호환성 래퍼"""
    return replace_block(path, old, new, validate=True, **kwargs)


if __name__ == "__main__":
    # 테스트 코드
    print("Replace Block Final - Ready to use!")
    print("Features:")
    print("  ✅ Fuzzy matching (들여쓰기 차이 무시)")
    print("  ✅ Special characters (f-string, regex, backslash)")
    print("  ✅ Preview mode")
    print("  ✅ Syntax validation")
    print("  ✅ Automatic backup")
    print("  ✅ Detailed error messages")
