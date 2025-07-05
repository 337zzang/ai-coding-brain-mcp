
"""
flow_project 디버깅 유틸리티
사용법: from debug_flow import debug_flow_project
"""
import os
import sys
import json
import traceback
import builtins
from pathlib import Path

def debug_flow_project(project_name, verbose=True):
    """
    flow_project 실행을 디버깅하는 함수
    
    Args:
        project_name: 프로젝트 이름
        verbose: 상세 출력 여부
    
    Returns:
        dict: 디버깅 결과
    """
    debug_info = {
        'project_name': project_name,
        'initial_cwd': os.getcwd(),
        'steps': [],
        'errors': [],
        'result': None
    }
    
    def log(message, level='INFO'):
        if verbose:
            print(f"[{level}] {message}")
        debug_info['steps'].append({'level': level, 'message': message})
    
    try:
        # 1. 환경 확인
        log("환경 확인 시작")
        log(f"현재 디렉토리: {os.getcwd()}")
        log(f"Python 버전: {sys.version.split()[0]}")
        log(f"helpers 존재: {'helpers' in builtins.__dict__}")
        
        # 2. 모듈 확인
        log("\nenhanced_flow 모듈 확인")
        flow_file = Path('python/enhanced_flow.py')
        if flow_file.exists():
            log(f"✅ {flow_file} 존재")
            
            # 함수 존재 확인
            with open(flow_file, 'r', encoding='utf-8') as f:
                content = f.read()
                has_flow_project = 'def flow_project' in content
                has_cmd_flow = 'def cmd_flow_with_context' in content
                
                log(f"flow_project 함수: {'✅' if has_flow_project else '❌'}")
                log(f"cmd_flow_with_context 함수: {'✅' if has_cmd_flow else '❌'}")
        else:
            log(f"❌ {flow_file} 없음", 'ERROR')
            
        # 3. 실행
        log("\nflow_project 실행")
        if 'helpers' in builtins.__dict__ and hasattr(builtins.__dict__['helpers'], 'cmd_flow_with_context'):
            result = builtins.__dict__['helpers'].cmd_flow_with_context(project_name)
            debug_info['result'] = result
            
            # 결과 분석
            log("\n실행 결과 분석")
            if result is None:
                log("⚠️ None 반환됨", 'WARNING')
            elif isinstance(result, dict):
                log(f"✅ dict 반환 (키: {', '.join(result.keys())})")
                if result.get('success'):
                    log("✅ 성공")
                else:
                    log(f"❌ 실패: {result.get('error', 'Unknown')}", 'ERROR')
            else:
                log(f"⚠️ 예상치 못한 타입: {type(result)}", 'WARNING')
        else:
            log("❌ helpers.cmd_flow_with_context 없음", 'ERROR')
            
    except Exception as e:
        log(f"\n예외 발생: {type(e).__name__}: {e}", 'ERROR')
        debug_info['errors'].append({
            'type': type(e).__name__,
            'message': str(e),
            'traceback': traceback.format_exc()
        })
        
    finally:
        debug_info['final_cwd'] = os.getcwd()
        
    return debug_info

def check_flow_health():
    """flow_project 시스템 상태 확인"""
    print("🏥 flow_project 시스템 진단")
    print("="*50)
    
    checks = {
        'enhanced_flow.py 존재': os.path.exists('python/enhanced_flow.py'),
        'helpers 사용 가능': 'helpers' in builtins.__dict__,
        'cmd_flow_with_context 메서드': 'helpers' in builtins.__dict__ and hasattr(builtins.__dict__['helpers'], 'cmd_flow_with_context'),
        'memory 디렉토리': os.path.exists('memory'),
        'context.json': os.path.exists('memory/context.json'),
    }
    
    all_good = True
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check}")
        if not status:
            all_good = False
    
    print("="*50)
    if all_good:
        print("✅ 모든 시스템이 정상입니다!")
    else:
        print("⚠️ 일부 문제가 발견되었습니다.")
        
    return all_good
