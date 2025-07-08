"""
Code Helper 리팩토링 테스트 스위트
특히 이중 래핑 문제 해결을 중점적으로 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ai_helpers.code import replace_block, insert_block, parse_code, parse_with_snippets
from helper_result import HelperResult
from helpers_wrapper import HelpersWrapper
import tempfile
import unittest


class TestDoubleWrapping(unittest.TestCase):
    """이중 래핑 문제 해결 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.test_file.write("""
def hello():
    return "world"
    
class TestClass:
    def method(self):
        pass
""")
        self.test_file.close()
        self.test_path = self.test_file.name
    
    def tearDown(self):
        """테스트 환경 정리"""
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)
    
    def test_no_double_wrapping_direct_call(self):
        """직접 함수 호출 시 HelperResult가 하나만 반환되는지 확인"""
        # 직접 호출
        result = replace_block(self.test_path, "hello", "def hello():\n    return 'modified'")
        
        # HelperResult인지 확인
        self.assertIsInstance(result, HelperResult)
        
        # data가 HelperResult가 아닌 일반 값인지 확인 (이중 래핑이 없음)
        if result.ok:
            self.assertIsInstance(result.data, str)
            self.assertIn("SUCCESS", result.data)
        else:
            self.assertIsInstance(result.error, str)
    
    def test_wrapper_single_wrapping(self):
        """HelpersWrapper를 통한 호출도 단일 래핑인지 확인"""
        # Mock AIHelpers 클래스
        class MockHelpers:
            replace_block = replace_block
            insert_block = insert_block
            parse_code = parse_code
            parse_with_snippets = parse_with_snippets
        
        # Wrapper 생성
        helpers = HelpersWrapper(MockHelpers())
        
        # Wrapper를 통한 호출
        result = helpers.replace_block(self.test_path, "hello", "def hello():\n    return 'wrapped'")
        
        # 결과 검증
        self.assertIsInstance(result, HelperResult)
        
        # 이중 래핑 검사 - data가 HelperResult가 아님
        self.assertNotIsInstance(result.data, HelperResult)
        
        if result.ok:
            self.assertIsInstance(result.data, str)
            self.assertIn("SUCCESS", result.data)
    
    def test_error_handling_single_wrap(self):
        """에러 발생 시에도 단일 래핑인지 확인"""
        helpers = HelpersWrapper(type('MockHelpers', (), {
            'replace_block': replace_block
        })())
        
        # 존재하지 않는 함수 교체 시도
        result = helpers.replace_block(self.test_path, "non_existent", "def new():\n    pass")
        
        # 에러가 제대로 처리되는지
        self.assertFalse(result.ok)
        self.assertIsNotNone(result.error)
        
        # 이중 래핑이 없는지
        self.assertNotIsInstance(result.data, HelperResult)
        self.assertNotIsInstance(result.error, HelperResult)


class TestParseWithSnippets(unittest.TestCase):
    """parse_with_snippets 구현 테스트"""
    
    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.test_file.write("""
import os
import sys

class Calculator:
    '''계산기 클래스'''
    
    def add(self, a, b):
        '''두 수를 더합니다'''
        return a + b
    
    def multiply(self, a, b):
        return a * b

def process_data(data):
    '''데이터를 처리합니다'''
    return [x * 2 for x in data]

async def async_operation():
    pass
""")
        self.test_file.close()
        self.test_path = self.test_file.name
    
    def tearDown(self):
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)
    
    def test_python_parsing(self):
        """Python 파일 파싱 테스트"""
        result = parse_with_snippets(self.test_path)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('parsing_success'))
        self.assertEqual(result.get('language'), 'python')
        
        # 함수 확인
        functions = result.get('functions', [])
        func_names = [f['name'] for f in functions]
        self.assertIn('process_data', func_names)
        self.assertIn('async_operation', func_names)
        
        # 클래스 확인
        classes = result.get('classes', [])
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]['name'], 'Calculator')
        
        # 메서드 확인
        methods = classes[0].get('methods', [])
        method_names = [m['name'] for m in methods]
        self.assertIn('add', method_names)
        self.assertIn('multiply', method_names)
        
        # imports 확인
        imports = result.get('imports', [])
        self.assertIn('os', imports)
        self.assertIn('sys', imports)
    
    def test_file_path_and_lines(self):
        """파일 경로와 라인 수가 포함되는지 테스트"""
        result = parse_with_snippets(self.test_path)
        
        self.assertEqual(result.get('file_path'), self.test_path)
        self.assertIsNotNone(result.get('total_lines'))
        self.assertGreater(result['total_lines'], 0)


class TestErrorHandling(unittest.TestCase):
    """에러 처리 개선 테스트"""
    
    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.test_file.write("def test():\n    pass\n")
        self.test_file.close()
        self.test_path = self.test_file.name
    
    def tearDown(self):
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)
    
    def test_error_returns_failure(self):
        """에러 발생 시 ok=False 반환 확인"""
        helpers = HelpersWrapper(type('MockHelpers', (), {
            'replace_block': replace_block,
            'insert_block': insert_block
        })())
        
        # 1. 존재하지 않는 타겟
        result = helpers.replace_block(self.test_path, "non_existent", "def new():\n    pass")
        self.assertFalse(result.ok)
        self.assertIn("찾을 수 없습니다", result.error)
        
        # 2. 잘못된 position
        result = helpers.insert_block(self.test_path, "test", "invalid", "pass")
        self.assertFalse(result.ok)
        self.assertIn("position", result.error)
        
        # 3. 구문 오류 코드
        result = helpers.replace_block(self.test_path, "test", "def test(\n    invalid")
        self.assertFalse(result.ok)
        self.assertIn("유효하지 않음", result.error)


class TestFunctionSignatures(unittest.TestCase):
    """함수 시그니처 변경 테스트"""
    
    def test_replace_block_simplified(self):
        """replace_block 시그니처 단순화 확인"""
        import inspect
        sig = inspect.signature(replace_block)
        params = list(sig.parameters.keys())
        
        # 필수 매개변수만 있는지 확인
        self.assertEqual(params, ['file_path', 'target_block', 'new_code'])
        
        # block_type, preserve_indent가 제거되었는지 확인
        self.assertNotIn('block_type', params)
        self.assertNotIn('preserve_indent', params)
    
    def test_insert_block_simplified(self):
        """insert_block 시그니처 단순화 확인"""
        import inspect
        sig = inspect.signature(insert_block)
        params = list(sig.parameters.keys())
        
        # 필수 매개변수만 있는지 확인
        self.assertEqual(params, ['file_path', 'target', 'position', 'new_code'])
        
        # target_type이 제거되었는지 확인
        self.assertNotIn('target_type', params)


def run_tests():
    """모든 테스트 실행"""
    # 테스트 스위트 생성
    suite = unittest.TestSuite()
    
    # 테스트 추가
    suite.addTest(unittest.makeSuite(TestDoubleWrapping))
    suite.addTest(unittest.makeSuite(TestParseWithSnippets))
    suite.addTest(unittest.makeSuite(TestErrorHandling))
    suite.addTest(unittest.makeSuite(TestFunctionSignatures))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
