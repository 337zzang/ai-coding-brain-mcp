"""
API 관리자 - 다양한 API를 동적으로 활성화/비활성화하고 helpers를 통해 접근할 수 있도록 함
"""
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class APIManager:
    """API를 동적으로 관리하는 클래스"""
    
    def __init__(self):
        self.enabled_apis: Dict[str, Any] = {}
        self.available_apis = {
            'image': 'python.api.image_generator.ImageGenerator',
            # 향후 추가 가능한 API들
            # 'translation': 'python.api.translator.Translator',
            # 'voice': 'python.api.voice_synthesizer.VoiceSynthesizer',
            'browser': 'python.api.web_automation_repl.REPLBrowser',
            'web_automation': 'python.api.web_automation_repl.REPLBrowser',  # REPL 호환 버전
        }
    def toggle_api(self, api_name: str, enabled: bool = True) -> Dict[str, Any]:
        """API를 활성화/비활성화"""
        if api_name not in self.available_apis:
            return {
                'success': False,
                'error': f"Unknown API: {api_name}. Available APIs: {list(self.available_apis.keys())}"
            }
            
        if enabled:
            if api_name not in self.enabled_apis:
                try:
                    # 동적으로 모듈 import
                    module_path = self.available_apis[api_name]
                    module_name, class_name = module_path.rsplit('.', 1)
                    
                    # importlib를 사용하여 동적 import
                    import importlib
                    module = importlib.import_module(module_name)
                    api_class = getattr(module, class_name)
                    
                    # API 인스턴스 생성
                    self.enabled_apis[api_name] = api_class()
                    
                    # helpers에 메서드 추가
                    self._inject_helpers(api_name)
                    
                    return {
                        'success': True,
                        'message': f"API '{api_name}' enabled successfully",
                        'methods': self._get_api_methods(api_name)
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"Failed to enable API '{api_name}': {str(e)}"
                    }
            else:
                return {
                    'success': True,
                    'message': f"API '{api_name}' is already enabled",
                    'methods': self._get_api_methods(api_name)
                }
        else:
            if api_name in self.enabled_apis:
                # API 비활성화
                del self.enabled_apis[api_name]
                
                # helpers에서 메서드 제거
                self._remove_helpers(api_name)
                
                return {
                    'success': True,
                    'message': f"API '{api_name}' disabled successfully"
                }
            else:
                return {
                    'success': True,
                    'message': f"API '{api_name}' is already disabled"
                }
                
    def list_apis(self) -> Dict[str, Any]:
        """사용 가능한 API 목록 반환"""
        return {
            'available': list(self.available_apis.keys()),
            'enabled': list(self.enabled_apis.keys()),
            'details': {
                api_name: {
                    'enabled': api_name in self.enabled_apis,
                    'methods': self._get_api_methods(api_name) if api_name in self.enabled_apis else []
                }
                for api_name in self.available_apis
            }
        }
        
    def _get_api_methods(self, api_name: str) -> list:
        """API의 사용 가능한 메서드 목록 반환"""
        if api_name not in self.enabled_apis:
            return []
            
        api_instance = self.enabled_apis[api_name]
        methods = [
            method for method in dir(api_instance)
            if not method.startswith('_') and callable(getattr(api_instance, method))
        ]
        return methods
        
    def _inject_helpers(self, api_name: str):
        """helpers 객체에 API 메서드 추가"""
        if api_name not in self.enabled_apis:
            return
            
        api_instance = self.enabled_apis[api_name]
        
        # helpers를 가져옴 (전역에서)
        import __main__
        if hasattr(__main__, 'helpers'):
            helpers = __main__.helpers
            
            # API별 메서드 매핑
            if api_name == 'image':
                # 이미지 API 메서드들을 helpers에 추가
                helpers.generate_image = api_instance.generate_image
                helpers.list_images = api_instance.list_images
                helpers.search_images = api_instance.search_images
            elif api_name in ['browser', 'web_automation']:
                # REPLBrowser 메서드들을 helpers에 추가
                helpers.browser_start = api_instance.start
                helpers.browser_goto = api_instance.goto
                helpers.browser_click = api_instance.click
                helpers.browser_type = api_instance.type
                helpers.browser_screenshot = api_instance.screenshot
                helpers.browser_wait = api_instance.wait
                helpers.browser_eval = api_instance.eval
                helpers.browser_get_content = api_instance.get_content
                helpers.browser_stop = api_instance.stop
    def _remove_helpers(self, api_name: str):
        """helpers 객체에서 API 메서드 제거"""
        import __main__
        if hasattr(__main__, 'helpers'):
            helpers = __main__.helpers
            
            # API별 메서드 제거
            if api_name == 'image':
                for method in ['generate_image', 'list_images', 'search_images']:
                    if hasattr(helpers, method):
                        delattr(helpers, method)
            elif api_name in ['browser', 'web_automation']:
                # REPLBrowser 메서드들 제거
                browser_methods = [
                    'browser_start',
                    'browser_goto',
                    'browser_click',
                    'browser_type',
                    'browser_screenshot',
                    'browser_wait',
                    'browser_eval',
                    'browser_get_content',
                    'browser_stop'
                ]
                for method in browser_methods:
                    if hasattr(helpers, method):
                        delattr(helpers, method)
# 전역 인스턴스 생성
api_manager = APIManager()
