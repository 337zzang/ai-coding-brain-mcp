#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
들여쓰기 관리 유틸리티 - 최종 통합 버전
Python 표준 4칸 단위를 완벽하게 준수하는 솔루션
"""

from typing import Tuple, Optional, Union

class IndentationManager:
    """들여쓰기 관리자 - Python 표준 4칸 단위 강제"""

    def __init__(self, indent_size: int = 4, tabsize: int = 8):
        """
        IndentationManager 초기화

        Args:
            indent_size: 기본 들여쓰기 크기 (기본값: 4)
            tabsize: 탭 크기 (기본값: 8)
        """
        self.indent_size = indent_size
        self.tabsize = tabsize
    def detect_indentation(self, code: str) -> int:
        """코드의 들여쓰기 크기 감지 - 기본 4칸"""
        return 4

    def get_line_indent(self, line: str) -> int:
        """
        라인의 들여쓰기 레벨을 반환 (개선됨: expandtabs 처리)

        O3 제안: 탭을 expandtabs로 정규화 후 계산
        """
        line = self._expand_tabs(line)
        return len(line) - len(line.lstrip(' '))
    
    def reindent_block(self, code: str, target_indent: int) -> str:
        """
        O3 제안: 오프셋 보존 방식으로 블록 재들여쓰기
        
        핵심 원리:
        - 상대적 구조를 완벽하게 보존
        - 압축 매핑 대신 평행 이동 사용
        - 8칸→4칸 같은 축소 없음
        
        Args:
            code: 재들여쓰기할 코드 블록
            target_indent: 목표 들여쓰기 레벨
            
        Returns:
            재들여쓰기된 코드
        """
        lines = code.split('\n')
        if not lines:
            return code
        
        # 1. 비어있지 않은 라인들의 들여쓰기 수집
        non_empty_lines = [(i, line) for i, line in enumerate(lines) if line.strip()]
        if not non_empty_lines:
            return code
        
        # 2. 최소 들여쓰기 찾기 (기준점)
        min_indent = min(self.get_line_indent(line) for _, line in non_empty_lines)
        
        # 3. 오프셋 보존하며 재들여쓰기
        result_lines = []
        for line in lines:
            if not line.strip():
                result_lines.append('')  # 빈 줄 유지
            else:
                # 현재 줄의 들여쓰기
                current_indent = self.get_line_indent(line)
                
                # 최소 들여쓰기 기준 상대 오프셋
                relative_offset = current_indent - min_indent
                
                # 목표 들여쓰기 + 상대 오프셋 (구조 보존!)
                new_indent = target_indent + relative_offset
                
                # 음수 방지
                new_indent = max(0, new_indent)
                
                # 재들여쓰기 적용
                result_lines.append(' ' * new_indent + line.lstrip())
        
        return '\n'.join(result_lines)
    def normalize_indent(self, code: str, target_indent: int = 0) -> str:
        """코드의 들여쓰기를 Python 표준 4칸으로 정규화

        핵심 기능:
        - 8칸 차이를 4칸 차이로 자동 변환
        - Python PEP 8 표준 준수
        - 논리적 블록 구조 유지
        """
        lines = code.split('\n')
        if not lines:
            return code

        # 1. 비어있지 않은 라인들의 들여쓰기 수집
        indent_levels = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indent_levels.append(indent)

        if not indent_levels:
            return code

        # 2. 최소 들여쓰기 찾기
        min_indent = min(indent_levels)

        # 3. 각 라인 처리 - 8칸을 4칸으로 변환
        normalized_lines = []
        for line in lines:
            if line.strip():
                current_indent = len(line) - len(line.lstrip())
                # 상대적 깊이 계산
                relative_depth = current_indent - min_indent

                # 핵심: 8칸 단위를 4칸 단위로 변환
                if relative_depth > 0:
                    # 8칸 차이를 1레벨로 간주하고, 4칸으로 재구성
                    depth_level = relative_depth // 8 if relative_depth >= 8 else 0
                    # 남은 4칸 차이 처리
                    if relative_depth % 8 >= 4:
                        depth_level += 1
                else:
                    depth_level = 0

                # 최종 들여쓰기 (Python 표준 4칸 단위)
                final_indent = target_indent + (depth_level * self.indent_size)
                normalized_lines.append(' ' * final_indent + line.lstrip())
            else:
                normalized_lines.append('')

        return '\n'.join(normalized_lines)

    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Python 구문 검증"""
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def smart_replace(self, 
                     original_code: str, 
                     old_block: str, 
                     new_block: str) -> Tuple[str, bool]:
        """
        O3 제안: 앵커 기반 스마트 코드 교체
        
        다층 매칭 파이프라인:
        1차: 앵커 라인 매칭 (첫 비공백 라인)
        2차: 경계 제약 퍼지 매칭 (윈도우 내)
        3차: 최적 후보 선택 및 구조 보존 교체
        """
        lines = original_code.split('\n')
        old_lines = old_block.strip().split('\n')
        
        # 1. 앵커 라인 찾기 (첫 번째 의미있는 라인)
        anchor_line = None
        anchor_idx = 0
        for idx, line in enumerate(old_lines):
            if line.strip() and not line.strip().startswith('#'):
                anchor_line = line.strip()
                anchor_idx = idx
                break
        
        if not anchor_line:
            return original_code, False
        
        # 2. 앵커 기반 매칭 시작
        candidates = []
        for i, line in enumerate(lines):
            if anchor_line in line.strip() or self._fuzzy_match_line(line.strip(), anchor_line):
                # 앵커 발견 - 전체 블록 검증
                window_start = i - anchor_idx  # 앵커 위치 조정
                window_start = max(0, window_start)
                window_end = window_start + len(old_lines)
                
                if window_end > len(lines):
                    continue
                
                # 윈도우 내 매칭 점수 계산
                match_score = self._calculate_match_score(
                    lines[window_start:window_end],
                    old_lines
                )
                
                if match_score > 0.7:  # 70% 이상 일치
                    candidates.append({
                        'start': window_start,
                        'end': window_end,
                        'score': match_score,
                        'indent': self.get_line_indent(lines[window_start])
                    })
        
        # 3. 최적 후보 선택
        if not candidates:
            # 앵커 매칭 실패 - 기존 방식 폴백
            return original_code, False
        
        best = max(candidates, key=lambda x: x['score'])
        
        # 4. reindent_block으로 새 코드 들여쓰기 조정 (O3 제안 메서드 사용!)
        adjusted_new = self.reindent_block(new_block, best['indent'])
        
        # 5. 교체 수행
        new_lines = (
            lines[:best['start']] + 
            adjusted_new.split('\n') + 
            lines[best['end']:]
        )
        result_code = '\n'.join(new_lines)
        
        # 6. 구문 검증
        is_valid, error_msg = self.validate_syntax(result_code)
        if not is_valid:
            return original_code, False
        
        return result_code, True
    
    def _calculate_match_score(self, window_lines, target_lines):
        """매칭 점수 계산 (0~1)"""
        if len(window_lines) != len(target_lines):
            return 0
        
        matches = 0
        for w_line, t_line in zip(window_lines, target_lines):
            # 들여쓰기 무시하고 내용만 비교
            if w_line.strip() == t_line.strip():
                matches += 1
        
        return matches / len(target_lines) if target_lines else 0
    
    def _fuzzy_match_line(self, line1: str, line2: str, threshold: float = 0.8) -> bool:
        """단일 라인 퍼지 매칭"""
        import difflib
        ratio = difflib.SequenceMatcher(None, line1, line2).ratio()
        return ratio >= threshold
    def reindent_block(self, code: str, target_indent: int) -> str:
        """
        O3 제안: 오프셋 보존 전략으로 들여쓰기 재조정

        상대 구조를 보존하면서 target_indent로 평행 이동합니다.
        기존 normalize_indent의 "압축 매핑" 문제를 해결합니다.

        Args:
            code: 재들여쓰기할 코드 블록
            target_indent: 목표 들여쓰기 레벨 (공백 수)

        Returns:
            재들여쓰기된 코드 문자열
        """
        lines = code.splitlines()
        if not lines:
            return code

        # 탭 정규화 + 최소 들여쓰기(min_new) 계산
        expanded = [self._expand_tabs(l) for l in lines]
        non_empty = [l for l in expanded if l.strip()]

        if not non_empty:
            return code

        # 최소 들여쓰기 계산 (상대 구조 보존의 기준점)
        min_new = min((self.get_line_indent(l) for l in non_empty), default=0)

        out = []
        for l in expanded:
            if l.strip():
                cur = self.get_line_indent(l)
                offset = max(cur - min_new, 0)  # 상대 구조 보존
                new_line = ' ' * (target_indent + offset) + l.lstrip()
                out.append(new_line)
            else:
                out.append('')  # 빈 줄은 빈 줄로 유지

        return '\n'.join(out)

    def smart_insert(self, 
                     original_code: str,
                     insert_content: str,
                     position: Union[int, str],
                     after: bool = True) -> Tuple[str, bool]:
        """
        O3 제안: 앵커 기반 스마트 삽입 알고리즘 (버그 수정 버전)
        
        핵심 개선사항:
        1. 앵커 라인 퍼지 매칭 (80%+ 유사도)
        2. 오프셋 보존 방식으로 들여쓰기 적용 (이중 적용 버그 수정!)
        3. 블록 구조 인식 삽입
        4. 빈 내용 검증 추가
        
        Args:
            original_code: 원본 코드
            insert_content: 삽입할 내용
            position: 위치 (줄 번호 또는 마커 텍스트)
            after: True면 position 뒤에, False면 앞에 삽입
            
        Returns:
            (수정된 코드, 성공 여부)
        """
        # 0. 빈 내용 검증 (O3 권장)
        if not self._has_effective_code(insert_content):
            return original_code, False
        
        lines = original_code.split('\n')
        
        # 1. 삽입 위치 결정
        insert_idx = None
        target_indent = 0
        need_extra_indent = False  # 블록 내부 삽입 여부
        
        if isinstance(position, int):
            # 줄 번호로 지정
            insert_idx = position - 1 if not after else position
            insert_idx = max(0, min(insert_idx, len(lines)))
            
            # 주변 라인에서 들여쓰기 추론
            if 0 < insert_idx < len(lines):
                ref_line = lines[insert_idx - 1] if not after else lines[min(insert_idx, len(lines)-1)]
                target_indent = self.get_line_indent(ref_line)
                
        elif isinstance(position, str):
            # 텍스트 마커로 찾기 (앵커 기반)
            best_match = None
            best_score = 0
            
            for i, line in enumerate(lines):
                # 정확한 매칭 우선
                if position in line:
                    best_match = i
                    best_score = 1.0
                    break
                    
                # 퍼지 매칭 (80% 이상)
                if self._fuzzy_match_line(line.strip(), position.strip(), 0.8):
                    score = self._calculate_similarity(line.strip(), position.strip())
                    if score > best_score:
                        best_match = i
                        best_score = score
            
            if best_match is not None:
                insert_idx = best_match if not after else best_match + 1
                # 매칭된 라인의 들여쓰기 가져오기
                target_indent = self.get_line_indent(lines[best_match])
            else:
                # 매칭 실패
                return original_code, False
        
        if insert_idx is None:
            return original_code, False
        
        # 2. 컨텍스트 기반 들여쓰기 결정 (O3 개선)
        # 단순히 이전 라인만 보지 않고 전체 컨텍스트 분석
        context_indent = self.determine_context_indent(lines, insert_idx)
        
        # 블록 시작 직후인지 체크
        if insert_idx > 0:
            prev_line = lines[insert_idx - 1].strip()
            if any(prev_line.startswith(kw) for kw in ['def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try:']):
                if prev_line.endswith(':'):
                    # 블록 시작 직후 - 한 단계 더 들여쓰기
                    need_extra_indent = True
                    # 하지만 context_indent가 이미 적절한 레벨이면 그대로 사용
                    if context_indent > target_indent:
                        final_indent = context_indent
                    else:
                        final_indent = target_indent + self.indent_size
                else:
                    final_indent = context_indent
            else:
                # 일반적인 경우 - 컨텍스트 들여쓰기 사용
                final_indent = context_indent
        else:
            final_indent = target_indent
        
        # 4. 스마트 들여쓰기 적용 (단일 적용!)
        adjusted_content = self.reindent_block(insert_content, final_indent)
        adjusted_lines = adjusted_content.split('\n')
        
        # 5. 코드 재구성
        new_lines = lines[:insert_idx] + adjusted_lines + lines[insert_idx:]
        result_code = '\n'.join(new_lines)
        
        # 6. 구문 검증
        is_valid, error_msg = self.validate_syntax(result_code)
        if not is_valid:
            # 구문 오류 시 원본 반환
            return original_code, False
        
        return result_code, True
    
    def _has_effective_code(self, code: str) -> bool:
        """코드가 실제 의미있는 내용을 포함하는지 검증 (O3 권장)"""
        if not code or not code.strip():
            return False
        
        # 주석만 있는지 체크
        lines = code.split('\n')
        non_comment_lines = [
            ln for ln in lines 
            if ln.strip() and not ln.lstrip().startswith('#')
        ]
        
        if not non_comment_lines:
            return False
        
        # 구문 검증 (O3 권장 방식)
        try:
            # 함수 내부에 래핑하여 검증
            wrapped = "def __temp__():\n" + "\n".join("    " + ln for ln in lines)
            import ast
            ast.parse(wrapped)
            return True
        except SyntaxError:
            # 전역 레벨 코드일 수 있으므로 다시 시도
            try:
                compile(code, '<string>', 'exec')
                return True
            except:
                return False
    
    def get_anchor_indent_from_ast(self, source: str, target_name: str) -> Optional[int]:
        """AST를 사용하여 정확한 앵커 위치의 들여쓰기 찾기 (O3 권장)"""
        try:
            import ast
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                # 함수 찾기
                if isinstance(node, ast.FunctionDef) and node.name == target_name:
                    lines = source.split('\n')
                    if node.lineno <= len(lines):
                        line = lines[node.lineno - 1]
                        return len(line) - len(line.lstrip())
                
                # 클래스 찾기
                elif isinstance(node, ast.ClassDef) and node.name == target_name:
                    lines = source.split('\n')
                    if node.lineno <= len(lines):
                        line = lines[node.lineno - 1]
                        return len(line) - len(line.lstrip())
            
            return None
        except:
            return None
    
    def determine_context_indent(self, lines: list, insert_idx: int) -> int:
        """삽입 위치의 컨텍스트를 분석하여 적절한 들여쓰기 결정 (O3 개선)"""
        if insert_idx <= 0 or insert_idx > len(lines):
            return 0
        
        # 현재 라인과 이전 라인들 분석
        for i in range(insert_idx - 1, -1, -1):
            line = lines[i]
            stripped = line.strip()
            indent = self.get_line_indent(line)
            
            # 클래스 정의 찾기
            if stripped.startswith('class '):
                # 클래스 내부 메서드는 4칸
                return 4
            
            # 함수 정의 찾기 (클래스 메서드)
            if stripped.startswith('def ') and indent == 4:
                # 같은 레벨의 다른 메서드
                return 4
            
            # 함수 정의 찾기 (전역 함수)
            if stripped.startswith('def ') and indent == 0:
                # 같은 레벨의 다른 함수
                return 0
        
        # 기본값: 현재 위치의 들여쓰기
        if insert_idx < len(lines):
            return self.get_line_indent(lines[insert_idx])
        return 0
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """두 문자열의 유사도 계산 (0~1)"""
        import difflib
        return difflib.SequenceMatcher(None, str1, str2).ratio()
    
    def _expand_tabs(self, line: str) -> str:
        """탭을 공백으로 확장 (일관된 들여쓰기 계산을 위해)"""
        return line.expandtabs(getattr(self, 'tabsize', 8))