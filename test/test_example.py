"""
예시 테스트 파일
테스트 작성 패턴을 보여줍니다.
"""
import pytest

def test_example_pass():
    """성공하는 테스트 예시"""
    assert 1 + 1 == 2

def test_example_with_fixture(sample_data):
    """fixture를 사용하는 테스트 예시"""
    assert sample_data["name"] == "test"
    assert sample_data["value"] == 123

@pytest.mark.skip(reason="아직 구현되지 않음")
def test_example_skip():
    """건너뛰는 테스트 예시"""
    assert False

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_example_parametrize(input, expected):
    """매개변수화된 테스트 예시"""
    assert input * 2 == expected
