#!/usr/bin/env python3
"""
AI Helpers 안전 사용을 위한 래퍼 모듈
즉시 사용 가능한 안전한 버전의 헬퍼 함수들
"""
from typing import Any, Dict, List, Optional, Callable, Union
import time
import functools

class SafeHelpers:
    """AI Helpers의 안전한 사용을 위한 유틸리티 클래스"""

    @staticmethod
    def safe_execute(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """함수를 안전하게 실행하고 표준 응답 반환"""
        try:
            result = func(*args, **kwargs)
            # 이미 ok/error 형식인 경우
            if isinstance(result, dict) and 'ok' in result:
                return result
            # 그 외의 경우 ok=True로 래핑
            return {'ok': True, 'data': result}
        except Exception as e:
            return {
                'ok': False, 
                'error': str(e),
                'error_type': type(e).__name__,
                'args': args,
                'kwargs': kwargs
            }

    @staticmethod
    def parse_safe(file_path: str) -> Dict[str, Any]:
        """h.parse()의 안전한 버전"""
        import ai_helpers_new as h

        # 1. 입력 검증
        if not file_path or not isinstance(file_path, str):
            return {'ok': False, 'error': 'Invalid file path', 'path': file_path}

        # 2. 파일 존재 확인
        exists_result = SafeHelpers.safe_execute(h.exists, file_path)
        if not exists_result.get('ok') or not exists_result.get('data'):
            return {
                'ok': False, 
                'error': f'File not found: {file_path}',
                'path': file_path
            }

        # 3. Parse 실행
        parse_result = SafeHelpers.safe_execute(h.parse, file_path)
        if not parse_result.get('ok'):
            return parse_result

        # 4. 결과 정규화
        data = parse_result.get('data', {})
        functions = data.get('functions', [])

        # 각 함수 정보 안전하게 정규화
        safe_functions = []
        for func in functions:
            if isinstance(func, dict):
                safe_functions.append({
                    'name': func.get('name', 'unknown'),
                    'line': func.get('line', 0),
                    'args': func.get('args', []),
                    'docstring': func.get('docstring', ''),
                    'is_async': func.get('is_async', False),
                    'decorators': func.get('decorators', [])
                })

        return {
            'ok': True,
            'path': file_path,
            'functions': safe_functions,
            'classes': data.get('classes', []),
            'imports': data.get('imports', []),
            'function_count': len(safe_functions)
        }

    @staticmethod
    def find_functions_by_pattern(file_path: str, pattern: str) -> List[Dict[str, Any]]:
        """패턴에 맞는 함수를 안전하게 검색"""
        result = SafeHelpers.parse_safe(file_path)
        if not result.get('ok'):
            return []

        pattern_lower = pattern.lower()
        matching = []

        for func in result.get('functions', []):
            func_name = func.get('name', '')
            if pattern_lower in func_name.lower():
                matching.append(func)

        return matching

    @staticmethod
    def task_logger_safe(plan_id: str, task_num: int, task_name: str, **kwargs):
        """TaskLogger를 안전하게 생성하고 설정"""
        import ai_helpers_new as h

        try:
            # Logger 생성
            logger = h.create_task_logger(plan_id, task_num, task_name)

            # 지원되는 파라미터로 task_info 호출
            title = kwargs.get('title', task_name)
            priority = kwargs.get('priority', 'medium')
            estimate = kwargs.get('estimate', '1h')

            logger.task_info(title, priority=priority, estimate=estimate)

            # 추가 정보는 NOTE로 기록
            for key, value in kwargs.items():
                if key not in ['title', 'priority', 'estimate']:
                    logger.note(f"📌 {key}: {value}")

            return {'ok': True, 'logger': logger}

        except Exception as e:
            return {'ok': False, 'error': str(e)}

    @staticmethod
    def batch_operation(operation: Callable, items: List[Any], 
                       continue_on_error: bool = True) -> Dict[str, Any]:
        """여러 항목에 대해 작업을 안전하게 수행"""
        results = []
        errors = []

        for i, item in enumerate(items):
            result = SafeHelpers.safe_execute(operation, item)
            if result.get('ok'):
                results.append({'index': i, 'item': item, 'result': result.get('data')})
            else:
                errors.append({'index': i, 'item': item, 'error': result.get('error')})
                if not continue_on_error:
                    break

        return {
            'ok': len(errors) == 0,
            'success_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors
        }

# 편의 함수들
def safe_parse(file_path: str) -> Dict[str, Any]:
    """h.parse()의 안전한 버전 (간편 호출)"""
    return SafeHelpers.parse_safe(file_path)

def find_wait_functions(file_path: str) -> List[Dict[str, Any]]:
    """wait 관련 함수 찾기"""
    return SafeHelpers.find_functions_by_pattern(file_path, 'wait')

def safe_task_logger(plan_id: str, task_num: int, task_name: str, **kwargs):
    """TaskLogger 안전 생성 (간편 호출)"""
    return SafeHelpers.task_logger_safe(plan_id, task_num, task_name, **kwargs)
