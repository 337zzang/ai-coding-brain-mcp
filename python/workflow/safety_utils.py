"""
워크플로우 안정성 개선 유틸리티
작성일: 2025-07-08
목적: KeyError, TypeError, AttributeError 등 런타임 오류 방지
"""

import json
import re
from enum import Enum
from typing import Any, Dict, Optional, Union


class WorkflowSafetyUtils:
    """워크플로우 안정성을 위한 유틸리티 클래스"""

    @staticmethod
    def safe_get(data: dict, path: str, default=None) -> Any:
        """
        중첩된 딕셔너리에서 안전하게 값을 가져옴

        Args:
            data: 탐색할 딕셔너리
            path: 점(.)으로 구분된 키 경로 (예: 'status.plan.name')
            default: 키가 없을 때 반환할 기본값

        Returns:
            찾은 값 또는 기본값

        예시:
            >>> data = {'status': {'plan': {'name': '테스트'}}}
            >>> safe_get(data, 'status.plan.name', '이름없음')
            '테스트'
            >>> safe_get(data, 'status.plan.missing', '기본값')
            '기본값'
        """
        if not isinstance(data, dict):
            return default

        keys = path.split('.')
        result = data

        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
                if result is None:
                    return default
            else:
                return default

        return result if result is not None else default

    @staticmethod
    def serialize_enum(obj: Any) -> Any:
        """
        Enum 객체를 JSON 직렬화 가능한 형태로 변환

        Args:
            obj: 변환할 객체 (Enum, dict, list 등)

        Returns:
            직렬화 가능한 객체
        """
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: WorkflowSafetyUtils.serialize_enum(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [WorkflowSafetyUtils.serialize_enum(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(WorkflowSafetyUtils.serialize_enum(item) for item in obj)
        return obj

    @staticmethod
    def safe_json_dumps(data: Any, **kwargs) -> str:
        """
        Enum을 포함한 데이터를 안전하게 JSON으로 변환

        Args:
            data: JSON으로 변환할 데이터
            **kwargs: json.dumps에 전달할 추가 인자

        Returns:
            JSON 문자열
        """
        # 기본값 설정
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('indent', 2)

        return json.dumps(WorkflowSafetyUtils.serialize_enum(data), **kwargs)

    @staticmethod
    def safe_hasattr(obj: Any, attr: str) -> bool:
        """
        안전한 속성 존재 확인

        Args:
            obj: 확인할 객체
            attr: 속성 이름

        Returns:
            속성 존재 여부
        """
        if obj is None:
            return False
        return hasattr(obj, attr)

    @staticmethod
    def safe_getattr(obj: Any, attr: str, default=None) -> Any:
        """
        안전한 속성 접근

        Args:
            obj: 접근할 객체
            attr: 속성 이름
            default: 기본값

        Returns:
            속성 값 또는 기본값
        """
        if obj is None:
            return default
        return getattr(obj, attr, default)


class CommandParser:
    """워크플로우 명령어 파싱 헬퍼"""

    # 명령어 패턴 정의
    PATTERNS = {
        'task': re.compile(r'^([^|]+?)\s*(?:\|\s*(.+))?$'),
        'plan': re.compile(r'^([^|]+?)\s*(?:\|\s*(.+))?$'),
        'complete': re.compile(r'^(.*)$')  # 자유 형식
    }

    @classmethod
    def parse_task_command(cls, args: str) -> Dict[str, str]:
        """
        /task 제목 [| 설명] 형식 파싱

        Args:
            args: 파싱할 명령어 인자

        Returns:
            {'title': str, 'description': str}
        """
        args = args.strip()
        if not args:
            raise ValueError("태스크 제목은 필수입니다")

        match = cls.PATTERNS['task'].match(args)
        if match:
            return {
                'title': match.group(1).strip(),
                'description': (match.group(2) or '').strip()
            }

        # 매치 실패시 전체를 제목으로
        return {'title': args, 'description': ''}

    @classmethod
    def parse_plan_command(cls, args: str) -> Dict[str, str]:
        """
        /plan 이름 [| 설명] 형식 파싱

        Args:
            args: 파싱할 명령어 인자

        Returns:
            {'name': str, 'description': str}
        """
        args = args.strip()
        if not args:
            raise ValueError("플랜 이름은 필수입니다")

        match = cls.PATTERNS['plan'].match(args)
        if match:
            return {
                'name': match.group(1).strip(),
                'description': (match.group(2) or '').strip()
            }

        return {'name': args, 'description': ''}

    @classmethod
    def parse_complete_command(cls, args: str) -> Dict[str, str]:
        """
        /complete [메모] 형식 파싱

        Args:
            args: 파싱할 명령어 인자

        Returns:
            {'notes': str}
        """
        return {'notes': args.strip()}


class WorkflowValidator:
    """워크플로우 데이터 검증 헬퍼"""

    @staticmethod
    def validate_task_data(task_data: dict) -> bool:
        """태스크 데이터 구조 검증"""
        required_fields = ['id', 'title', 'status']
        return all(field in task_data for field in required_fields)

    @staticmethod
    def validate_plan_data(plan_data: dict) -> bool:
        """플랜 데이터 구조 검증"""
        required_fields = ['id', 'name', 'tasks']
        return all(field in plan_data for field in required_fields)

    @staticmethod
    def ensure_dict(data: Any, default: Optional[dict] = None) -> dict:
        """
        데이터가 딕셔너리인지 확인하고, 아니면 기본값 반환

        Args:
            data: 확인할 데이터
            default: 기본값 (None인 경우 빈 딕셔너리)

        Returns:
            딕셔너리
        """
        if isinstance(data, dict):
            return data
        return default if default is not None else {}


# 편의 함수들
def safe_get(data: dict, path: str, default=None) -> Any:
    """WorkflowSafetyUtils.safe_get의 단축 버전"""
    return WorkflowSafetyUtils.safe_get(data, path, default)


def safe_json(data: Any, **kwargs) -> str:
    """WorkflowSafetyUtils.safe_json_dumps의 단축 버전"""
    return WorkflowSafetyUtils.safe_json_dumps(data, **kwargs)
