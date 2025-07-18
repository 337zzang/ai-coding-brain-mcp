"""
안전한 코드 수정 도구 - 자동 문법 검증 및 롤백 지원
"""
import ast
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import os


class SafeCodeModifier:
    """문법 검증을 지원하는 안전한 코드 수정 클래스"""

    def __init__(self, auto_backup: bool = True, validate_syntax: bool = True):
        self.auto_backup = auto_backup
        self.validate_syntax = validate_syntax
        self.backup_history = []

    def safe_replace(self, filepath: str, target_name: str, new_code: str) -> Dict[str, Any]:
        """안전한 코드 교체 - 문법 검증 및 자동 롤백"""
        result = {
            'success': False,
            'filepath': filepath,
            'target': target_name,
            'backup_path': None,
            'error': None,
            'rollback': False
        }

        # 1. 백업 생성
        if self.auto_backup:
            backup_path = self._create_backup(filepath)
            result['backup_path'] = backup_path
            self.backup_history.append((filepath, backup_path))

        try:
            # 2. 원본 파일 문법 검증
            if self.validate_syntax:
                original_valid, original_error = self._validate_file_syntax(filepath)
                if not original_valid:
                    result['error'] = f"원본 파일 구문 오류: {original_error}"
                    return result

            # 3. 새 코드 문법 검증 (독립적으로)
            if self.validate_syntax:
                new_code_valid, new_code_error = self._validate_code_syntax(new_code)
                if not new_code_valid:
                    result['error'] = f"새 코드 구문 오류: {new_code_error}"
                    return result

            # 4. ez_parse 사용하여 대상 찾기
            try:
                from .ez_code import ez_parse
            except ImportError:
                # 직접 경로에서 임포트
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                sys.path.insert(0, current_dir)
                from ez_code import ez_parse
                
            items = ez_parse(filepath)

            if target_name not in items:
                result['error'] = f"대상 '{target_name}'을 찾을 수 없습니다"
                return result

            # 5. 코드 교체 수행
            start, end = items[target_name]

            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 들여쓰기 처리
            indent = len(lines[start]) - len(lines[start].lstrip())
            new_lines = self._apply_indent(new_code, indent)

            # 교체
            lines[start:end+1] = new_lines

            # 임시 파일에 쓰기
            temp_path = filepath + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            # 6. 수정된 파일 문법 검증
            if self.validate_syntax:
                modified_valid, modified_error = self._validate_file_syntax(temp_path)
                if not modified_valid:
                    os.remove(temp_path)
                    result['error'] = f"수정 후 구문 오류: {modified_error}"
                    result['rollback'] = True

                    # 자동 롤백
                    if self.auto_backup and backup_path:
                        shutil.copy2(backup_path, filepath)
                        result['error'] += " (자동 롤백됨)"

                    return result

            # 7. 성공 - 원본 파일 교체
            os.replace(temp_path, filepath)

            result['success'] = True
            result['lines_changed'] = end - start + 1
            result['new_lines'] = len(new_lines)

            return result

        except Exception as e:
            result['error'] = str(e)

            # 예외 발생 시 롤백
            if self.auto_backup and result['backup_path']:
                shutil.copy2(result['backup_path'], filepath)
                result['rollback'] = True
                result['error'] += " (자동 롤백됨)"

            return result

    def _create_backup(self, filepath: str) -> str:
        """백업 파일 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        return backup_path

    def _validate_file_syntax(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """파일의 Python 구문 검증"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            compile(content, filepath, 'exec')
            return True, None

        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def _validate_code_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """코드 조각의 Python 구문 검증"""
        try:
            # 들여쓰기를 제거하여 독립적으로 검증
            lines = code.strip().split('\n')
            if lines:
                # 첫 줄의 들여쓰기 계산
                first_line = lines[0]
                base_indent = len(first_line) - len(first_line.lstrip())

                # 모든 줄에서 기본 들여쓰기 제거
                normalized_lines = []
                for line in lines:
                    if line.strip():  # 빈 줄이 아닌 경우
                        if len(line) >= base_indent:
                            normalized_lines.append(line[base_indent:])
                        else:
                            normalized_lines.append(line)
                    else:
                        normalized_lines.append(line)

                normalized_code = '\n'.join(normalized_lines)
                compile(normalized_code, '<string>', 'exec')

            return True, None

        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def _apply_indent(self, code: str, indent: int) -> list:
        """코드에 들여쓰기 적용"""
        lines = []
        code_lines = code.strip().split('\n')

        for i, line in enumerate(code_lines):
            if i == 0:
                # 첫 줄은 원본 들여쓰기 사용
                lines.append(' ' * indent + line.lstrip() + '\n')
            else:
                # 나머지는 상대적 들여쓰기 유지
                if line.strip():  # 빈 줄이 아닌 경우
                    lines.append(' ' * indent + line + '\n')
                else:
                    lines.append(line + '\n')

        return lines

    def get_backup_history(self) -> list:
        """백업 이력 반환"""
        return self.backup_history.copy()

    def clear_old_backups(self, filepath: str, keep_latest: int = 5):
        """오래된 백업 파일 정리"""
        import glob

        backup_pattern = f"{filepath}.backup_*"
        backups = sorted(glob.glob(backup_pattern), reverse=True)

        # 최신 N개만 유지
        for old_backup in backups[keep_latest:]:
            try:
                os.remove(old_backup)
                print(f"🗑️ 오래된 백업 삭제: {old_backup}")
            except:
                pass


# 통합 함수 - ez_code와 연동
def ez_replace_safe(filepath: str, target_name: str, new_code: str, 
                   backup: bool = True, validate: bool = True) -> str:
    """ez_replace의 안전한 버전"""
    modifier = SafeCodeModifier(auto_backup=backup, validate_syntax=validate)
    result = modifier.safe_replace(filepath, target_name, new_code)

    if result['success']:
        msg = f"✅ Replaced {target_name} ({result['lines_changed']} → {result['new_lines']} lines)"
        if result['backup_path']:
            msg += f"\n   Backup: {result['backup_path']}"
        return msg
    else:
        return f"❌ 교체 실패: {result['error']}"
