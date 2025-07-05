"""
AI 이미지 생성 헬퍼 모듈
DALL-E 3를 사용하여 이미지를 생성하고 저장합니다.
OpenAI API v1.x 호환 버전
"""
import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from openai import OpenAI
from PIL import Image
from io import BytesIO
import hashlib
import base64

class ImageGenerator:
    """AI 이미지 생성 및 관리 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")
        
        # 새 버전 API 클라이언트 생성
        self.client = OpenAI(api_key=self.api_key)
        
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.image_dir = os.path.join(self.project_root, "image")
        self.metadata_file = os.path.join(self.image_dir, "image_metadata.json")
        
        # image 디렉토리가 없으면 생성
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        # 메타데이터 로드
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """이미지 메타데이터 로드"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"images": []}
        return {"images": []}
    
    def _save_metadata(self):
        """이미지 메타데이터 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def generate_image(self, 
                      prompt: str, 
                      filename: Optional[str] = None,
                      model: str = "dall-e-3", 
                      size: str = "1024x1024",
                      quality: str = "standard",
                      style: str = "vivid",
                      return_base64: bool = False) -> Dict[str, Any]:
        """
        DALL-E 3를 사용하여 이미지 생성
        
        Args:
            prompt: 이미지 생성 프롬프트
            filename: 저장할 파일명 (없으면 자동 생성)
            model: 사용할 모델 (dall-e-3 또는 dall-e-2)
            size: 이미지 크기 (1024x1024, 1024x1792, 1792x1024)
            quality: 품질 (standard 또는 hd)
            style: 스타일 (vivid 또는 natural)
            return_base64: base64 인코딩된 이미지 반환 여부
        
        Returns:
            생성된 이미지 정보
        """
        try:
            # 이미지 생성 요청 (새 API)
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            
            # 응답에서 URL과 수정된 프롬프트 추출
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt if hasattr(response.data[0], 'revised_prompt') else prompt
            
            # 파일명 생성
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                filename = f"dalle3_{timestamp}_{prompt_hash}.png"
            elif not filename.endswith(('.png', '.jpg', '.jpeg')):
                filename += '.png'
            
            # 이미지 다운로드 및 저장
            filepath = self.save_image_from_url(image_url, filename)
            
            # base64 인코딩 (선택적)
            base64_data = None
            if return_base64:
                with open(filepath, 'rb') as f:
                    base64_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 메타데이터 저장
            image_info = {
                "filename": filename,
                "filepath": filepath,
                "prompt": prompt,
                "revised_prompt": revised_prompt,
                "model": model,
                "size": size,
                "quality": quality,
                "style": style,
                "created_at": datetime.now().isoformat(),
                "url": image_url
            }
            
            self.metadata["images"].append(image_info)
            self._save_metadata()
            
            result = {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "prompt": prompt,
                "revised_prompt": revised_prompt,
                "model": model,
                "size": size,
                "quality": quality,
                "style": style,
                "url": image_url,
                "message": f"이미지가 성공적으로 생성되었습니다: {filename}"
            }
            
            if base64_data:
                result["base64"] = base64_data
                
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"이미지 생성 실패: {str(e)}"
            }
    
    def save_image_from_url(self, url: str, filename: str) -> str:
        """
        URL에서 이미지를 다운로드하여 저장
        
        Args:
            url: 이미지 URL
            filename: 저장할 파일명
        
        Returns:
            저장된 파일 경로
        """
        response = requests.get(url)
        response.raise_for_status()
        
        # PIL로 이미지 열기
        img = Image.open(BytesIO(response.content))
        
        # 파일 경로 생성
        filepath = os.path.join(self.image_dir, filename)
        
        # 이미지 저장
        img.save(filepath)
        
        return filepath
    
    def get_image_base64(self, filename: str) -> Optional[str]:
        """이미지를 base64로 인코딩하여 반환"""
        filepath = os.path.join(self.image_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        return None
    
    def list_images(self) -> list:
        """생성된 이미지 목록 반환"""
        return self.metadata.get("images", [])
    
    def get_image_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """특정 이미지의 정보 반환"""
        for image in self.metadata.get("images", []):
            if image["filename"] == filename:
                return image
        return None
    
    def search_images_by_prompt(self, keyword: str) -> list:
        """프롬프트 키워드로 이미지 검색"""
        results = []
        keyword_lower = keyword.lower()
        
        for image in self.metadata.get("images", []):
            if keyword_lower in image["prompt"].lower() or                keyword_lower in image.get("revised_prompt", "").lower():
                results.append(image)
        
        return results

# 헬퍼 함수들 (execute_code에서 쉽게 사용할 수 있도록)
def generate_ai_image(prompt: str, filename: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """AI 이미지 생성 간편 함수"""
    generator = ImageGenerator()
    return generator.generate_image(prompt, filename, **kwargs)

def list_ai_images() -> list:
    """생성된 이미지 목록 조회"""
    generator = ImageGenerator()
    return generator.list_images()

def search_ai_images(keyword: str) -> list:
    """키워드로 이미지 검색"""
    generator = ImageGenerator()
    return generator.search_images_by_prompt(keyword)

def get_image_base64(filename: str) -> Optional[str]:
    """이미지를 base64로 반환"""
    generator = ImageGenerator()
    return generator.get_image_base64(filename)
