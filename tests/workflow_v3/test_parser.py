"""
Workflow v3 테스트 - 명령어 파서
"""
import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from python.workflow.v3.parser import CommandParser, ParsedCommand


class TestCommandParser(unittest.TestCase):
    """명령어 파서 테스트"""
    
    def setUp(self):
        self.parser = CommandParser()
        
    def test_basic_command_parsing(self):
        """기본 명령어 파싱 테스트"""
        # start 명령
        parsed = self.parser.parse("/start 새 프로젝트")
        self.assertEqual(parsed.command, "start")
        self.assertEqual(parsed.title, "새 프로젝트")
        
        # task 명령
        parsed = self.parser.parse("/task 데이터베이스 설계")
        self.assertEqual(parsed.command, "task")
        self.assertEqual(parsed.title, "데이터베이스 설계")
        
    def test_alias_parsing(self):
        """별칭 파싱 테스트"""
        # /t -> /task
        parsed = self.parser.parse("/t API 구현")
        self.assertEqual(parsed.command, "task")
        self.assertEqual(parsed.title, "API 구현")
        
        # /n -> /next
        parsed = self.parser.parse("/n 작업 완료")
        self.assertEqual(parsed.command, "next")
        self.assertEqual(parsed.title, "작업 완료")
        
    def test_legacy_command_mapping(self):
        """레거시 명령어 매핑 테스트"""
        # /done -> /next
        parsed = self.parser.parse("/done 완료 메모")
        self.assertEqual(parsed.command, "next")
        self.assertEqual(parsed.title, "완료 메모")
        
        # /history -> /status history
        parsed = self.parser.parse("/history")
        self.assertEqual(parsed.command, "status")
        self.assertEqual(parsed.subcommand, "history")
        
    def test_task_add_keyword_removal(self):
        """task add 키워드 제거 테스트"""
        # /task add 제목 -> 'add' 제거
        parsed = self.parser.parse("/task add 데이터베이스 설계")
        self.assertEqual(parsed.command, "task")
        self.assertEqual(parsed.title, "데이터베이스 설계")
        self.assertNotIn("add", parsed.title)
        
        # /task add만 입력한 경우
        with self.assertRaises(ValueError) as context:
            self.parser.parse("/task add")
        self.assertIn("태스크 제목을 입력해주세요", str(context.exception))
        
    def test_pipe_separation(self):
        """파이프로 제목과 설명 분리 테스트"""
        parsed = self.parser.parse("/plan 새 프로젝트 | 프로젝트 설명입니다")
        self.assertEqual(parsed.command, "plan")
        self.assertEqual(parsed.title, "새 프로젝트")
        self.assertEqual(parsed.description, "프로젝트 설명입니다")
        
    def test_subcommand_parsing(self):
        """서브커맨드 파싱 테스트"""
        # /plan list
        parsed = self.parser.parse("/plan list")
        self.assertEqual(parsed.command, "plan")
        self.assertEqual(parsed.subcommand, "list")
        
        # /status history
        parsed = self.parser.parse("/status history")
        self.assertEqual(parsed.command, "status")
        self.assertEqual(parsed.subcommand, "history")
        
        # /build review
        parsed = self.parser.parse("/build review")
        self.assertEqual(parsed.command, "build")
        self.assertEqual(parsed.subcommand, "review")
        
    def test_focus_number_parsing(self):
        """focus 명령어 숫자 파싱 테스트"""
        parsed = self.parser.parse("/focus 3")
        self.assertEqual(parsed.command, "focus")
        self.assertEqual(parsed.args['task_number'], 3)
        
        # ID로 focus
        parsed = self.parser.parse("/focus task-id-123")
        self.assertEqual(parsed.command, "focus")
        self.assertEqual(parsed.args['task_id'], "task-id-123")
        
    def test_input_validation(self):
        """입력 검증 테스트"""
        # 빈 명령어
        with self.assertRaises(ValueError):
            self.parser.parse("")
            
        # 슬래시 없는 명령어
        with self.assertRaises(ValueError):
            self.parser.parse("task 제목")
            
        # 알 수 없는 명령어
        with self.assertRaises(ValueError):
            self.parser.parse("/unknown")
            
    def test_title_validation(self):
        """제목 검증 테스트"""
        # 빈 플랜 이름
        with self.assertRaises(ValueError) as context:
            self.parser.parse("/plan")
            # subcommand가 없고 title도 없으면 에러
            
        # 빈 태스크 제목
        # /task만 입력하면 태스크 목록 조회이므로 에러 없음
        parsed = self.parser.parse("/task")
        self.assertEqual(parsed.command, "task")
        self.assertEqual(parsed.title, "")
        
    def test_special_characters(self):
        """특수 문자 처리 테스트"""
        # 파이프가 포함된 제목
        parsed = self.parser.parse("/task API 엔드포인트 구현 | GET /users/:id")
        self.assertEqual(parsed.title, "API 엔드포인트 구현")
        self.assertEqual(parsed.description, "GET /users/:id")
        
    def test_help_method(self):
        """도움말 메서드 테스트"""
        # 전체 도움말
        help_text = self.parser.get_help()
        self.assertIn("7개 핵심 명령어", help_text)
        
        # 특정 명령어 도움말
        help_text = self.parser.get_help("task")
        self.assertIn("새 태스크 추가", help_text)
        
    def test_extract_command(self):
        """명령어 추출 테스트"""
        # 텍스트에서 명령어 추출
        text = "작업 완료했습니다. /next 다음 작업 진행"
        cmd = CommandParser.extract_command(text)
        self.assertEqual(cmd, "/next 다음 작업 진행")
        
        # 명령어 없는 텍스트
        text = "일반 텍스트입니다"
        cmd = CommandParser.extract_command(text)
        self.assertIsNone(cmd)


if __name__ == '__main__':
    unittest.main()
