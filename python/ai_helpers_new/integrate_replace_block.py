#!/usr/bin/env python
"""
Replace Block 자동 통합 스크립트
"""

import shutil
from pathlib import Path

def integrate_replace_block():
    """replace_block을 ai_helpers_new에 통합"""

    # 경로 설정
    source = Path("python/ai_helpers_new/replace_block_final.py")
    target_dir = Path("python/ai_helpers_new")
    init_file = target_dir / "__init__.py"

    # 1. 백업
    backup_dir = Path("python/ai_helpers_new.backup")
    if not backup_dir.exists():
        shutil.copytree(target_dir, backup_dir)
        print(f"✅ Backup created: {backup_dir}")

    # 2. __init__.py 수정
    with open(init_file, 'r') as f:
        content = f.read()

    # replace_block import 추가
    import_code = """
# Replace Block Integration
from .replace_block_final import (
    replace_block,
    replace_block_preview,
    replace_block_exact,
    replace_block_safe
)

# Override existing functions
replace = replace_block
safe_replace = replace_block_safe
replace_v2 = replace_block
"""

    if "replace_block" not in content:
        with open(init_file, 'a') as f:
            f.write(import_code)
        print(f"✅ Updated: {init_file}")
    else:
        print("ℹ️ Already integrated")

    print("✅ Integration complete!")
    print("Test with: import ai_helpers_new as h; h.replace(file, old, new)")

if __name__ == "__main__":
    integrate_replace_block()
