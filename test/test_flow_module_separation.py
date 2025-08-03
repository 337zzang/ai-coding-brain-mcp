"""
Flow 시스템 분리 후 단위 테스트
작성일: 2025-08-03
"""

import pytest
import sys
import os

# 테스트를 위한 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_helpers_new.flow_api import FlowAPI
from ai_helpers_new.flow_cli import flow, get_flow_api_instance
from ai_helpers_new.flow_views import show_status, show_plans
from ai_helpers_new.flow_manager_utils import get_manager


class TestFlowModuleSeparation:
    """Flow 시스템 모듈 분리 테스트"""

    def test_flow_api_import(self):
        """FlowAPI 클래스 import 테스트"""
        assert FlowAPI is not None

    def test_flow_cli_import(self):
        """CLI 함수 import 테스트"""
        assert flow is not None
        assert callable(flow)

    def test_flow_views_import(self):
        """View 함수 import 테스트"""
        assert show_status is not None
        assert show_plans is not None
        assert callable(show_status)
        assert callable(show_plans)

    def test_manager_utils_import(self):
        """Manager 유틸리티 import 테스트"""
        assert get_manager is not None
        assert callable(get_manager)

    def test_flow_api_instance(self):
        """FlowAPI 인스턴스 생성 테스트"""
        api = get_flow_api_instance()
        assert api is not None
        assert isinstance(api, FlowAPI)

    def test_backwards_compatibility(self):
        """레거시 호환성 테스트"""
        # simple_flow_commands에서 모든 함수 import 가능한지 확인
        from ai_helpers_new.simple_flow_commands import (
            FlowAPI, flow, show_status, get_manager
        )
        assert all([FlowAPI, flow, show_status, get_manager])


class TestFlowCLI:
    """Flow CLI 기능 테스트"""

    def test_flow_status_command(self):
        """flow /status 명령 테스트"""
        result = flow("/status")
        assert result is not None
        assert isinstance(result, (str, dict))

    def test_flow_help_command(self):
        """flow /help 명령 테스트"""
        result = flow("/help")
        assert result is not None
        assert "사용 가능한 명령어" in str(result) or "Available commands" in str(result)


if __name__ == "__main__":
    # 간단한 테스트 실행
    print("🧪 Flow 시스템 모듈 분리 테스트 시작")

    # Import 테스트
    try:
        from ai_helpers_new.flow_api import FlowAPI
        from ai_helpers_new.flow_cli import flow
        from ai_helpers_new.flow_views import show_status
        from ai_helpers_new.flow_manager_utils import get_manager
        print("✅ 모든 모듈 import 성공")
    except ImportError as e:
        print(f"❌ Import 오류: {e}")

    # FlowAPI 인스턴스 테스트
    try:
        from ai_helpers_new.flow_cli import get_flow_api_instance
        api = get_flow_api_instance()
        print(f"✅ FlowAPI 인스턴스 생성 성공: {type(api)}")
    except Exception as e:
        print(f"❌ FlowAPI 인스턴스 오류: {e}")

    # 레거시 호환성 테스트
    try:
        from ai_helpers_new.simple_flow_commands import flow as legacy_flow
        print("✅ 레거시 호환성 유지됨")
    except ImportError as e:
        print(f"❌ 레거시 호환성 오류: {e}")

    print("\n테스트 완료!")
