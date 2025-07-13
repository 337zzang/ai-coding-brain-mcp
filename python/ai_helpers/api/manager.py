"""
API 관리 모듈
- API 활성화/비활성화 관리
- API 목록 조회
"""

import os
from typing import Dict, Any, Optional
from ai_helpers.decorators import track_operation


class APIManager:
    """API 관리 클래스"""
    
    def __init__(self):
        self._enabled_apis = {}  # API 활성화 상태 관리
        self._api_modules = {
            'image': 'ai_helpers.api.image',
            'web': 'ai_helpers.api.web_automation',
            'structure': 'ai_helpers.api.structure_tools'
        }
    
    @track_operation('api', 'toggle')
    def toggle_api(self, api_name: str, enabled: bool = True) -> Dict[str, Any]:
        """API 활성화/비활성화 토글
        
        Args:
            api_name: API 이름 (예: 'image', 'translator', 'voice' 등)
            enabled: 활성화 여부
        
        Returns:
            결과 딕셔너리
        """
        self._enabled_apis[api_name] = enabled
        
        status = "활성화" if enabled else "비활성화"
        return {
            "success": True,
            "api": api_name,
            "enabled": enabled,
            "message": f"{api_name} API가 {status}되었습니다."
        }
    
    @track_operation('api', 'list')
    def list_apis(self) -> Dict[str, bool]:
        """활성화된 API 목록 반환"""
        # 사용 가능한 API 확인
        available_apis = list(self._api_modules.keys())
        
        # API 상태 정보
        api_status = {}
        for api in available_apis:
            api_status[api] = self._enabled_apis.get(api, True)  # 기본값 True
        
        return api_status
    
    def check_api_enabled(self, api_name: str) -> bool:
        """API 활성화 상태 확인"""
        return self._enabled_apis.get(api_name, True)  # 기본값은 True
    
    def get_api_module(self, api_name: str) -> Optional[str]:
        """API 모듈 경로 반환"""
        return self._api_modules.get(api_name)


# 싱글톤 인스턴스
_api_manager = APIManager()

# 외부에서 사용할 함수들
def toggle_api(api_name: str, enabled: bool = True) -> Dict[str, Any]:
    """API 활성화/비활성화"""
    return _api_manager.toggle_api(api_name, enabled)

def list_apis() -> Dict[str, bool]:
    """API 목록 조회"""
    return _api_manager.list_apis()

def check_api_enabled(api_name: str) -> bool:
    """API 활성화 상태 확인"""
    return _api_manager.check_api_enabled(api_name)

# Updated API management for special features only

def get_available_apis():
    """사용 가능한 특수 기능 API 목록"""
    return ['image', 'web_automation']

def list_apis():
    """API 목록과 활성화 상태 반환"""
    available = get_available_apis()
    enabled = []

    # 각 API의 활성화 상태 확인 (간단한 구현)
    for api in available:
        if check_api_enabled(api):
            enabled.append(api)

    return {
        'available': available,
        'enabled': enabled
    }
