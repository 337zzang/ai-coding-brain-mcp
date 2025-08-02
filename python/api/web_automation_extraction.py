"""
웹 자동화 고급 데이터 추출 모듈

AdvancedExtractionManager: 
- 배치 추출, 속성 추출, 폼 추출 등 고급 추출 기능 제공
- Playwright의 Locator API와 page.evaluate()를 전략적으로 활용
"""

from typing import Dict, List, Any, Optional, Union
import json
import re
from .web_automation_errors import safe_execute


class AdvancedExtractionManager:
    """고급 데이터 추출 기능 관리자"""

    def __init__(self, page):
        """
        Args:
            page: Playwright Page 객체
        """
        self.page = page

        # 타입 변환 함수들
        self.transformers = {
            'int': lambda x: int(re.sub(r'[^0-9-]', '', str(x))),
            'float': lambda x: float(re.sub(r'[^0-9.-]', '', str(x).h.replace(',', ''))),
            'bool': lambda x: str(x).lower() in ['true', '1', 'yes', 'on', 'checked'],
            'json': lambda x: json.loads(x) if x else {},
            'trim': lambda x: str(x).strip(),
            'lower': lambda x: str(x).lower(),
            'upper': lambda x: str(x).upper()
        }

    def extract_batch(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        여러 요소를 단일 호출로 추출 (최고 성능)

        Args:
            configs: 추출 설정 리스트
                [{
                    "selector": "CSS 선택자",
                    "name": "데이터 이름",
                    "type": "text|attr|...",  # 또는 "extract"
                    "attr": "속성명",  # type이 attr인 경우
                    "transform": "int|float|bool|json",  # 선택적
                    "default": "기본값"  # 선택적
                }]

        Returns:
            {'ok': true, 'data': {name: value, ...}}
        """
        # JavaScript 함수로 모든 데이터를 한번에 추출
        js_function = """
        (configs) => {
            const results = {};

            configs.forEach(config => {
                try {
                    const el = document.querySelector(config.selector);
                    if (!el) {
                        results[config.name] = config.default !== undefined ? config.default : null;
                        return;
                    }

                    let value;
                    const type = config.type || config.extract || 'text';

                    switch(type) {
                        case 'text':
                            value = el.innerText || el.textContent || '';
                            break;
                        case 'value':
                            value = el.value || '';
                            break;
                        case 'attr':
                        case 'attribute':
                            value = el.getAttribute(config.attr || config.attribute) || '';
                            break;
                        case 'href':
                            value = el.href || el.getAttribute('href') || '';
                            break;
                        case 'src':
                            value = el.src || el.getAttribute('src') || '';
                            break;
                        case 'html':
                            value = el.innerHTML || '';
                            break;
                        case 'data':
                            // data-* 속성들을 객체로 반환
                            value = Object.assign({}, el.dataset);
                            break;
                        case 'style':
                            value = el.style.cssText || '';
                            break;
                        case 'class':
                            value = el.className || '';
                            break;
                        case 'id':
                            value = el.id || '';
                            break;
                        default:
                            value = el.innerText || '';
                    }

                    results[config.name] = value;
                } catch (e) {
                    results[config.name] = config.default !== undefined ? config.default : null;
                }
            });

            return results;
        }
        """

        # 배치 추출 실행
        raw_results = self.page.evaluate(js_function, configs)

        # 타입 변환 적용
        final_results = {}
        for config in configs:
            name = config.get('name')
            if name in raw_results:
                value = raw_results[name]

                # transform 적용
                transform = config.get('transform')
                if transform and transform in self.transformers:
                    try:
                        value = self.transformers[transform](value)
                    except Exception:
                        # 변환 실패 시 원본 값 유지
                        pass

                final_results[name] = value

        return {'ok': true, 'data': final_results}

    def extract_attributes(self, selector: str, attributes: List[str]) -> Dict[str, Any]:
        """
        여러 속성을 한번에 추출 (Locator API 활용)

        Args:
            selector: CSS 선택자
            attributes: 추출할 속성 리스트

        Returns:
            {'ok': true, 'data': {attr: value, ...}}
        """
        try:
            locator = self.page.locator(selector).first

            # 요소 존재 확인
            if not locator.count():
                return {'ok': false, 'error': 'Element not found'}

            result = {}

            # 특수 속성 처리
            special_attrs = {
                'text': lambda: locator.text_content(),
                'value': lambda: locator.input_value(),
                'checked': lambda: locator.is_checked(),
                'visible': lambda: locator.is_visible(),
                'enabled': lambda: locator.is_enabled()
            }

            for attr in attributes:
                if attr in special_attrs:
                    result[attr] = special_attrs[attr]()
                else:
                    result[attr] = locator.get_attribute(attr)

            return {'ok': true, 'data': result}

        except Exception as e:
            return {'ok': false, 'error': str(e)}

    def extract_form(self, form_selector: str) -> Dict[str, Any]:
        """
        폼의 모든 입력 필드 자동 수집

        Args:
            form_selector: 폼 CSS 선택자

        Returns:
            {'ok': true, 'data': {field_name: value, ...}}
        """
        js_function = """
        (formSelector) => {
            const form = document.querySelector(formSelector);
            if (!form) return null;

            const data = {};

            // 모든 입력 요소 수집
            const inputs = form.querySelectorAll('input, select, textarea');

            inputs.forEach(input => {
                const name = input.name || input.id;
                if (!name) return;

                switch(input.type) {
                    case 'checkbox':
                        data[name] = input.checked;
                        break;
                    case 'radio':
                        if (input.checked) {
                            data[name] = input.value;
                        }
                        break;
                    case 'select-multiple':
                        const selected = [];
                        for (let option of input.selectedOptions) {
                            selected.push(option.value);
                        }
                        data[name] = selected;
                        break;
                    default:
                        data[name] = input.value;
                }
            });

            return data;
        }
        """

        form_data = self.page.evaluate(js_function, form_selector)

        if form_data is None:
            return {'ok': false, 'error': 'Form not found'}

        return {'ok': true, 'data': form_data}

    def _apply_transform(self, value: Any, transform: Optional[str]) -> Any:
        """타입 변환 적용"""
        if not transform or transform not in self.transformers:
            return value

        try:
            return self.transformers[transform](value)
        except Exception:
            return value  # 변환 실패 시 원본 반환
