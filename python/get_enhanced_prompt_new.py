def get_enhanced_prompt(session_key: str = "shared") -> str:
    """AI가 다음 작업을 이어서 수행하도록 구체적인 지침 제공"""
    
    # SessionPool import (전역 변수 접근용)
    from json_repl_session import SESSION_POOL
    
    output = []
    output.append("\n" + "━" * 60)
    output.append("\n🤖 AI 작업 연속성 지침")
    output.append("━" * 60)
    
    # 1. 가장 최근 작업 결과 확인
    if SESSION_POOL.shared_variables:
        recent_items = list(SESSION_POOL.shared_variables.items())[-3:]  # 최근 3개
        
        if recent_items:
            output.append("\n📝 이전 작업에서:")
            
            for key, value in recent_items:
                # Flow 플랜은 따로 처리
                if key == 'current_flow_plan':
                    continue
                    
                # 구체적인 작업 설명 생성
                if 'file' in key or 'content' in key:
                    output.append(f"  ✓ 파일 내용을 '{key}' 변수에 저장했습니다")
                    output.append(f"    → 이제 get_shared('{key}')로 내용을 가져와서 분석하세요")
                    
                elif 'analysis' in key:
                    output.append(f"  ✓ 분석 결과를 '{key}' 변수에 저장했습니다")
                    output.append(f"    → 이제 get_shared('{key}')로 결과를 확인하고 최적화하세요")
                    
                elif 'optimization' in key:
                    output.append(f"  ✓ 최적화 결과를 '{key}' 변수에 저장했습니다")
                    output.append(f"    → 이제 get_shared('{key}')로 결과를 가져와서 테스트하세요")
                    
                elif 'test' in key:
                    output.append(f"  ✓ 테스트 결과를 '{key}' 변수에 저장했습니다")
                    output.append(f"    → 결과를 확인하고 필요시 수정 작업을 진행하세요")
                    
                elif isinstance(value, dict):
                    output.append(f"  ✓ 데이터를 '{key}' 변수에 딕셔너리로 저장했습니다")
                    output.append(f"    → get_shared('{key}')로 가져와서 필요한 필드를 활용하세요")
                    
                elif isinstance(value, list):
                    output.append(f"  ✓ {len(value)}개 항목을 '{key}' 변수에 리스트로 저장했습니다")
                    output.append(f"    → get_shared('{key}')로 가져와서 반복 처리하세요")
                    
                else:
                    output.append(f"  ✓ 결과를 '{key}' 변수에 저장했습니다")
                    output.append(f"    → get_shared('{key}')로 가져와서 다음 작업에 활용하세요")
    
    # 2. Flow 플랜 기반 다음 작업 지시
    flow_plan = SESSION_POOL.shared_variables.get('current_flow_plan')
    if flow_plan:
        tasks = flow_plan.get('tasks', {})
        if isinstance(tasks, dict):
            task_list = list(tasks.values())
        else:
            task_list = tasks if tasks else []
        
        # 다음 태스크 찾기
        next_task = None
        for task in task_list:
            if task.get('status') not in ['completed', 'done']:
                next_task = task
                break
        
        if next_task:
            task_name = next_task.get('title') or next_task.get('name', 'Unknown')
            output.append(f"\n🎯 다음 태스크: '{task_name}'")
            
            # 태스크별 구체적 지침
            if '분석' in task_name:
                output.append("  1. 저장된 데이터를 가져오세요:")
                output.append("     data = get_shared('이전_결과_키')")
                output.append("  2. 분석을 수행하세요")
                output.append("  3. 결과를 저장하세요:")
                output.append("     set_shared('analysis_result', 분석결과)")
                
            elif '최적화' in task_name:
                output.append("  1. 분석 결과를 가져오세요:")
                output.append("     analysis = get_shared('analysis_result')")
                output.append("  2. 최적화를 수행하세요")
                output.append("  3. 결과를 저장하세요:")
                output.append("     set_shared('optimization_result', 최적화결과)")
                
            elif '테스트' in task_name:
                output.append("  1. 이전 결과를 가져오세요:")
                output.append("     data = get_shared('optimization_result')")
                output.append("  2. 테스트를 실행하세요")
                output.append("  3. 결과를 저장하세요:")
                output.append("     set_shared('test_result', 테스트결과)")
                
            else:
                output.append(f"  → {task_name}을(를) 수행하고 결과를 set_shared()로 저장하세요")
    
    else:
        # Flow 플랜이 없을 때 일반 지침
        output.append("\n💡 작업 지침:")
        
        # 저장된 변수 기반 추천
        if 'analysis_result' in SESSION_POOL.shared_variables:
            if 'optimization_result' not in SESSION_POOL.shared_variables:
                output.append("  → 분석이 완료되었으니 최적화를 진행하세요:")
                output.append("    1. analysis = get_shared('analysis_result')")
                output.append("    2. # 최적화 로직 수행")
                output.append("    3. set_shared('optimization_result', 결과)")
        else:
            output.append("  → 초기 데이터를 설정하고 작업을 시작하세요:")
            output.append("    1. # 데이터 준비 또는 파일 읽기")
            output.append("    2. set_shared('data', 준비된_데이터)")
            output.append("    3. # 다음 작업 진행")
    
    # 3. 유용한 명령 안내
    output.append("\n📌 유용한 명령:")
    output.append(f"  • list_shared() - 저장된 모든 변수 키 확인")
    output.append(f"  • var_count() - 현재 {len(SESSION_POOL.shared_variables)}개 변수 저장됨")
    
    output.append("━" * 60)
    
    return "\n".join(output)


# 테스트용 코드
if __name__ == "__main__":
    # 테스트 데이터 설정
    from json_repl_session import SESSION_POOL
    
    SESSION_POOL.shared_variables['file_content'] = "테스트 파일 내용"
    SESSION_POOL.shared_variables['analysis_result'] = {"복잡도": "중간", "라인수": 150}
    
    print(get_enhanced_prompt())