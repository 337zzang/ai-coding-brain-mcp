"""
Safe Helpers - 헬퍼 함수의 반환값을 안전하게 처리하는 래퍼
"""

class SafeHelpers:
    """헬퍼 함수의 반환값을 안전하게 처리하는 래퍼 클래스"""

    def __init__(self, helpers):
        self.h = helpers

    def parse_file(self, filename):
        """parse_with_snippets의 안전한 래퍼

        Returns:
            dict: {
                'success': bool,
                'functions': list[dict],
                'classes': list[dict],
                'methods': list[dict],
                'all_snippets': list[dict]
            }
        """
        result = self.h.parse_with_snippets(filename)

        if not isinstance(result, dict) or not result.get('success', False):
            return {
                'success': False,
                'functions': [],
                'classes': [],
                'methods': [],
                'all_snippets': []
            }

        snippets = result.get('snippets', [])
        functions = []
        classes = []
        methods = []

        for s in snippets:
            info = {
                'name': getattr(s, 'name', 'unknown'),
                'type': getattr(s, 'type', 'unknown'),
                'start': getattr(s, 'start_line', 0),
                'end': getattr(s, 'end_line', 0),
                'code': getattr(s, 'content', ''),
                'lines': getattr(s, 'end_line', 0) - getattr(s, 'start_line', 0) + 1
            }

            if info['type'] == 'function':
                functions.append(info)
            elif info['type'] == 'class':
                classes.append(info)
            elif info['type'] == 'method':
                methods.append(info)

        return {
            'success': True,
            'functions': functions,
            'classes': classes,
            'methods': methods,
            'all_snippets': [self._snippet_to_dict(s) for s in snippets]
        }

    def _snippet_to_dict(self, snippet):
        """CodeSnippet을 dict로 변환"""
        return {
            'name': getattr(snippet, 'name', ''),
            'type': getattr(snippet, 'type', ''),
            'start': getattr(snippet, 'start_line', 0),
            'end': getattr(snippet, 'end_line', 0),
            'code': getattr(snippet, 'content', '')
        }

    def search_in_code(self, path, pattern, file_pattern="*"):
        """search_code의 안전한 래퍼

        Returns:
            list[dict]: 각 dict는 'file', 'line', 'text', 'context' 키를 가짐
        """
        results = self.h.search_code(path, pattern, file_pattern)

        if not isinstance(results, list):
            return []

        clean_results = []
        for r in results:
            if isinstance(r, dict):
                clean_results.append({
                    'file': r.get('file', ''),
                    'line': r.get('line_number', 0),
                    'text': r.get('line', ''),
                    'context': r.get('context', [])
                })

        return clean_results

    def get_git_status(self):
        """git_status의 안전한 래퍼

        Returns:
            dict: {
                'success': bool,
                'is_clean': bool,
                'modified': list[str],
                'untracked': list[str],
                'staged': list[str]
            }
        """
        status = self.h.git_status()

        if not isinstance(status, dict):
            return {
                'success': False,
                'is_clean': True,
                'modified': [],
                'untracked': [],
                'staged': []
            }

        return {
            'success': status.get('success', False),
            'is_clean': status.get('clean', True),
            'modified': status.get('modified', []),
            'untracked': status.get('untracked', []),
            'staged': status.get('staged', [])
        }

    def safe_replace(self, file, old_code, new_code):
        """replace_block의 안전한 래퍼

        Returns:
            dict: {
                'success': bool,
                'file': str,
                'backup': str,
                'changes': int,
                'error': str (optional)
            }
        """
        result = self.h.replace_block(file, old_code, new_code)

        if not isinstance(result, dict):
            return {'success': False, 'error': 'Invalid return type'}

        return {
            'success': result.get('success', False),
            'file': result.get('filepath', file),
            'backup': result.get('backup_path', ''),
            'changes': result.get('lines_changed', 0),
            'error': result.get('error', '')
        }

    def find_functions(self, path, name):
        """find_function의 안전한 래퍼"""
        results = self.h.find_function(path, name)

        if not isinstance(results, list):
            return []

        return [self._clean_search_result(r) for r in results if isinstance(r, dict)]

    def find_classes(self, path, name):
        """find_class의 안전한 래퍼"""
        results = self.h.find_class(path, name)

        if not isinstance(results, list):
            return []

        return [self._clean_search_result(r) for r in results if isinstance(r, dict)]

    def _clean_search_result(self, result):
        """검색 결과를 깨끗하게 정리"""
        return {
            'file': result.get('file', ''),
            'line': result.get('line_number', 0),
            'text': result.get('line', ''),
            'context': result.get('context', [])
        }

    def scan_directory(self, path):
        """scan_directory_dict의 안전한 래퍼"""
        result = self.h.scan_directory_dict(path)

        if not isinstance(result, dict):
            return {'files': [], 'dirs': [], 'error': 'Invalid return type'}

        structure = result.get('structure', {})
        files = []
        dirs = []

        for name, info in structure.items():
            if isinstance(info, dict):
                item = {
                    'name': name,
                    'type': info.get('type', 'unknown'),
                    'size': info.get('size', 0),
                    'modified': info.get('modified', 0)
                }

                if item['type'] == 'file':
                    files.append(item)
                elif item['type'] == 'directory':
                    dirs.append(item)

        return {
            'files': files,
            'dirs': dirs,
            'total_files': len(files),
            'total_dirs': len(dirs),
            'root': result.get('root', path)
        }

# 디버깅 도구
def inspect_return_value(value, name="value", max_depth=2, current_depth=0):
    """반환값의 구조를 상세히 출력하는 헬퍼 함수"""
    indent = "  " * current_depth
    print(f"{indent}{name}: {type(value).__name__}")

    if current_depth >= max_depth:
        return

    if isinstance(value, dict):
        for key in list(value.keys())[:5]:
            print(f"{indent}  .{key}: {type(value[key]).__name__}")
            if isinstance(value[key], (dict, list)) and current_depth < max_depth - 1:
                inspect_return_value(value[key], f"{key}", max_depth, current_depth + 1)

    elif isinstance(value, list) and len(value) > 0:
        print(f"{indent}  길이: {len(value)}")
        print(f"{indent}  첫 번째 요소:")
        inspect_return_value(value[0], "item[0]", max_depth, current_depth + 1)

    elif hasattr(value, '__dict__'):
        attrs = [a for a in dir(value) if not a.startswith('_')][:5]
        for attr in attrs:
            try:
                attr_value = getattr(value, attr)
                if not callable(attr_value):
                    print(f"{indent}  .{attr}: {type(attr_value).__name__}")
            except:
                pass
