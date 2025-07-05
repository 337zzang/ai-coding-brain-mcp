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


    def extract_text(self, selector: str, by: str = "css", all_matches: bool = False,
                    timeout: int = 30000) -> Dict[str, Any]:
        """특정 요소의 텍스트를 추출
        
        Args:
            selector: 요소 선택자
            by: 선택자 유형 (click_element와 동일)
            all_matches: True일 경우 모든 매칭 요소의 텍스트 추출
            timeout: 대기 시간 (밀리초)
        
        Returns:
            Dict: 작업 결과
                - text: 추출된 텍스트 (단일) 또는 texts: 텍스트 리스트 (다중)
        """
        try:
            if not self.page:
                return {
                    "success": False,
                    "error": "NoPageError",
                    "message": "페이지가 열려있지 않습니다. go_to_page()를 먼저 호출하세요."
                }
            
            logger.info(f"텍스트 추출 시도: {selector} (by={by}, all={all_matches})")
            
            # locator 생성
            locator = self._get_locator(selector, by)
            
            if all_matches:
                # 모든 매칭 요소 처리
                try:
                    # 첫 번째 요소가 나타날 때까지 대기
                    locator.first.wait_for(state="visible", timeout=timeout)
                    
                    # 모든 요소의 텍스트 추출
                    elements = locator.all()
                    texts = []
                    for element in elements:
                        text = element.text_content()
                        if text:
                            texts.append(text.strip())
                    
                    logger.info(f"텍스트 추출 성공: {len(texts)}개 요소")
                    
                    return {
                        "success": True,
                        "message": f"{len(texts)}개 요소에서 텍스트 추출 완료",
                        "texts": texts,
                        "count": len(texts),
                        "selector": selector,
                        "by": by
                    }
                    
                except TimeoutError:
                    # 요소를 찾지 못한 경우 빈 리스트 반환
                    return {
                        "success": True,
                        "message": "매칭되는 요소를 찾을 수 없습니다",
                        "texts": [],
                        "count": 0,
                        "selector": selector,
                        "by": by
                    }
            else:
                # 단일 요소 처리
                locator.wait_for(state="visible", timeout=timeout)
                
                # 텍스트 추출
                text = locator.text_content()
                
                # inner_text도 시도 (더 정확한 가시적 텍스트)
                if not text or not text.strip():
                    text = locator.inner_text()
                
                if text:
                    text = text.strip()
                
                logger.info(f"텍스트 추출 성공: {len(text) if text else 0}자")
                
                return {
                    "success": True,
                    "message": "텍스트 추출 성공",
                    "text": text or "",
                    "length": len(text) if text else 0,
                    "selector": selector,
                    "by": by
                }
                
        except TimeoutError:
            logger.error(f"텍스트 추출 타임아웃: {selector}")
            return {
                "success": False,
                "error": "TimeoutError",
                "message": f"요소를 찾을 수 없습니다: {selector}",
                "selector": selector,
                "by": by
            }
            
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {str(e)}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"텍스트 추출 실패: {str(e)}",
                "selector": selector,
                "by": by
            }
    
    def scroll_page(self, amount: int = 0, to: str = "bottom", 
                   smooth: bool = True, wait_after: int = 500) -> Dict[str, Any]:
        """페이지를 스크롤
        
        Args:
            amount: 스크롤할 픽셀 수 (0이면 to 파라미터 사용)
            to: 스크롤 위치
                - "bottom": 페이지 끝 (기본값)
                - "top": 페이지 상단
                - "element:selector": 특정 요소로 스크롤
            smooth: 부드러운 스크롤 여부
            wait_after: 스크롤 후 대기 시간 (밀리초)
        
        Returns:
            Dict: 작업 결과
        """
        try:
            if not self.page:
                return {
                    "success": False,
                    "error": "NoPageError",
                    "message": "페이지가 열려있지 않습니다. go_to_page()를 먼저 호출하세요."
                }
            
            logger.info(f"페이지 스크롤: amount={amount}, to={to}")
            
            # 스크롤 전 위치 저장
            before_position = self.page.evaluate("window.pageYOffset")
            
            # 스크롤 동작
            if amount > 0:
                # 특정 픽셀만큼 스크롤
                self.page.evaluate(f"""
                    window.scrollBy({{
                        top: {amount},
                        behavior: '{"smooth" if smooth else "instant"}'
                    }})
                """)
                action = f"{amount}px 스크롤"
                
            elif to == "bottom":
                # 페이지 끝으로 스크롤
                self.page.evaluate(f"""
                    window.scrollTo({{
                        top: document.body.scrollHeight,
                        behavior: '{"smooth" if smooth else "instant"}'
                    }})
                """)
                action = "페이지 끝으로 스크롤"
                
            elif to == "top":
                # 페이지 상단으로 스크롤
                self.page.evaluate(f"""
                    window.scrollTo({{
                        top: 0,
                        behavior: '{"smooth" if smooth else "instant"}'
                    }})
                """)
                action = "페이지 상단으로 스크롤"
                
            elif to.startswith("element:"):
                # 특정 요소로 스크롤
                selector = to[8:]  # "element:" 제거
                try:
                    locator = self.page.locator(selector)
                    locator.scroll_into_view_if_needed()
                    action = f"요소로 스크롤: {selector}"
                except:
                    return {
                        "success": False,
                        "error": "ElementNotFound",
                        "message": f"스크롤 대상 요소를 찾을 수 없습니다: {selector}"
                    }
            else:
                return {
                    "success": False,
                    "error": "InvalidParameter",
                    "message": f"올바르지 않은 스크롤 대상: {to}"
                }
            
            # 스크롤 후 대기
            if wait_after > 0:
                self.page.wait_for_timeout(wait_after)
            
            # 스크롤 후 위치
            after_position = self.page.evaluate("window.pageYOffset")
            scroll_distance = after_position - before_position
            
            # 페이지 정보
            page_height = self.page.evaluate("document.body.scrollHeight")
            viewport_height = self.page.evaluate("window.innerHeight")
            
            logger.info(f"스크롤 완료: {action} (이동거리: {abs(scroll_distance)}px)")
            
            return {
                "success": True,
                "message": f"스크롤 완료: {action}",
                "before_position": before_position,
                "after_position": after_position,
                "scroll_distance": scroll_distance,
                "page_height": page_height,
                "viewport_height": viewport_height,
                "at_bottom": after_position + viewport_height >= page_height - 10,
                "at_top": after_position <= 10
            }
            
        except Exception as e:
            logger.error(f"스크롤 실패: {str(e)}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"스크롤 실패: {str(e)}"
            }
    
    def get_page_content(self) -> Dict[str, Any]:
        """전체 페이지 콘텐츠 가져오기 (보너스 메서드)
        
        Returns:
            Dict: 페이지 HTML 및 텍스트 콘텐츠
        """
        try:
            if not self.page:
                return {
                    "success": False,
                    "error": "NoPageError",
                    "message": "페이지가 열려있지 않습니다."
                }
            
            # HTML 콘텐츠
            html = self.page.content()
            
            # 전체 텍스트 (보이는 텍스트만)
            text = self.page.locator("body").inner_text()
            
            return {
                "success": True,
                "message": "페이지 콘텐츠 추출 성공",
                "html_length": len(html),
                "text_length": len(text),
                "text": text,
                "title": self.page.title(),
                "url": self.page.url
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"콘텐츠 추출 실패: {str(e)}"
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

    def handle_login(self, login_url: str, username: str, password: str,
                    username_selector: str = "input[name='username']",
                    password_selector: str = "input[name='password']", 
                    submit_selector: str = "button[type='submit']",
                    success_indicator: Optional[str] = None,
                    wait_after_login: int = 2000) -> Dict[str, Any]:
        """범용적인 로그인 프로세스 자동화
        
        Args:
            login_url: 로그인 페이지 URL
            username: 사용자명/이메일
            password: 비밀번호
            username_selector: 아이디 입력 필드 선택자
            password_selector: 비밀번호 입력 필드 선택자
            submit_selector: 로그인 버튼 선택자
            success_indicator: 로그인 성공 판단 기준 (선택자 또는 URL 패턴)
            wait_after_login: 로그인 후 대기 시간 (밀리초)
        
        Returns:
            Dict: 로그인 결과
                - success: 로그인 성공 여부
                - message: 결과 메시지
                - final_url: 로그인 후 최종 URL
                - login_time: 로그인 소요 시간
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"로그인 프로세스 시작: {login_url}")
            
            # 1. 로그인 페이지로 이동
            goto_result = self.go_to_page(login_url)
            if not goto_result["success"]:
                return {
                    "success": False,
                    "error": "NavigationError",
                    "message": f"로그인 페이지 접속 실패: {goto_result['message']}",
                    "login_url": login_url
                }
            
            # 로그인 전 URL 저장
            before_login_url = self.page.url
            
            # 2. 아이디 입력
            logger.info("아이디 입력 중...")
            username_result = self.input_text(
                username_selector, 
                username,
                clear_first=True
            )
            if not username_result["success"]:
                return {
                    "success": False,
                    "error": "UsernameInputError", 
                    "message": f"아이디 입력 실패: {username_result['message']}",
                    "selector": username_selector
                }
            
            # 3. 비밀번호 입력
            logger.info("비밀번호 입력 중...")
            password_result = self.input_text(
                password_selector,
                password,
                clear_first=True
            )
            if not password_result["success"]:
                return {
                    "success": False,
                    "error": "PasswordInputError",
                    "message": f"비밀번호 입력 실패: {password_result['message']}",
                    "selector": password_selector
                }
            
            # 4. 로그인 버튼 클릭
            logger.info("로그인 버튼 클릭...")
            
            # 네트워크 요청 대기를 위한 준비
            with self.page.expect_navigation(wait_until="networkidle", timeout=30000):
                click_result = self.click_element(submit_selector)
                if not click_result["success"]:
                    return {
                        "success": False,
                        "error": "SubmitClickError",
                        "message": f"로그인 버튼 클릭 실패: {click_result['message']}",
                        "selector": submit_selector
                    }
            
            # 5. 로그인 후 대기
            if wait_after_login > 0:
                self.page.wait_for_timeout(wait_after_login)
            
            # 6. 로그인 성공 여부 확인
            after_login_url = self.page.url
            login_success = False
            success_method = ""
            
            # URL 변경 확인
            if after_login_url != before_login_url and after_login_url != login_url:
                login_success = True
                success_method = "URL 변경 감지"
            
            # success_indicator가 제공된 경우 추가 확인
            if success_indicator:
                if success_indicator.startswith("http"):
                    # URL 패턴으로 확인
                    if success_indicator in after_login_url:
                        login_success = True
                        success_method = "URL 패턴 일치"
                else:
                    # 요소 존재로 확인
                    try:
                        self.page.wait_for_selector(success_indicator, timeout=5000)
                        login_success = True
                        success_method = "성공 요소 발견"
                    except:
                        # 로그인 실패 요소 확인 (옵션)
                        error_selectors = [
                            ".error-message",
                            ".alert-danger", 
                            "[class*='error']",
                            "[class*='fail']"
                        ]
                        for error_sel in error_selectors:
                            try:
                                error_element = self.page.locator(error_sel).first
                                if error_element.is_visible():
                                    error_text = error_element.text_content()
                                    return {
                                        "success": False,
                                        "error": "LoginFailed",
                                        "message": f"로그인 실패: {error_text}",
                                        "final_url": after_login_url,
                                        "error_selector": error_sel
                                    }
                            except:
                                continue
            
            login_time = (datetime.now() - start_time).total_seconds()
            
            if login_success:
                logger.info(f"로그인 성공! ({success_method})")
                
                # 쿠키 정보 (선택적)
                cookies = self.context.cookies()
                
                return {
                    "success": True,
                    "message": f"로그인 성공 ({success_method})",
                    "before_url": before_login_url,
                    "final_url": after_login_url,
                    "login_time": login_time,
                    "cookie_count": len(cookies),
                    "username": username[:3] + "***"  # 일부만 표시
                }
            else:
                logger.warning("로그인 성공 여부를 확인할 수 없습니다")
                return {
                    "success": False,
                    "error": "LoginVerificationFailed",
                    "message": "로그인 성공 여부를 확인할 수 없습니다",
                    "before_url": before_login_url,
                    "final_url": after_login_url,
                    "login_time": login_time
                }
                
        except Exception as e:
            logger.error(f"로그인 프로세스 오류: {str(e)}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"로그인 프로세스 오류: {str(e)}",
                "login_url": login_url
            }
    
    def is_logged_in(self, check_selector: Optional[str] = None, 
                    check_url_pattern: Optional[str] = None) -> bool:
        """현재 로그인 상태 확인 (보너스 메서드)
        
        Args:
            check_selector: 로그인 상태 확인용 요소 선택자
            check_url_pattern: 로그인 상태 확인용 URL 패턴
        
        Returns:
            bool: 로그인 여부
        """
        try:
            if not self.page:
                return False
            
            # URL 패턴 확인
            if check_url_pattern and check_url_pattern in self.page.url:
                return True
            
            # 요소 존재 확인
            if check_selector:
                try:
                    element = self.page.locator(check_selector).first
                    return element.is_visible()
                except:
                    return False
            
            # 쿠키 확인 (일반적인 세션 쿠키명들)
            cookies = self.context.cookies()
            session_cookie_names = ['session', 'sessionid', 'auth', 'token', 'jwt']
            for cookie in cookies:
                if any(name in cookie['name'].lower() for name in session_cookie_names):
                    return True
            
            return False
            
        except:
            return False


    def _get_locator(self, selector: str, by: str = "css"):
        """선택자 타입에 따라 적절한 locator 반환 (내부 메서드)"""
        if not self.page:
            raise Exception("페이지가 열려있지 않습니다. go_to_page()를 먼저 호출하세요.")
        
        by_lower = by.lower()
        
        if by_lower == "css":
            return self.page.locator(selector)
        elif by_lower == "xpath":
            return self.page.locator(f"xpath={selector}")
        elif by_lower == "text":
            return self.page.get_by_text(selector, exact=False)
        elif by_lower == "text_exact":
            return self.page.get_by_text(selector, exact=True)
        elif by_lower == "role":
            # role 선택자 예: "button:Submit"
            if ":" in selector:
                role, name = selector.split(":", 1)
                return self.page.get_by_role(role, name=name)
            else:
                return self.page.get_by_role(selector)
        elif by_lower == "label":
            return self.page.get_by_label(selector)
        elif by_lower == "placeholder":
            return self.page.get_by_placeholder(selector)
        elif by_lower == "alt":
            return self.page.get_by_alt_text(selector)
        elif by_lower == "title":
            return self.page.get_by_title(selector)
        else:
            raise ValueError(f"지원하지 않는 선택자 타입: {by}")
    
    def click_element(self, selector: str, by: str = "css", wait_for: bool = True, 
                     timeout: int = 30000) -> Dict[str, Any]:
        """지정한 요소를 클릭
        
        Args:
            selector: 요소 선택자
            by: 선택자 유형
                - "css": CSS 선택자 (기본값)
                - "xpath": XPath 선택자
                - "text": 텍스트 포함 (부분 일치)
                - "text_exact": 텍스트 정확히 일치
                - "role": ARIA role (예: "button:Submit")
                - "label": label 텍스트
                - "placeholder": placeholder 텍스트
                - "alt": alt 텍스트
                - "title": title 속성
            wait_for: 요소가 클릭 가능할 때까지 대기 여부
            timeout: 대기 시간 (밀리초)
        
        Returns:
            Dict: 작업 결과
        """
        try:
            if not self.page:
                return {
                    "success": False,
                    "error": "NoPageError",
                    "message": "페이지가 열려있지 않습니다. go_to_page()를 먼저 호출하세요."
                }
            
            logger.info(f"요소 클릭 시도: {selector} (by={by})")
            
            # locator 생성
            locator = self._get_locator(selector, by)
            
            # 요소가 나타날 때까지 대기
            if wait_for:
                locator.wait_for(state="visible", timeout=timeout)
                locator.wait_for(state="enabled", timeout=timeout)
            
            # 클릭 전 현재 URL 저장
            before_url = self.page.url
            
            # 클릭 수행
            locator.click(timeout=timeout)
            
            # 클릭 후 잠시 대기 (네트워크 요청 등)
            self.page.wait_for_timeout(100)
            
            # 페이지 변경 확인
            after_url = self.page.url
            page_changed = before_url != after_url
            
            logger.info(f"요소 클릭 성공: {selector}")
            
            return {
                "success": True,
                "message": f"요소 클릭 완료: {selector}",
                "selector": selector,
                "by": by,
                "page_changed": page_changed,
                "new_url": after_url if page_changed else None
            }
            
        except TimeoutError:
            logger.error(f"요소 클릭 타임아웃: {selector}")
            return {
                "success": False,
                "error": "TimeoutError",
                "message": f"요소를 찾을 수 없거나 클릭할 수 없습니다: {selector}",
                "selector": selector,
                "by": by
            }
            
        except Exception as e:
            logger.error(f"요소 클릭 실패: {str(e)}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"클릭 실패: {str(e)}",
                "selector": selector,
                "by": by
            }
    
    def input_text(self, selector: str, text: str, by: str = "css", 
                   clear_first: bool = True, press_enter: bool = False,
                   timeout: int = 30000) -> Dict[str, Any]:
        """입력 필드에 텍스트 입력
        
        Args:
            selector: 입력 필드 선택자
            text: 입력할 텍스트
            by: 선택자 유형 (click_element와 동일)
            clear_first: 입력 전 기존 텍스트 지우기
            press_enter: 입력 후 Enter 키 누르기
            timeout: 대기 시간 (밀리초)
        
        Returns:
            Dict: 작업 결과
        """
        try:
            if not self.page:
                return {
                    "success": False,
                    "error": "NoPageError",
                    "message": "페이지가 열려있지 않습니다. go_to_page()를 먼저 호출하세요."
                }
            
            logger.info(f"텍스트 입력 시도: {selector} (by={by})")
            
            # locator 생성
            locator = self._get_locator(selector, by)
            
            # 요소가 나타날 때까지 대기
            locator.wait_for(state="visible", timeout=timeout)
            locator.wait_for(state="enabled", timeout=timeout)
            
            # 입력 필드 포커스
            locator.focus()
            
            # 기존 텍스트 지우기
            if clear_first:
                # Ctrl+A 후 Delete
                locator.press("Control+a")
                locator.press("Delete")
            
            # 텍스트 입력
            locator.fill(text)
            
            # Enter 키 누르기
            if press_enter:
                locator.press("Enter")
                # Enter 후 잠시 대기
                self.page.wait_for_timeout(100)
            
            logger.info(f"텍스트 입력 성공: {selector}")
            
            # 마스킹이 필요한 필드 확인 (password, secret 등)
            is_sensitive = any(word in selector.lower() for word in ['password', 'secret', 'token', 'key'])
            
            return {
                "success": True,
                "message": f"텍스트 입력 완료",
                "selector": selector,
                "by": by,
                "text_length": len(text),
                "value": "***" if is_sensitive else text[:20] + "..." if len(text) > 20 else text,
                "press_enter": press_enter
            }
            
        except TimeoutError:
            logger.error(f"입력 필드 타임아웃: {selector}")
            return {
                "success": False,
                "error": "TimeoutError",
                "message": f"입력 필드를 찾을 수 없습니다: {selector}",
                "selector": selector,
                "by": by
            }
            
        except Exception as e:
            logger.error(f"텍스트 입력 실패: {str(e)}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": f"입력 실패: {str(e)}",
                "selector": selector,
                "by": by
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

