"""
데이터 추출 기능 기본 테스트

주요 테스트:
- extract_batch: 배치 추출 기능
- extract_attributes: 속성 추출 기능
- extract_form: 폼 데이터 추출
- 타입 변환 시스템
"""

import pytest
from unittest.mock import Mock, MagicMock
from web_automation_extraction import AdvancedExtractionManager


class TestAdvancedExtractionManager:
    """AdvancedExtractionManager 단위 테스트"""

    @pytest.fixture
    def mock_page(self):
        """Mock Playwright Page 객체"""
        page = Mock()
        page.evaluate = MagicMock()
        page.locator = MagicMock()
        return page

    @pytest.fixture
    def manager(self, mock_page):
        """테스트용 AdvancedExtractionManager 인스턴스"""
        return AdvancedExtractionManager(mock_page)

    def test_extract_batch_basic(self, manager, mock_page):
        """배치 추출 기본 테스트"""
        # Mock 설정
        mock_page.evaluate.return_value = {
            'title': 'Test Product',
            'price': '29.99',
            'stock': '10'
        }

        # 테스트 실행
        configs = [
            {"selector": "h1", "name": "title", "type": "text"},
            {"selector": ".price", "name": "price", "type": "text", "transform": "float"},
            {"selector": ".stock", "name": "stock", "type": "text", "transform": "int"}
        ]

        result = manager.extract_batch(configs)

        # 검증
        assert result['ok'] is True
        assert result['data']['title'] == 'Test Product'
        assert result['data']['price'] == 29.99  # float 변환 확인
        assert result['data']['stock'] == 10  # int 변환 확인

        # evaluate 호출 확인
        mock_page.evaluate.assert_called_once()

    def test_extract_batch_with_default(self, manager, mock_page):
        """기본값 처리 테스트"""
        mock_page.evaluate.return_value = {
            'title': 'Test',
            'description': None  # 요소를 찾지 못한 경우
        }

        configs = [
            {"selector": "h1", "name": "title", "type": "text"},
            {"selector": ".desc", "name": "description", "type": "text", "default": "No description"}
        ]

        result = manager.extract_batch(configs)

        assert result['ok'] is True
        assert result['data']['description'] == "No description"

    def test_extract_attributes(self, manager, mock_page):
        """속성 추출 테스트"""
        # Mock 설정
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        mock_locator.text_content.return_value = "Product Title"
        mock_locator.get_attribute.side_effect = lambda attr: {
            'id': 'prod-123',
            'data-price': '29.99',
            'data-sku': 'ABC123'
        }.get(attr)

        mock_page.locator.return_value.first = mock_locator

        # 테스트 실행
        result = manager.extract_attributes(
            ".product",
            ["text", "id", "data-price", "data-sku"]
        )

        # 검증
        assert result['ok'] is True
        assert result['data']['text'] == "Product Title"
        assert result['data']['id'] == 'prod-123'
        assert result['data']['data-price'] == '29.99'
        assert result['data']['data-sku'] == 'ABC123'

    def test_extract_attributes_not_found(self, manager, mock_page):
        """요소를 찾지 못한 경우 테스트"""
        mock_locator = Mock()
        mock_locator.count.return_value = 0
        mock_page.locator.return_value.first = mock_locator

        result = manager.extract_attributes(".missing", ["id"])

        assert result['ok'] is False
        assert 'error' in result

    def test_extract_form(self, manager, mock_page):
        """폼 데이터 추출 테스트"""
        # Mock 설정
        mock_page.evaluate.return_value = {
            'username': 'testuser',
            'password': 'secret',
            'remember': True,
            'country': 'US'
        }

        # 테스트 실행
        result = manager.extract_form("#login-form")

        # 검증
        assert result['ok'] is True
        assert result['data']['username'] == 'testuser'
        assert result['data']['password'] == 'secret'
        assert result['data']['remember'] is True
        assert result['data']['country'] == 'US'

    def test_extract_form_not_found(self, manager, mock_page):
        """폼을 찾지 못한 경우 테스트"""
        mock_page.evaluate.return_value = None

        result = manager.extract_form("#missing-form")

        assert result['ok'] is False
        assert result['error'] == 'Form not found'

    def test_transformers(self, manager):
        """타입 변환 함수 테스트"""
        # int 변환
        assert manager.transformers['int']('123') == 123
        assert manager.transformers['int']('$1,234') == 1234
        assert manager.transformers['int']('-99') == -99

        # float 변환
        assert manager.transformers['float']('29.99') == 29.99
        assert manager.transformers['float']('$1,234.56') == 1234.56

        # bool 변환
        assert manager.transformers['bool']('true') is True
        assert manager.transformers['bool']('1') is True
        assert manager.transformers['bool']('yes') is True
        assert manager.transformers['bool']('false') is False
        assert manager.transformers['bool']('0') is False

        # string 변환
        assert manager.transformers['trim']('  hello  ') == 'hello'
        assert manager.transformers['lower']('HELLO') == 'hello'
        assert manager.transformers['upper']('hello') == 'HELLO'

    def test_extract_batch_all_types(self, manager, mock_page):
        """모든 추출 타입 테스트"""
        mock_page.evaluate.return_value = {
            'text': 'Sample Text',
            'value': 'input-value',
            'href': 'https://example.com',
            'src': '/image.jpg',
            'html': '<strong>Bold</strong>',
            'data': {'id': '123', 'price': '29.99'},
            'style': 'color: red; font-size: 14px;',
            'class': 'product-item active',
            'id': 'prod-123'
        }

        configs = [
            {"selector": ".text", "name": "text", "type": "text"},
            {"selector": "input", "name": "value", "type": "value"},
            {"selector": "a", "name": "href", "type": "href"},
            {"selector": "img", "name": "src", "type": "src"},
            {"selector": ".content", "name": "html", "type": "html"},
            {"selector": ".product", "name": "data", "type": "data"},
            {"selector": ".styled", "name": "style", "type": "style"},
            {"selector": ".item", "name": "class", "type": "class"},
            {"selector": "#prod", "name": "id", "type": "id"}
        ]

        result = manager.extract_batch(configs)

        assert result['ok'] is True
        assert result['data']['text'] == 'Sample Text'
        assert result['data']['value'] == 'input-value'
        assert result['data']['href'] == 'https://example.com'
        assert result['data']['src'] == '/image.jpg'
        assert result['data']['html'] == '<strong>Bold</strong>'
        assert result['data']['data'] == {'id': '123', 'price': '29.99'}
        assert 'color: red' in result['data']['style']
        assert 'active' in result['data']['class']
        assert result['data']['id'] == 'prod-123'


# 통합 테스트를 위한 간단한 예제
def test_integration_example():
    """통합 테스트 예제 (실제 브라우저 필요)"""
    # 이 테스트는 실제 Playwright 환경에서만 실행
    # pytest.skip("Integration test - requires real browser")
    pass
