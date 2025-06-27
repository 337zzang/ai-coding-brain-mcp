#!/usr/bin/env python
"""
AI Coding Brain MCP 통합 테스트 스크립트
프로젝트의 주요 기능들을 테스트합니다.
"""

import os
import sys
import json
from pathlib import Path

# Python 경로 설정
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def test_imports():
    """모듈 import 테스트"""
    print("🧪 모듈 Import 테스트...")
    
    try:
        # Core 모듈들
        from core.context_manager import get_context_manager
        print("✅ core.context_manager 임포트 성공")
        
        from core.models import ProjectContext, TaskStatus
        print("✅ core.models 임포트 성공")
        
        # 메인 모듈
        from claude_code_ai_brain import cmd_flow, initialize_context
        print("✅ claude_code_ai_brain 임포트 성공")
        
        # Wisdom 모듈
        from project_wisdom import get_wisdom_manager
        print("✅ project_wisdom 임포트 성공")
        
        from wisdom_hooks import get_wisdom_hooks
        print("✅ wisdom_hooks 임포트 성공")
        
        # Git 모듈
        from git_version_manager import GitVersionManager
        print("✅ git_version_manager 임포트 성공")
        
        return True
    except Exception as e:
        print(f"❌ Import 오류: {e}")
        return False

def test_context_manager():
    """컨텍스트 매니저 테스트"""
    print("\n🧪 컨텍스트 매니저 테스트...")
    
    try:
        from core.context_manager import get_context_manager
        
        # 컨텍스트 매니저 초기화
        cm = get_context_manager()
        print("✅ 컨텍스트 매니저 초기화 성공")
        
        # 프로젝트 설정
        cm.set_project("test-project", create_if_not_exists=True)
        print(f"✅ 프로젝트 설정: {cm.context.project_name}")
        
        # 컨텍스트 정보
        context_info = cm.get_context()
        print(f"✅ 컨텍스트 정보: 프로젝트={context_info.get('project_name')}")
        
        return True
    except Exception as e:
        print(f"❌ 컨텍스트 매니저 오류: {e}")
        return False

def test_wisdom_system():
    """Wisdom 시스템 테스트"""
    print("\n🧪 Wisdom 시스템 테스트...")
    
    try:
        from project_wisdom import get_wisdom_manager
        from wisdom_hooks import get_wisdom_hooks
        
        # Wisdom 매니저 초기화
        wisdom = get_wisdom_manager()
        print("✅ Wisdom 매니저 초기화 성공")
        
        # 통계 확인
        stats = wisdom.get_statistics()
        print(f"✅ Wisdom 통계: 실수={stats['total_mistakes']}, 오류={stats['total_errors']}")
        
        # Hooks 초기화
        hooks = get_wisdom_hooks()
        print("✅ Wisdom Hooks 초기화 성공")
        
        # 패턴 감지 테스트
        test_code = 'console.log("test")'
        detections = hooks.check_code_patterns(test_code, "test.js")
        print(f"✅ 패턴 감지 테스트: {len(detections)} 패턴 발견")
        
        return True
    except Exception as e:
        print(f"❌ Wisdom 시스템 오류: {e}")
        return False

def test_git_manager():
    """Git 버전 관리자 테스트"""
    print("\n🧪 Git 버전 관리자 테스트...")
    
    try:
        from git_version_manager import GitVersionManager
        
        # Git 매니저 초기화
        git_manager = GitVersionManager()
        print("✅ Git 매니저 초기화 성공")
        
        # Git 상태 확인
        status = git_manager.git_status()
        print(f"✅ Git 상태: 브랜치={status['branch']}, 수정된 파일={len(status['modified'])}개")
        
        return True
    except Exception as e:
        print(f"❌ Git 매니저 오류: {e}")
        return False

def test_file_operations():
    """파일 작업 테스트"""
    print("\n🧪 파일 작업 테스트...")
    
    try:
        import file_system_helpers as fs_helpers
        
        print("✅ 파일 시스템 헬퍼 모듈 로드 성공")
        
        # 테스트 파일 경로
        test_file = "test_file.txt"
        test_content = "Hello, AI Coding Brain!"
        
        # 파일 생성
        fs_helpers.create_file(test_file, test_content)
        print(f"✅ 파일 생성: {test_file}")
        
        # 파일 읽기
        content = fs_helpers.read_file(test_file)
        if content == test_content:
            print("✅ 파일 읽기 성공")
        
        # 파일 삭제
        os.remove(test_file)
        print("✅ 테스트 파일 정리 완료")
        
        return True
    except Exception as e:
        print(f"❌ 파일 작업 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 AI Coding Brain MCP 통합 테스트 시작\n")
    
    # 현재 디렉토리 확인
    print(f"📁 현재 디렉토리: {os.getcwd()}")
    print(f"📁 Python 디렉토리: {current_dir}")
    
    # 테스트 실행
    tests = [
        ("모듈 Import", test_imports),
        ("컨텍스트 매니저", test_context_manager),
        ("Wisdom 시스템", test_wisdom_system),
        ("Git 버전 관리자", test_git_manager),
        ("파일 작업", test_file_operations)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 테스트 실행 중 오류: {e}")
            results[test_name] = False
    
    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n총 {total_tests}개 테스트 중 {passed_tests}개 통과 ({passed_tests/total_tests*100:.1f}%)")
    
    # 종료 코드 반환
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
