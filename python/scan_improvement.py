"""
개선된 디렉토리 스캔 함수
"""
import os
from typing import Dict, List
from ai_helpers.helper_result import HelperResult


def improved_scan_directory(path: str, include_hidden: bool = False) -> HelperResult:
    """개선된 디렉토리 스캔 - 오류 처리 및 숨김 파일 옵션"""
    try:
        files = []
        directories = []
        errors = []
        
        for root, dirs, filenames in os.walk(path):
            # 숨김 디렉토리 필터링
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for dirname in dirs:
                dir_path = os.path.join(root, dirname)
                try:
                    # 접근 권한 확인
                    os.listdir(dir_path)
                    directories.append(dir_path)
                except PermissionError:
                    errors.append(f"권한 없음: {dir_path}")
                except Exception as e:
                    errors.append(f"오류 {dir_path}: {str(e)}")
            
            for filename in filenames:
                # 숨김 파일 필터링
                if not include_hidden and filename.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, filename)
                try:
                    # 파일 정보 가져오기
                    stat = os.stat(file_path)
                    files.append({
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })
                except Exception as e:
                    errors.append(f"파일 오류 {file_path}: {str(e)}")
        
        result = {
            'files': files,
            'directories': directories,
            'errors': errors,
            'stats': {
                'total_files': len(files),
                'total_dirs': len(directories),
                'total_errors': len(errors)
            }
        }
        
        return HelperResult.success(result)
        
    except Exception as e:
        return HelperResult.failure(f"스캔 실패: {str(e)}")
