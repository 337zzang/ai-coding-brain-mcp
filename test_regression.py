"""
회귀 테스트 및 엣지 케이스 테스트
기존 동작을 보장하고 극한 상황에서의 동작을 검증
"""
import pytest
import sys
import gc
from test_sample import calculate_factorial, find_duplicates, DataProcessor


class TestRegressionFactorial:
    """팩토리얼 함수 회귀 테스트"""
    
    def test_factorial_baseline_results(self):
        """기준 결과 회귀 테스트 - 이 값들은 변경되어서는 안됨"""
        baseline_results = {
            0: 1,
            1: 1,
            2: 2,
            3: 6,
            4: 24,
            5: 120,
            6: 720,
            7: 5040,
            8: 40320,
            9: 362880,
            10: 3628800,
        }
        
        for input_val, expected in baseline_results.items():
            result = calculate_factorial(input_val)
            assert result == expected, f"Regression: factorial({input_val}) should be {expected}, got {result}"
    
    def test_factorial_negative_values_regression(self):
        """음수 처리 회귀 테스트"""
        negative_inputs = [-1, -5, -10, -100]
        for n in negative_inputs:
            result = calculate_factorial(n)
            assert result is None, f"Regression: factorial({n}) should return None, got {result}"
    
    def test_factorial_consistency(self):
        """일관성 테스트 - 같은 입력에 대해 항상 같은 결과"""
        test_values = [0, 1, 5, 10]
        for val in test_values:
            results = [calculate_factorial(val) for _ in range(10)]
            assert all(r == results[0] for r in results), f"Inconsistent results for factorial({val})"


class TestRegressionFindDuplicates:
    """중복 찾기 함수 회귀 테스트"""
    
    def test_find_duplicates_baseline_cases(self):
        """기준 케이스 회귀 테스트"""
        test_cases = [
            ([], []),
            ([1], []),
            ([1, 1], [1]),
            ([1, 2, 1], [1]),
            ([1, 2, 3, 2, 1], [1, 2]),
            ([1, 1, 2, 2, 3, 3], [1, 2, 3]),
        ]
        
        for input_data, expected in test_cases:
            result = find_duplicates(input_data.copy())  # copy to avoid modification
            assert result == expected, f"Regression: find_duplicates({input_data}) should be {expected}, got {result}"
    
    def test_find_duplicates_order_preservation(self):
        """순서 보존 회귀 테스트"""
        # 현재 구현에서는 발견 순서대로 반환해야 함
        test_data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
        result = find_duplicates(test_data)
        expected = [3, 1, 5]  # 발견 순서
        assert result == expected, f"Order regression: expected {expected}, got {result}"
    
    def test_find_duplicates_data_integrity(self):
        """원본 데이터 무결성 테스트"""
        original_data = [1, 2, 3, 2, 4, 3, 5]
        data_copy = original_data.copy()
        
        find_duplicates(data_copy)
        
        assert data_copy == original_data, "Function should not modify input data"


class TestRegressionDataProcessor:
    """데이터 프로세서 클래스 회귀 테스트"""
    
    def test_data_processor_baseline_behavior(self):
        """기준 동작 회귀 테스트"""
        processor = DataProcessor()
        
        # 기본 상태 확인
        assert len(processor.data) == 0
        assert processor.process_all() == []
        
        # 데이터 추가 후
        processor.add_data("  TEST  ")
        assert len(processor.data) == 1
        assert processor.process_all() == ["test"]
        
        # 데이터가 누적됨을 확인
        processor.add_data("  ANOTHER  ")
        assert len(processor.data) == 2
        result = processor.process_all()
        assert result == ["test", "another"]
    
    def test_data_processor_string_processing_regression(self):
        """문자열 처리 로직 회귀 테스트"""
        test_cases = [
            ("  HELLO  ", "hello"),
            ("world", "world"),
            ("  MiXeD CaSe  ", "mixed case"),
            ("123", "123"),
            ("", ""),
            ("   ", ""),
        ]
        
        processor = DataProcessor()
        for input_str, expected in test_cases:
            processor.add_data(input_str)
        
        results = processor.process_all()
        expected_results = [expected for _, expected in test_cases]
        
        assert results == expected_results, f"String processing regression: expected {expected_results}, got {results}"


class TestEdgeCases:
    """극한 상황 및 엣지 케이스 테스트"""
    
    def test_factorial_large_numbers(self):
        """큰 수에 대한 팩토리얼 테스트"""
        # Python은 임의 정밀도 정수를 지원하므로 매우 큰 결과도 가능
        result_50 = calculate_factorial(50)
        assert isinstance(result_50, int)
        assert result_50 > 0
        
        # 50!은 특정 값이어야 함
        expected_50_factorial = 30414093201713378043612608166064768844377641568960512000000000000
        assert result_50 == expected_50_factorial
    
    def test_factorial_recursion_depth(self):
        """재귀 깊이 제한 테스트"""
        # 현재 재귀 제한 확인
        original_limit = sys.getrecursionlimit()
        
        try:
            # 제한을 낮춰서 테스트
            sys.setrecursionlimit(100)
            
            with pytest.raises(RecursionError):
                calculate_factorial(150)
        finally:
            # 원래 제한 복원
            sys.setrecursionlimit(original_limit)
    
    def test_find_duplicates_extreme_cases(self):
        """중복 찾기 극한 케이스"""
        # 매우 큰 배열 (메모리 제한 내에서)
        large_array = list(range(5000)) + list(range(2500))
        result = find_duplicates(large_array)
        assert len(result) == 2500
        assert all(isinstance(x, int) for x in result)
        
        # 모든 요소가 동일한 경우
        all_same = [42] * 1000
        result = find_duplicates(all_same)
        assert result == [42]
        
        # 매우 긴 문자열들
        long_strings = ["a" * 1000, "b" * 1000, "a" * 1000]
        result = find_duplicates(long_strings)
        assert len(result) == 1
        assert result[0] == "a" * 1000
    
    def test_data_processor_extreme_cases(self):
        """데이터 프로세서 극한 케이스"""
        processor = DataProcessor()
        
        # 매우 긴 문자열
        very_long_string = "  " + "X" * 10000 + "  "
        processor.add_data(very_long_string)
        result = processor.process_all()
        assert len(result) == 1
        assert result[0] == "x" * 10000
        
        # 특수 문자들
        special_chars = "  !@#$%^&*()_+{}|:<>?[]\\;'\",./ "
        processor.data.clear()  # 이전 데이터 지움
        processor.add_data(special_chars)
        result = processor.process_all()
        expected = special_chars.strip().lower()
        assert result[0] == expected
        
        # Unicode 문자들
        unicode_str = "  한글 테스트 🚀 émojis  "
        processor.data.clear()
        processor.add_data(unicode_str)
        result = processor.process_all()
        assert "한글" in result[0]
        assert "🚀" in result[0]
    
    def test_memory_extreme_cases(self):
        """메모리 극한 상황 테스트"""
        processor = DataProcessor()
        
        # 메모리 사용량 모니터링
        initial_objects = len(gc.get_objects())
        
        # 대량 데이터 추가
        for i in range(100000):
            processor.add_data(f"item_{i}")
        
        # 처리
        results = processor.process_all()
        
        # 검증
        assert len(results) == 100000
        assert len(processor.data) == 100000  # 원본 데이터가 여전히 남아있음 (메모리 누수)
        
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # 객체 수가 증가했는지 확인 (메모리 누수 징후)
        assert object_growth > 0, f"Expected some object growth (indicating memory usage), got {object_growth}"
    
    def test_type_edge_cases(self):
        """타입 관련 엣지 케이스"""
        # 팩토리얼에 float 전달 (현재는 에러 처리 없음)
        try:
            result = calculate_factorial(5.0)  # float이지만 정수값
            assert result == 120  # 작동할 수 있음
        except (TypeError, RecursionError):
            pass  # 에러도 허용
        
        # find_duplicates에 다양한 타입
        mixed_types = [1, 1.0, "1", True, None, None]
        result = find_duplicates(mixed_types)
        # Python에서 1 == 1.0 == True이므로 복잡한 중복 패턴
        assert None in result  # None은 중복됨
        
        # DataProcessor에 다양한 타입
        processor = DataProcessor()
        weird_types = [None, [], {}, set(), lambda x: x]
        for item in weird_types:
            processor.add_data(item)
        
        results = processor.process_all()
        assert len(results) == len(weird_types)
        assert all(isinstance(r, str) for r in results)


class TestConcurrency:
    """동시성 및 상태 관리 테스트"""
    
    def test_multiple_processors_independence(self):
        """여러 프로세서 인스턴스 독립성 확인"""
        processors = [DataProcessor() for _ in range(10)]
        
        # 각각에 다른 데이터 추가
        for i, processor in enumerate(processors):
            processor.add_data(f"processor_{i}_data")
        
        # 독립성 확인
        for i, processor in enumerate(processors):
            assert len(processor.data) == 1
            assert processor.data[0] == f"processor_{i}_data"
            result = processor.process_all()
            assert result == [f"processor_{i}_data"]
    
    def test_processor_state_persistence(self):
        """프로세서 상태 지속성 테스트"""
        processor = DataProcessor()
        
        # 단계적 데이터 추가
        for i in range(5):
            processor.add_data(f"step_{i}")
            intermediate_result = processor.process_all()
            assert len(intermediate_result) == i + 1
            assert intermediate_result[-1] == f"step_{i}"


if __name__ == "__main__":
    # 회귀 테스트 실행
    pytest.main([__file__, "-v", "--tb=short"])