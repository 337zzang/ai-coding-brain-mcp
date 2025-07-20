"""
flow_project 래퍼 - 워크플로우 자동 연동
"""
import os
import sys
# from workflow.global_context import get_global_context_manager  # WorkflowManager로 대체됨

def flow_project_with_workflow(project_name: str):
    """프로젝트 전환 시 워크플로우도 자동으로 전환 - 바탕화면에서만 검색"""
    result = {"success": False}

    try:
        from pathlib import Path
        
        # 동적으로 바탕화면 경로 찾기
        desktop_candidates = [
            Path.home() / "Desktop",
            Path.home() / "바탕화면",
            Path.home() / "OneDrive" / "Desktop",
            Path.home() / "OneDrive" / "바탕 화면"
        ]
        
        # 실제 존재하는 바탕화면 경로 찾기
        desktop_path = None
        for candidate in desktop_candidates:
            if candidate.exists() and candidate.is_dir():
                desktop_path = candidate
                break
        
        if not desktop_path:
            result = {
                "success": False,
                "error": "바탕화면 경로를 찾을 수 없습니다"
            }
            print("❌ 바탕화면 경로를 찾을 수 없습니다")
            return result
        
        # 바탕화면에서만 프로젝트 찾기
        project_path = desktop_path / project_name


        if project_path.exists() and project_path.is_dir():
            # 현재 디렉토리 저장
            previous_dir = os.getcwd()
            
            # 프로젝트로 이동
            os.chdir(str(project_path))
            
            # 프로젝트 정보 수집
            import json
            from datetime import datetime
            
            project_info = {
                "name": project_name,
                "path": str(project_path),
                "type": "node" if (project_path / "package.json").exists() else "python",
                "has_git": (project_path / ".git").exists(),
                "switched_at": datetime.now().isoformat()
            }
            
            # 캐시 업데이트 (프로젝트 정보 저장)
            cache_dir = Path.home() / ".ai-coding-brain" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / "current_project.json"
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=2)
            

            # 글로벌 컨텍스트 저장
            try:
            # global_ctx = get_global_context_manager()  # 더 이상 필요없음

                # 컨텍스트 데이터 준비
                context_data = {
                    'project_name': project_name,
                    'project_info': project_info,
                    'recent_work': f"프로젝트 전환: {project_name}"
                }

                # 글로벌 컨텍스트에 저장
                global_ctx.save_project_context(project_name, context_data)

                # AI 컨텍스트 파일 생성
                ai_context = global_ctx.create_ai_context_file(project_name)

                print("📋 글로벌 컨텍스트 저장 완료")
            except Exception as e:
                print(f"⚠️ 글로벌 컨텍스트 저장 중 오류: {e}")

            result = {
                "success": True,
                "project": project_info,
                "previous": previous_dir
            }
            print(f"✅ 프로젝트 전환: {project_name}")
            print(f"📍 경로: {project_path}")

            # 워크플로우 전환 시도 (에러 무시)
            try:
                from workflow_wrapper import wf
                wf(f"/start {project_name}")
                print(f"✅ 워크플로우도 {project_name}로 전환됨")
            except:
                pass  # 워크플로우 실패해도 프로젝트 전환은 성공

        else:
            result = {
                "success": False,
                "error": f"바탕화면에서 프로젝트를 찾을 수 없음: {project_name}"
            }
            print(f"❌ 바탕화면에서 프로젝트를 찾을 수 없음: {project_name}")
            print(f"   검색 경로: {desktop_path}")

    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
        print(f"❌ 프로젝트 전환 실패: {e}")

    return result

# 별칭
fp = flow_project_with_workflow
flow_project = flow_project_with_workflow
