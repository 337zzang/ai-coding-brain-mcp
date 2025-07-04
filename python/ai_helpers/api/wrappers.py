"""
API 래퍼 함수들 - json_repl_session.py에서 사용
"""

from typing import Dict, Any, Optional, List
from ai_helpers.api.manager import check_api_enabled
from ai_helpers.decorators import track_operation


class ImageAPI:
    """이미지 API 래퍼 클래스"""
    
    @staticmethod
    @track_operation('api', 'generate_image')
    def generate_image(prompt: str, filename: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """AI를 사용하여 이미지 생성"""
        if not check_api_enabled('image'):
            return {
                "success": False,
                "error": "Image API가 비활성화되어 있습니다. helpers.toggle_api('image', True)로 활성화하세요."
            }
        
        try:
            # 지연 import
            from ai_helpers.api.image import generate_ai_image
            result = generate_ai_image(prompt, filename, **kwargs)
            return result
        except ImportError as e:
            return {
                "success": False,
                "error": f"이미지 생성 모듈을 로드할 수 없습니다: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"이미지 생성 중 오류 발생: {str(e)}"
            }
    
    @staticmethod
    @track_operation('api', 'list_images')
    def list_generated_images() -> List[Dict[str, Any]]:
        """생성된 이미지 목록 조회"""
        try:
            from ai_helpers.api.image import list_ai_images
            return list_ai_images()
        except Exception as e:
            return []
    
    @staticmethod
    @track_operation('api', 'search_images')
    def search_generated_images(keyword: str) -> List[Dict[str, Any]]:
        """키워드로 생성된 이미지 검색"""
        try:
            from ai_helpers.api.image import search_ai_images
            return search_ai_images(keyword)
        except Exception as e:
            return []
    
    @staticmethod
    @track_operation('api', 'get_image_base64')
    def get_image_base64(filename: str) -> Optional[str]:
        """이미지를 base64로 인코딩하여 반환"""
        try:
            from ai_helpers.api.image import get_image_base64
            return get_image_base64(filename)
        except Exception as e:
            return None
