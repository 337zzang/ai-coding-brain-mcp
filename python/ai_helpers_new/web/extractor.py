"""
웹 자동화 데이터 추출 모듈
페이지에서 다양한 형식의 데이터를 추출하는 기능 제공
"""

import logging
import json
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from .types import HelperResult, ExtractType
from .exceptions import ElementNotFoundError, ExtractorError
from .utils import (
    safe_execute, validate_selector, 
    get_alternative_selectors, parse_timeout
)
from .browser import get_browser_manager

logger = logging.getLogger(__name__)


class DataExtractor:
    """웹 페이지 데이터 추출 클래스"""

    def __init__(self):
        self.browser_manager = get_browser_manager()

    def _get_page(self, session_id: str):
        """페이지 객체 가져오기"""
        result = self.browser_manager.get_page(session_id)
        if not result.ok:
            raise ExtractorError(f"Cannot get page: {result.error}")
        return result.data

    @safe_execute
    def extract(
        self,
        session_id: str,
        selector: str,
        extract_type: Union[str, ExtractType] = ExtractType.TEXT,
        attribute: Optional[str] = None,
        multiple: bool = False,
        timeout: Optional[int] = None
    ) -> HelperResult:
        """
        데이터 추출 메인 메서드

        Args:
            session_id: 세션 ID
            selector: CSS 선택자
            extract_type: 추출 타입 (text, html, value, attribute)
            attribute: 속성명 (extract_type이 attribute일 때)
            multiple: 다중 요소 추출 여부
            timeout: 타임아웃 (밀리초)

        Returns:
            HelperResult with extracted data
        """
        if not validate_selector(selector):
            return HelperResult.failure(f"Invalid selector: {selector}")

        # ExtractType enum 변환
        if isinstance(extract_type, str):
            try:
                extract_type = ExtractType(extract_type)
            except ValueError:
                extract_type = ExtractType.TEXT

        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            # 요소 대기
            page.wait_for_selector(selector, timeout=timeout)

            if multiple:
                # 다중 요소 추출
                elements = page.query_selector_all(selector)
                if not elements:
                    return HelperResult.success([])

                results = []
                for element in elements:
                    data = self._extract_from_element(
                        page, element, extract_type, attribute
                    )
                    if data is not None:
                        results.append(data)

                return HelperResult.success(results)
            else:
                # 단일 요소 추출
                element = page.query_selector(selector)
                if not element:
                    raise ElementNotFoundError(selector)

                data = self._extract_from_element(
                    page, element, extract_type, attribute
                )
                return HelperResult.success(data)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return HelperResult.failure(str(e))

    def _extract_from_element(
        self,
        page,
        element,
        extract_type: ExtractType,
        attribute: Optional[str] = None
    ) -> Any:
        """요소에서 데이터 추출"""
        if extract_type == ExtractType.TEXT:
            return element.text_content()
        elif extract_type == ExtractType.HTML:
            return element.inner_html()
        elif extract_type == ExtractType.VALUE:
            return element.input_value() if hasattr(element, 'input_value') else None
        elif extract_type == ExtractType.ATTRIBUTE:
            if attribute:
                return element.get_attribute(attribute)
            return None
        else:
            return element.text_content()

    @safe_execute
    def extract_table(
        self,
        session_id: str,
        selector: str,
        headers: bool = True,
        timeout: Optional[int] = None
    ) -> HelperResult:
        """
        테이블 데이터 추출

        Args:
            session_id: 세션 ID
            selector: 테이블 선택자
            headers: 헤더 포함 여부
            timeout: 타임아웃

        Returns:
            HelperResult with table data as list of dicts
        """
        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            # 테이블 요소 찾기
            page.wait_for_selector(selector, timeout=timeout)

            # JavaScript로 테이블 파싱
            table_data = page.evaluate(f"""
                (() => {{
                    const table = document.querySelector('{selector}');
                    if (!table) return null;

                    const data = [];
                    const rows = table.querySelectorAll('tr');
                    let headers = [];

                    // 헤더 추출
                    if ({str(headers).lower()}) {{
                        const headerRow = rows[0];
                        if (headerRow) {{
                            headers = Array.from(
                                headerRow.querySelectorAll('th, td')
                            ).map(cell => cell.textContent.trim());
                        }}
                    }}

                    // 데이터 행 추출
                    const startIdx = headers.length > 0 ? 1 : 0;
                    for (let i = startIdx; i < rows.length; i++) {{
                        const cells = rows[i].querySelectorAll('td');
                        if (cells.length === 0) continue;

                        if (headers.length > 0) {{
                            const rowData = {{}};
                            cells.forEach((cell, idx) => {{
                                const key = headers[idx] || `col_${{idx}}`;
                                rowData[key] = cell.textContent.trim();
                            }});
                            data.push(rowData);
                        }} else {{
                            const rowData = Array.from(cells).map(
                                cell => cell.textContent.trim()
                            );
                            data.push(rowData);
                        }}
                    }}

                    return data;
                }})();
            """)

            return HelperResult.success(table_data)

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def extract_links(
        self,
        session_id: str,
        selector: Optional[str] = "a[href]",
        absolute: bool = True,
        timeout: Optional[int] = None
    ) -> HelperResult:
        """
        링크 추출

        Args:
            session_id: 세션 ID
            selector: 링크 선택자
            absolute: 절대 경로 변환 여부
            timeout: 타임아웃

        Returns:
            HelperResult with list of links
        """
        page = self._get_page(session_id)

        try:
            links = page.evaluate(f"""
                Array.from(document.querySelectorAll('{selector}')).map(a => ({{
                    text: a.textContent.trim(),
                    href: {str(absolute).lower()} ? a.href : a.getAttribute('href'),
                    title: a.title || null,
                    target: a.target || null
                }}))
            """)

            return HelperResult.success(links)

        except Exception as e:
            logger.error(f"Link extraction failed: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def extract_images(
        self,
        session_id: str,
        selector: Optional[str] = "img",
        include_data_urls: bool = False
    ) -> HelperResult:
        """
        이미지 정보 추출

        Args:
            session_id: 세션 ID
            selector: 이미지 선택자
            include_data_urls: data URL 포함 여부

        Returns:
            HelperResult with list of image info
        """
        page = self._get_page(session_id)

        try:
            images = page.evaluate(f"""
                Array.from(document.querySelectorAll('{selector}')).map(img => {{
                    const src = img.src;
                    const includeData = {str(include_data_urls).lower()};

                    if (!includeData && src.startsWith('data:')) {{
                        return null;
                    }}

                    return {{
                        src: src,
                        alt: img.alt || null,
                        title: img.title || null,
                        width: img.naturalWidth,
                        height: img.naturalHeight,
                        loading: img.loading || 'auto'
                    }};
                }}).filter(img => img !== null)
            """)

            return HelperResult.success(images)

        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def extract_form_data(
        self,
        session_id: str,
        form_selector: str
    ) -> HelperResult:
        """
        폼 데이터 추출

        Args:
            session_id: 세션 ID
            form_selector: 폼 선택자

        Returns:
            HelperResult with form data
        """
        page = self._get_page(session_id)

        try:
            form_data = page.evaluate(f"""
                (() => {{
                    const form = document.querySelector('{form_selector}');
                    if (!form) return null;

                    const data = {{}};
                    const inputs = form.querySelectorAll('input, select, textarea');

                    inputs.forEach(input => {{
                        const name = input.name || input.id;
                        if (!name) return;

                        if (input.type === 'checkbox') {{
                            data[name] = input.checked;
                        }} else if (input.type === 'radio') {{
                            if (input.checked) {{
                                data[name] = input.value;
                            }}
                        }} else {{
                            data[name] = input.value;
                        }}
                    }});

                    return {{
                        action: form.action || null,
                        method: form.method || 'GET',
                        data: data
                    }};
                }})();
            """)

            return HelperResult.success(form_data)

        except Exception as e:
            logger.error(f"Form extraction failed: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def extract_metadata(
        self,
        session_id: str
    ) -> HelperResult:
        """
        페이지 메타데이터 추출

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult with metadata
        """
        page = self._get_page(session_id)

        try:
            metadata = page.evaluate("""
                (() => {
                    const meta = {};

                    // 기본 메타 태그
                    document.querySelectorAll('meta').forEach(tag => {
                        const name = tag.name || tag.getAttribute('property');
                        const content = tag.content;
                        if (name && content) {
                            meta[name] = content;
                        }
                    });

                    // Open Graph 태그
                    const og = {};
                    document.querySelectorAll('meta[property^="og:"]').forEach(tag => {
                        const property = tag.getAttribute('property').replace('og:', '');
                        og[property] = tag.content;
                    });

                    // 기본 정보
                    return {
                        title: document.title,
                        url: window.location.href,
                        description: meta.description || null,
                        keywords: meta.keywords || null,
                        author: meta.author || null,
                        viewport: meta.viewport || null,
                        charset: document.characterSet,
                        language: document.documentElement.lang || null,
                        openGraph: og,
                        meta: meta
                    };
                })();
            """)

            return HelperResult.success(metadata)

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return HelperResult.failure(str(e))


# 전역 추출기 인스턴스
_data_extractor: Optional[DataExtractor] = None


def get_data_extractor() -> DataExtractor:
    """전역 데이터 추출기 인스턴스 반환"""
    global _data_extractor
    if _data_extractor is None:
        _data_extractor = DataExtractor()
    return _data_extractor
