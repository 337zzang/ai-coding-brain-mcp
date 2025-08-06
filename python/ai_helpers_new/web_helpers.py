"""
웹 자동화 헬퍼 함수
Playwright 기반 웹 자동화 유틸리티
"""
from typing import Dict, Any, Optional, Union
from .wrappers import ensure_response, safe_execution


@safe_execution
def handle_popup(page, button_text: str = "예", force: bool = True) -> Dict[str, Any]:
    """범용 팝업 처리 함수

    다양한 유형의 웹 팝업/모달/다이얼로그를 처리합니다.
    여러 선택자를 시도하고, 실패 시 JavaScript로 직접 클릭합니다.

    Args:
        page: Playwright page 객체
        button_text: 클릭할 버튼의 텍스트 (기본값: "예")
        force: 강제 클릭 여부 (기본값: True) - 요소가 가려져 있어도 클릭

    Returns:
        표준 응답 형식 {'ok': bool, 'data': dict, 'error': str}
        성공 시 data에는 {'clicked': True, 'method': str} 포함

    Examples:
        >>> result = h.handle_popup(page, "확인")
        >>> if result['ok']:
        ...     print(f"팝업 처리 완료: {result['data']['method']}")
    """
    # 다양한 팝업 선택자 시도
    selectors = [
        f'[role="dialog"] button:has-text("{button_text}")',
        f'[role="alertdialog"] button:has-text("{button_text}")',
        f'.modal button:has-text("{button_text}")',
        f'[class*="popup"] button:has-text("{button_text}")',
        f'[class*="dialog"] button:has-text("{button_text}")',
        f'[class*="overlay"] button:has-text("{button_text}")',
        f'div[style*="z-index"] button:has-text("{button_text}")',
        f'button:has-text("{button_text}"):visible'
    ]

    # 각 선택자로 클릭 시도
    for i, selector in enumerate(selectors):
        try:
            # 요소가 존재하는지 확인 (타임아웃 짧게)
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click(force=force, timeout=2000)
                return ensure_response({
                    'clicked': True,
                    'method': 'selector',
                    'selector_index': i,
                    'selector': selector
                })
        except Exception:
            continue

    # 모든 선택자 실패 시 JavaScript로 직접 클릭
    try:
        result = page.evaluate(f'''
            (() => {{
                const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
                for(let btn of buttons) {{
                    const text = btn.textContent || btn.value || '';
                    if(text.includes('{button_text}')) {{
                        btn.click();
                        return {{
                            clicked: true,
                            element: btn.tagName.toLowerCase(),
                            text: text.trim()
                        }};
                    }}
                }}
                return {{clicked: false}};
            }})()
        ''')

        if result and result.get('clicked'):
            return ensure_response({
                'clicked': True,
                'method': 'javascript',
                'element': result.get('element'),
                'text': result.get('text')
            })
        else:
            return ensure_response(
                None,
                error=f"버튼 '{button_text}'을(를) 찾을 수 없습니다"
            )

    except Exception as e:
        return ensure_response(
            None,
            error=f"JavaScript 실행 실패: {str(e)}",
            exception=e
        )


@safe_execution  
def handle_alert(page, accept: bool = True, text: Optional[str] = None) -> Dict[str, Any]:
    """브라우저 alert/confirm/prompt 처리

    Args:
        page: Playwright page 객체
        accept: 수락 여부 (True: 확인, False: 취소)
        text: prompt의 경우 입력할 텍스트

    Returns:
        표준 응답 형식
    """
    try:
        # alert 이벤트 핸들러 등록
        def handle_dialog(dialog):
            if text is not None:
                dialog.accept(text)
            elif accept:
                dialog.accept()
            else:
                dialog.dismiss()

        page.on("dialog", handle_dialog)

        return ensure_response({
            'handler_registered': True,
            'accept': accept,
            'text': text
        })

    except Exception as e:
        return ensure_response(
            None,
            error=f"Alert 핸들러 등록 실패: {str(e)}",
            exception=e
        )


@safe_execution
def wait_and_click(page, selector: str, timeout: int = 5000, force: bool = False) -> Dict[str, Any]:
    """요소가 나타날 때까지 기다린 후 클릭

    Args:
        page: Playwright page 객체
        selector: CSS 선택자 또는 텍스트 선택자
        timeout: 대기 시간 (밀리초)
        force: 강제 클릭 여부

    Returns:
        표준 응답 형식
    """
    try:
        # 선택자가 텍스트인 경우 자동 변환
        if not any(char in selector for char in ['#', '.', '[', ':', '>']):
            selector = f'text="{selector}"'

        # 요소 대기
        page.wait_for_selector(selector, timeout=timeout, state="visible")

        # 클릭
        page.click(selector, force=force)

        return ensure_response({
            'clicked': True,
            'selector': selector,
            'timeout': timeout
        })

    except Exception as e:
        return ensure_response(
            None,
            error=f"클릭 실패: {str(e)}",
            selector=selector
        )


@safe_execution
def handle_modal_by_class(page, modal_class: str, button_text: str, force: bool = True) -> Dict[str, Any]:
    """특정 클래스의 모달 내에서 버튼 클릭

    Args:
        page: Playwright page 객체
        modal_class: 모달의 클래스명
        button_text: 클릭할 버튼 텍스트
        force: 강제 클릭 여부

    Returns:
        표준 응답 형식
    """
    try:
        selector = f'.{modal_class} button:has-text("{button_text}")'

        if page.locator(selector).count() > 0:
            page.locator(selector).first.click(force=force)
            return ensure_response({
                'clicked': True,
                'modal_class': modal_class,
                'button_text': button_text
            })
        else:
            return ensure_response(
                None,
                error=f"모달 '{modal_class}'에서 버튼 '{button_text}'을(를) 찾을 수 없습니다"
            )

    except Exception as e:
        return ensure_response(
            None,
            error=f"모달 처리 실패: {str(e)}",
            exception=e
        )


# 편의 함수들 - 자주 사용하는 패턴
def close_popup(page) -> Dict[str, Any]:
    """팝업 닫기 (다양한 닫기 버튼 텍스트 시도)"""
    close_texts = ["닫기", "확인", "OK", "Close", "X", "×", "✕"]

    for text in close_texts:
        result = handle_popup(page, text)
        if result['ok']:
            return result

    return ensure_response(
        None,
        error="닫기 버튼을 찾을 수 없습니다"
    )


def confirm_popup(page) -> Dict[str, Any]:
    """확인 팝업 처리"""
    confirm_texts = ["확인", "예", "네", "OK", "Yes", "Confirm"]

    for text in confirm_texts:
        result = handle_popup(page, text)
        if result['ok']:
            return result

    return ensure_response(
        None,
        error="확인 버튼을 찾을 수 없습니다"
    )


def cancel_popup(page) -> Dict[str, Any]:
    """취소 팝업 처리"""
    cancel_texts = ["취소", "아니오", "아니요", "Cancel", "No"]

    for text in cancel_texts:
        result = handle_popup(page, text)
        if result['ok']:
            return result

    return ensure_response(
        None,
        error="취소 버튼을 찾을 수 없습니다"
    )
