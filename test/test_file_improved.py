"""
file_improved.py 테스트 코드
원자적 쓰기, 메모리 효율성, 성능 개선 검증
"""
import unittest
import tempfile
import os
import time
from pathlib import Path
import sys

# 테스트를 위한 경로 설정
test_dir = Path(__file__).parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root / 'python'))

# 이제 import
from ai_helpers_new import file_improved


class TestFileImproved(unittest.TestCase):
    """개선된 file.py 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = Path(tempfile.mkdtemp(prefix='test_file_'))
        self.test_file = self.test_dir / 'test.txt'

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_atomic_write(self):
        """원자적 쓰기 테스트"""
        # 정상 쓰기
        content = "Hello, World!"
        result = file_improved.write(self.test_file, content)
        self.assertTrue(result['ok'])
        self.assertEqual(result['data']['size'], len(content))

        # 파일 내용 확인
        self.assertTrue(self.test_file.exists())
        self.assertEqual(self.test_file.read_text(), content)

    def test_atomic_write_with_backup(self):
        """백업 포함 원자적 쓰기 테스트"""
        # 초기 파일 생성
        original = "Original content"
        file_improved.write(self.test_file, original)

        # 백업과 함께 덮어쓰기
        new_content = "New content"
        result = file_improved.write(self.test_file, new_content, backup=True)
        self.assertTrue(result['ok'])
        self.assertIsNotNone(result['data'].get('backup'))

        # 백업 파일 확인 (백업이 생성된 경우)
        if result['data'].get('backup'):
            backup_path = Path(result['data']['backup'])
            self.assertTrue(backup_path.exists())
            self.assertEqual(backup_path.read_text(), original)

    def test_efficient_read(self):
        """효율적인 부분 읽기 테스트"""
        # 테스트 데이터 생성
        lines = [f"Line {i}" for i in range(100)]
        content = '\n'.join(lines)
        file_improved.write(self.test_file, content)

        # 정방향 읽기 (offset >= 0)
        result = file_improved.read(self.test_file, offset=10, length=5)
        self.assertTrue(result['ok'])
        read_lines = result['data'].split('\n')
        self.assertEqual(len(read_lines), 5)
        self.assertEqual(read_lines[0], "Line 10")

        # 역방향 읽기 (offset < 0)
        result = file_improved.read(self.test_file, offset=-5)
        self.assertTrue(result['ok'])
        read_lines = result['data'].split('\n')
        self.assertEqual(len(read_lines), 5)
        self.assertEqual(read_lines[-1], "Line 99")

    def test_memory_efficient_info(self):
        """메모리 효율적인 info 테스트"""
        # 큰 파일 시뮬레이션 (실제로는 작게)
        lines = [f"Line {i}" * 100 for i in range(1000)]
        content = '\n'.join(lines)
        file_improved.write(self.test_file, content)

        # info 호출 (메모리 효율적으로 라인 카운트)
        result = file_improved.info(self.test_file)
        self.assertTrue(result['ok'])
        self.assertEqual(result['data']['lineCount'], 1000)
        self.assertTrue(result['data']['exists'])
        self.assertTrue(result['data']['is_file'])

    def test_structured_list_directory(self):
        """구조화된 디렉토리 목록 테스트"""
        # 테스트 파일들 생성
        (self.test_dir / 'file1.txt').write_text('content1')
        (self.test_dir / 'file2.txt').write_text('content2')
        (self.test_dir / 'subdir').mkdir()

        # 디렉토리 목록 조회
        result = file_improved.list_directory(self.test_dir)
        self.assertTrue(result['ok'])

        items = result['data']['items']
        self.assertEqual(len(items), 3)

        # 구조화된 데이터 확인
        for item in items:
            self.assertIn('name', item)
            self.assertIn('type', item)
            self.assertIn('size', item)
            self.assertIn('path', item)

    def test_json_operations(self):
        """JSON 읽기/쓰기 테스트"""
        json_file = self.test_dir / 'test.json'
        test_data = {
            'name': 'test',
            'value': 42,
            'items': ['a', 'b', 'c']
        }

        # JSON 쓰기
        result = file_improved.write_json(json_file, test_data)
        self.assertTrue(result['ok'])

        # JSON 읽기
        result = file_improved.read_json(json_file)
        self.assertTrue(result['ok'])
        self.assertEqual(result['data'], test_data)

    def test_append_atomic(self):
        """원자적 추가 테스트"""
        # 초기 내용
        file_improved.write(self.test_file, "Line 1")

        # 추가
        result = file_improved.append(self.test_file, "Line 2")
        self.assertTrue(result['ok'])

        # 내용 확인
        content = self.test_file.read_text()
        self.assertIn("Line 1", content)
        self.assertIn("Line 2", content)

    def test_error_handling(self):
        """에러 처리 테스트"""
        # 존재하지 않는 파일 읽기
        result = file_improved.read("nonexistent.txt")
        self.assertFalse(result['ok'])
        self.assertIn("not found", result['error'].lower())

        # 잘못된 JSON 읽기
        bad_json_file = self.test_dir / 'bad.json'
        bad_json_file.write_text("not a json")
        result = file_improved.read_json(bad_json_file)
        self.assertFalse(result['ok'])
        self.assertIn("json", result['error'].lower())


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
