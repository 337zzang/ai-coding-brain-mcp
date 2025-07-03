#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
print 문을 logger로 자동 변환하는 스크립트
"""
import re
import os
import sys

def convert_prints_to_logger(file_path):
    """파일의 print 문을 logger로 변환"""
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 변환 패턴 정의
    patterns = [
        # print("✅ ...") -> logger.info("✅ ...")
        (r'print\(["\'](✅[^"\']*)["\']', r'logger.info("\1"'),
        # print("❌ ...") -> logger.error("❌ ...")
        (r'print\(["\'](❌[^"\']*)["\']', r'logger.error("\1"'),
        # print("⚠️ ...") -> logger.warning("⚠️ ...")
        (r'print\(["\'](⚠️[^"\']*)["\']', r'logger.warning("\1"'),
        # print(f"✅ ...") -> logger.info(f"✅ ...")
        (r'print\(f["\'](✅[^"\']*)["\']', r'logger.info(f"\1"'),
        # print(f"❌ ...") -> logger.error(f"❌ ...")
        (r'print\(f["\'](❌[^"\']*)["\']', r'logger.error(f"\1"'),
        # print(f"⚠️ ...") -> logger.warning(f"⚠️ ...")
        (r'print\(f["\'](⚠️[^"\']*)["\']', r'logger.warning(f"\1"'),
        # 일반 print() -> logger.info()
        (r'print\(([^)]+)\)', r'logger.info(\1)'),
    ]
    
    # 패턴 적용
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def main():
    # 변환할 파일 목록
    files_to_convert = [
        'python/json_repl_session.py',
        'python/enhanced_flow.py',
        'python/core/context_manager.py',
        'python/workflow/commands.py',
        'python/workflow/workflow_manager.py',
    ]
    
    for file_path in files_to_convert:
        if os.path.exists(file_path):
            print(f"Converting {file_path}...")
            
            # 백업 생성
            backup_path = file_path + '.backup'
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            
            # 변환 수행
            converted = convert_prints_to_logger(file_path)
            
            # 로거 import 추가 (아직 없는 경우)
            if 'from utils.logger import' not in converted:
                # import 섹션 찾기
                import_section_end = 0
                lines = converted.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('import') and not line.startswith('from'):
                        import_section_end = i
                        break
                
                # logger import 추가
                lines.insert(import_section_end, '')
                lines.insert(import_section_end + 1, '# 로거 설정')
                lines.insert(import_section_end + 2, 'from utils.logger import setup_logger')
                lines.insert(import_section_end + 3, f'logger = setup_logger("{os.path.basename(file_path).replace(".py", "")}")')
                lines.insert(import_section_end + 4, '')
                
                converted = '\n'.join(lines)
            
            # 파일 쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted)
            
            print(f"✅ Converted {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

if __name__ == '__main__':
    main()
