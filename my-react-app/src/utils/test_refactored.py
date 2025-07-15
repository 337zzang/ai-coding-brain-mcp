import unittest
from refactored_code import process_user_data, calculate_total

class TestUserProcessing(unittest.TestCase):
    def setUp(self):
        self.test_users = [
            {'name': 'Alice', 'age': 25, 'status': 'active', 'subscription': 'premium', 'email': 'alice@test.com'},
            {'name': 'Bob', 'age': 17, 'status': 'active', 'subscription': 'basic', 'email': 'bob@test.com'},
            {'name': 'Charlie', 'age': 30, 'status': 'inactive', 'subscription': 'premium', 'email': 'charlie@test.com'},
            {'name': 'David', 'age': 22, 'status': 'active', 'subscription': 'basic', 'email': 'david@test.com'}
        ]

    def test_process_user_data(self):
        """성인 활성 사용자만 처리되는지 테스트"""
        result = process_user_data(self.test_users)

        # Alice와 David만 포함되어야 함
        self.assertEqual(len(result), 2)

        # 할인율 확인
        alice_record = next(r for r in result if r['name'] == 'Alice')
        self.assertEqual(alice_record['discount'], 0.2)

        david_record = next(r for r in result if r['name'] == 'David')
        self.assertEqual(david_record['discount'], 0.1)

    def test_calculate_total(self):
        """총액 계산 테스트"""
        items = [
            {'price': 100, 'discount': 0.2},
            {'price': 50, 'discount': 0.1}
        ]

        total = calculate_total(items)
        expected = 100 * 0.8 + 50 * 0.9  # 80 + 45 = 125

        self.assertEqual(total, expected)

if __name__ == '__main__':
    unittest.main()
