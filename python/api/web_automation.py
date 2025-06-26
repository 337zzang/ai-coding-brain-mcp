"""
Playwright 기반 웹 자동화 API 모듈

이 모듈은 웹 스크래핑 및 자동화를 위한 헬퍼 클래스를 제공합니다.
브라우저 제어, 페이지 조작, 데이터 추출 등의 기능을 포함합니다.
"""

import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from playwright.sync_api import sync_playwright, Browser, Page, Playwright

# 로거 설정
logger = logging.getLogger(__name__)


class WebAutomation:
    """웹 스크래핑 및 자동화 헬퍼 클래스
    
    Playwright를 사용하여 브라우저를 제어하고 웹 페이지와 상호작용합니다.
    모든 메서드는 일관된 응답 형식을 반환합니다:
    {"success": bool, "message": str, ...}
    """
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        """WebAutomation 인스턴스 초기화
        
        Args:
            headless: 헤드리스 모드 실행 여부 (기본값: True)
            browser_type: 브라우저 종류 - "chromium", "firefox", "webkit" (기본값: "chromium")
        """
        self.headless = headless
        self.browser_type = browser_type
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        
        # 초기화 시간 기록
        self.initialized_at = datetime.now()
        
        try:
            # Playwright 시작
            self.playwright = sync_playwright().start()
            logger.info(f"Playwright 시작 완료 (browser_type: {browser_type}, headless: {headless})")
            
            # 브라우저 실행
            self._launch_browser()
            
        except Exception as e:
            logger.error(f"WebAutomation 초기화 실패: {str(e)}")
            self.close()
            raise
    
    def _launch_browser(self):
        """브라우저 실행 (내부 메서드)"""
        try:
            # 브라우저 타입에 따라 실행
            if self.browser_type == "chromium":
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )
            elif self.browser_type == "firefox":
                self.browser = self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"지원하지 않는 브라우저 타입: {self.browser_type}")
            
            # 브라우저 컨텍스트 생성 (쿠키, 세션 등 관리)
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            logger.info(f"{self.browser_type} 브라우저 실행 완료")
            
        except Exception as e:
            logger.error(f"브라우저 실행 실패: {str(e)}")
            raise
    
    def close(self):
        """브라우저 및 Playwright 종료
        
        Returns:
            Dict: 종료 결과
        """
        try:
            # 페이지 닫기
            if self.page:
                self.page.close()
                self.page = None
            
            # 컨텍스트 닫기
            if self.context:
                self.context.close()
                self.context = None
            
            # 브라우저 닫기
            if self.browser:
                self.browser.close()
                self.browser = None
            
            # Playwright 종료
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            logger.info("WebAutomation 리소스 정리 완료")
            
            return {
                "success": True,
                "message": "브라우저가 성공적으로 종료되었습니다."
            }
            
        except Exception as e:
            logger.error(f"종료 중 오류 발생: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"브라우저 종료 실패: {str(e)}"
            }
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()
    

    def go_to_page(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """지정된 URL로 페이지 이동
        
        Args:
            url: 이동할 URL
            wait_until: 페이지 로드 대기 조건
                - "networkidle": 네트워크 활동이 없을 때까지 대기 (기본값)
                - "domcontentloaded": DOM 로드 완료 시
                - "load": load 이벤트 발생 시
                - "commit": 네비게이션 커밋 시
        
        Returns:
            Dict: 작업 결과
                - success: 성공 여부
                - url: 최종 URL (리다이렉트 고려)
                - title: 페이지 제목
                - message: 결과 메시지
                - load_time: 로드 시간 (초)
        """
        start_time = datetime.now()
        
        try:
            # 새 페이지 생성 또는 기존 페이지 사용
            if not self.page:
                self.page = self.context.new_page()
                logger.info("새 페이지 생성")
            
            # URL 유효성 기본 검사
            if not url.startswith(('http://', 'https://')):
                # 프로토콜이 없으면 https 추가
                url = f"https://{url}"
                logger.info(f"프로토콜 추가: {url}")
            
            # 페이지 이동
            logger.info(f"페이지 이동 시작: {url}")
            response = self.page.goto(
                url, 
                wait_until=wait_until,
                timeout=30000  # 30초 타임아웃
            )
            
            # 응답 상태 확인
            if response and response.status >= 400:
                logger.warning(f"HTTP 에러: {response.status}")
            
            # 페이지 로드 완료 대기
            self.page.wait_for_load_state(wait_until)
            
            # 최종 URL 및 제목 가져오기
            final_url = self.page.url
            title = self.page.title()
            
            load_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"페이지 이동 성공: {final_url} (로드 시간: {load_time:.2f}초)")
            
            return {
                "success": True,
                "url": final_url,
                "title": title,
                "message": f"페이지 이동 성공: {title}",
                "load_time": load_time,
                "status_code": response.status if response else None
            }
            
        except TimeoutError as e:
            logger.error(f"페이지 로드 타임아웃: {url}")
            return {
                "success": False,
                "error": "TimeoutError",
                "message": f"페이지 로드 타임아웃: {url}",
                "url": url
            }
            
        except Exception as e:
            logger.error(f"페이지 이동 실패: {str(e)}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"페이지 이동 실패: {str(e)}",
                "url": url
            }

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회
        
        Returns:
            Dict: 브라우저 및 페이지 상태 정보
        """
        return {
            "success": True,
            "browser_type": self.browser_type,
            "headless": self.headless,
            "browser_running": self.browser is not None,
            "page_open": self.page is not None,
            "current_url": self.page.url if self.page else None,
            "initialized_at": self.initialized_at.isoformat(),
            "message": "상태 조회 성공"
        }



# 테스트 코드 (모듈 직접 실행 시)
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # WebAutomation 테스트
    print("🧪 WebAutomation 클래스 테스트")
    
    try:
        # 컨텍스트 매니저로 사용
        with WebAutomation(headless=True) as browser:
            # 상태 확인
            status = browser.get_status()
            print(f"✅ 브라우저 상태: {status}")
            
            # 페이지 이동 테스트
            result = browser.go_to_page("https://www.example.com")
            if result["success"]:
                print(f"✅ 페이지 이동 성공: {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   로드 시간: {result['load_time']:.2f}초")
            else:
                print(f"❌ 페이지 이동 실패: {result['message']}")
            
        print("✅ 브라우저 정상 종료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

