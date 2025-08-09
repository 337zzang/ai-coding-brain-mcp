# 리팩토링 실행 준비 확인

import os
import shutil
from datetime import datetime

print("🔍 리팩토링 전 최종 확인")
print("="*70)

# 백업 폴더 생성
backup_dir = f"python/backups/refactoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
print(f"백업 폴더: {backup_dir}")

# 삭제 대상 파일 목록
delete_list = [
    # 백업/임시
    "python/ai_helpers_new/backups/",
    "python/ai_helpers_new/backup_utils.py",
    "python/ai_helpers_new/__init___full.py",

    # search 중복 (6개)
    "python/ai_helpers_new/search_improved.py",
    "python/ai_helpers_new/search_improved_part1.py",
    "python/ai_helpers_new/search_improved_part2.py",
    "python/ai_helpers_new/search_improved_part3.py",
    "python/ai_helpers_new/search_improved_part4.py",
    "python/ai_helpers_new/search_improved_part5.py",

    # facade 중복 (3개)
    "python/ai_helpers_new/facade.py",
    "python/ai_helpers_new/facade_minimal.py",
    "python/ai_helpers_new/facade_safe_with_llm.py",

    # replace 중복 (4개)
    "python/ai_helpers_new/replace_block_final.py",
    "python/ai_helpers_new/smart_replace_ultimate.py",
    "python/ai_helpers_new/improved_insert_delete.py",
    "python/ai_helpers_new/integrate_replace_block.py",

    # 테스트/데모 (3개)
    "python/ai_helpers_new/test_search_improved.py",
    "python/repl_kernel/demo_error_isolation.py",
    "python/api/example_javascript_execution.py",

    # Web automation 중복 (8개)
    "python/api/web_automation_errors.py",
    "python/api/web_automation_extraction.py",
    "python/api/web_automation_integrated.py",
    "python/api/web_automation_manager.py",
    "python/api/web_automation_recorder.py",
    "python/api/web_automation_repl.py",
    "python/api/web_automation_smart_wait.py",
    "python/api/web_session_simple.py"
]

print(f"\n📊 삭제 예정 파일: {len(delete_list)}개")

# 삭제될 파일 크기 계산
total_delete_size = 0
for path in delete_list:
    if os.path.exists(path):
        if os.path.isfile(path):
            total_delete_size += os.path.getsize(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    total_delete_size += os.path.getsize(os.path.join(root, file))

print(f"삭제될 용량: {total_delete_size:,} bytes ({total_delete_size/1024:.2f} KB)")

# 유지할 핵심 파일 확인
core_files = {
    "ai_helpers_new": [
        "__init__.py",
        "file.py",
        "code.py",
        "search.py",
        "git.py",
        "llm.py",
        "project.py",
        "excel.py",
        "facade_safe.py",
        "wrappers.py",
        "util.py",
        "flow_api.py",
        "ultra_simple_flow_manager.py",
        "simple_flow_commands.py",
        "task_logger.py"
    ],
    "repl_kernel": [
        "__init__.py",
        "manager.py",
        "worker.py"
    ],
    "api": [
        "__init__.py",
        "web_session.py",
        "web_session_persistent.py",
        "web_automation_helpers.py"
    ]
}

print(f"\n✅ 유지할 핵심 파일:")
for folder, files in core_files.items():
    print(f"  {folder}: {len(files)}개")

print(f"\n🎯 최종 결과 예상:")
print(f"  - 파일 수: 87개 → 약 25개")
print(f"  - 크기: 738KB → 약 400KB")
print(f"  - 중복 제거율: 87%")
