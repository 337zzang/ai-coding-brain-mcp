
"""
들여쓰기 오류 처리 시스템 테스트
"""
import unittest
import sys
import os

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.indentation_preprocessor import IndentationPreprocessor
from core.indentation_error_handler import IndentationErrorHandler
from core.indentation_auto_fixer import IndentationAutoFixer

class TestIndentationErrorHandling(unittest.TestCase):
    """들여쓰기 오류 처리 테스트"""
    
    def setUp(self):
        self.preprocessor = IndentationPreprocessor()
        self.error_handler = IndentationErrorHandler()
        self.auto_fixer = IndentationAutoFixer()
    
    def test_missing_indent_after_colon(self):
        """콜론 뒤 들여쓰기 누락 테스트"""
        code = """def test():
print("hello")"""
        
        # 전처리기 테스트
        fixed_code, modified = self.preprocessor.preprocess(code)
        self.assertTrue(modified)
        
        # 수정된 코드가 실행 가능한지 확인
        try:
            compile(fixed_code, '<test>', 'exec')
            success = True
        except IndentationError:
            success = False
        
        self.assertTrue(success, "전처리 후에도 들여쓰기 오류 발생")
    
    def test_unexpected_indent(self):
        """불필요한 들여쓰기 테스트"""
        code = """x = 1
    y = 2"""
        
        fixed_code, modified = self.preprocessor.preprocess(code)
        self.assertTrue(modified)
        self.assertNotIn("    y", fixed_code)
    
    def test_unindent_mismatch(self):
        """들여쓰기 불일치 테스트"""
        code = """if True:
    x = 1
  y = 2"""  # 2칸 들여쓰기 (불일치)
        
        try:
            fixed_code, modified = self.preprocessor.preprocess(code)
            self.assertTrue(modified)
        except IndentationError as e:
            # 오류 핸들러 테스트
            error_info = self.error_handler.handle_error(code, e)
            self.assertIsNotNone(error_info['auto_fix'])
    
    def test_mixed_tabs_spaces(self):
        """탭과 스페이스 혼용 테스트"""
        code = "def test():\n\tx = 1\n    y = 2"  # 탭과 스페이스 혼용
        
        fixed_code, modified = self.preprocessor.preprocess(code)
        self.assertTrue(modified)
        self.assertNotIn('\t', fixed_code)
    
    def test_empty_block_with_pass(self):
        """빈 블록에 pass 추가 테스트"""
        code = """def empty():
"""
        
        fixed_code, modified = self.preprocessor.preprocess(code)
        self.assertTrue(modified)
        self.assertIn('pass', fixed_code)
    
    def test_nested_indentation(self):
        """중첩된 들여쓰기 테스트"""
        code = """class Test:
def method(self):
if True:
print("nested")"""
        
        try:
            fixed_code, modified = self.preprocessor.preprocess(code)
            # 각 레벨이 올바르게 들여쓰기 되었는지 확인
            lines = fixed_code.split('\n')
            self.assertTrue(lines[1].startswith('    '))  # method
            self.assertTrue(lines[2].startswith('        '))  # if
            self.assertTrue(lines[3].startswith('            '))  # print
        except IndentationError:
            self.fail("중첩 들여쓰기 처리 실패")
    
    def test_auto_fixer_suggestion(self):
        """자동 수정 제안 테스트"""
        code = """def test():
print("hello")"""
        
        try:
            compile(code, '<test>', 'exec')
        except IndentationError as e:
            error_info = self.error_handler.handle_error(code, e)
            suggestion = self.auto_fixer.suggest_fix(code, error_info)
            
            self.assertTrue(suggestion['has_fix'])
            self.assertGreater(suggestion['confidence'], 0.9)
            self.assertIsNotNone(suggestion['fixed_code'])
    
    def test_detect_indent_style(self):
        """들여쓰기 스타일 감지 테스트"""
        # 2칸 들여쓰기
        code_2_spaces = """def test():
  x = 1
  if True:
    y = 2"""
        
        indent_size = self.preprocessor.detect_indent_style(code_2_spaces)
        self.assertEqual(indent_size, 2)
        
        # 4칸 들여쓰기
        code_4_spaces = """def test():
    x = 1
    if True:
        y = 2"""
        
        indent_size = self.preprocessor.detect_indent_style(code_4_spaces)
        self.assertEqual(indent_size, 4)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def test_full_pipeline(self):
        """전체 파이프라인 테스트"""
        problematic_codes = [
            # 케이스 1: 기본 들여쓰기 오류
            """def hello():
print("world")""",
            
            # 케이스 2: 클래스 메서드
            """class MyClass:
def method(self):
return True""",
            
            # 케이스 3: 조건문
            """if x > 0:
result = "positive"
else:
result = "negative"""",
            
            # 케이스 4: 반복문
            """for i in range(10):
print(i)
if i > 5:
break"""
        ]
        
        preprocessor = IndentationPreprocessor()
        success_count = 0
        
        for i, code in enumerate(problematic_codes):
            try:
                fixed_code, modified = preprocessor.preprocess(code)
                compile(fixed_code, f'<test{i}>', 'exec')
                success_count += 1
            except Exception as e:
                print(f"케이스 {i+1} 실패: {e}")
        
        # 90% 이상 성공해야 함
        success_rate = success_count / len(problematic_codes)
        self.assertGreaterEqual(success_rate, 0.9)


if __name__ == '__main__':
    unittest.main()
