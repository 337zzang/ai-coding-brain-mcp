"""
파일 분석 명령어 구현

/file 명령어를 통해 개별 파일을 분석합니다.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analyzers.project_analyzer import ProjectAnalyzer
from analyzers.manifest_manager import ManifestManager
from smart_print import smart_print


def analyze_file(file_path: str, update_manifest: bool = True) -> Dict[str, Any]:
    """
    특정 파일을 분석하고 상세 정보를 반환합니다.
    
    Args:
        file_path: 분석할 파일 경로 (상대 경로)
        update_manifest: Manifest 업데이트 여부
        
    Returns:
        분석 결과 딕셔너리
    """
    result = {
        'success': False,
        'file_path': file_path,
        'info': None,
        'context': None,
        'error': None
    }
    
    try:
        # 절대 경로로 변환
        if not os.path.isabs(file_path):
            abs_path = os.path.abspath(file_path)
        else:
            abs_path = file_path
        
        # 파일 존재 확인
        if not os.path.exists(abs_path):
            result['error'] = f"파일을 찾을 수 없습니다: {file_path}"
            return result
        
        # 파일인지 확인
        if not os.path.isfile(abs_path):
            result['error'] = f"디렉토리입니다. 파일 경로를 지정하세요: {file_path}"
            return result
        
        # 프로젝트 루트 찾기
        current_dir = Path.cwd()
        project_root = current_dir
        
        # 상대 경로 계산
        try:
            relative_path = Path(abs_path).relative_to(project_root)
            normalized_path = str(relative_path).replace('\\', '/')
        except ValueError:
            # 프로젝트 외부 파일
            result['error'] = "프로젝트 외부 파일은 분석할 수 없습니다."
            return result
        
        # ProjectAnalyzer 사용
        analyzer = ProjectAnalyzer(str(project_root))
        
        # 기존 Manifest에서 파일 정보 확인
        manifest = analyzer.get_manifest()
        existing_info = manifest.get('files', {}).get(normalized_path)
        
        # 파일이 Manifest에 없거나 업데이트가 필요한 경우
        if not existing_info or update_manifest:
            smart_print(f"🔍 파일 분석 중: {normalized_path}")
            
            # 파일 정보 수집
            file_stat = os.stat(abs_path)
            from datetime import datetime
            
            file_info = {
                'absolute_path': abs_path,
                'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'size': file_stat.st_size
            }
            
            # FileAnalyzer로 분석
            from analyzers.file_analyzer import FileAnalyzer
            file_analyzer = FileAnalyzer()
            
            # helpers 객체 설정 (JSON REPL 환경)
            if 'helpers' in globals():
                file_analyzer.helpers = globals()['helpers']
            elif hasattr(sys.modules.get('__main__', None), 'helpers'):
                file_analyzer.helpers = sys.modules['__main__'].helpers
            
            # 분석 실행
            analysis_result = file_analyzer.analyze(abs_path)
            
            # 파일 정보 병합
            file_data = {
                'path': normalized_path,
                'last_modified': file_info['last_modified'],
                'size': file_info['size'],
                'language': analyzer._detect_language(normalized_path),
                **analysis_result
            }
            
            # Manifest 업데이트
            if update_manifest:
                manifest['files'][normalized_path] = file_data
                manifest['last_analyzed'] = datetime.now().isoformat()
                analyzer.manifest_manager.save(manifest)
                smart_print("✅ Manifest 업데이트 완료")
            
            result['info'] = file_data
        else:
            # 기존 정보 사용
            result['info'] = existing_info
        
        # 파일 컨텍스트 생성
        context = analyzer.get_file_context(normalized_path)
        if context:
            result['context'] = context
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        import traceback
        traceback.print_exc()
    
    return result


def get_file_summary(file_path: str) -> Optional[str]:
    """
    파일의 간단한 요약만 반환합니다.
    
    Args:
        file_path: 파일 경로
        
    Returns:
        파일 요약 문자열
    """
    result = analyze_file(file_path, update_manifest=False)
    
    if result['success'] and result['info']:
        info = result['info']
        return (f"{file_path}: {info.get('summary', 'No summary')} "
                f"({info.get('language', 'unknown')}, "
                f"{len(info.get('functions', []))} functions, "
                f"{len(info.get('classes', []))} classes)")
    
    return None


def analyze_directory(dir_path: str, extensions: list = None) -> Dict[str, Any]:
    """
    디렉토리 내 모든 파일을 분석합니다.
    
    Args:
        dir_path: 디렉토리 경로
        extensions: 분석할 파일 확장자 목록 (기본값: ['.py', '.ts', '.js'])
        
    Returns:
        디렉토리 분석 결과
    """
    if extensions is None:
        extensions = ['.py', '.ts', '.js', '.tsx', '.jsx']
    
    result = {
        'directory': dir_path,
        'total_files': 0,
        'analyzed_files': 0,
        'failed_files': [],
        'summary': {}
    }
    
    # 디렉토리 순회
    for root, dirs, files in os.walk(dir_path):
        # 무시할 디렉토리
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', 'node_modules', 'dist', 'build',
            '.pytest_cache', 'venv', '.venv', 'backups'
        }]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                result['total_files'] += 1
                file_path = os.path.join(root, file)
                
                # 파일 분석
                analysis = analyze_file(file_path, update_manifest=True)
                
                if analysis['success']:
                    result['analyzed_files'] += 1
                    
                    # 언어별 통계
                    lang = analysis['info'].get('language', 'unknown')
                    if lang not in result['summary']:
                        result['summary'][lang] = {
                            'count': 0,
                            'total_functions': 0,
                            'total_classes': 0
                        }
                    
                    result['summary'][lang]['count'] += 1
                    result['summary'][lang]['total_functions'] += len(
                        analysis['info'].get('functions', [])
                    )
                    result['summary'][lang]['total_classes'] += len(
                        analysis['info'].get('classes', [])
                    )
                else:
                    result['failed_files'].append({
                        'path': file_path,
                        'error': analysis['error']
                    })
    
    return result


# 테스트 코드
if __name__ == '__main__':
    # 현재 파일 분석 테스트
    result = analyze_file(__file__)
    
    if result['success']:
        print(f"✅ 분석 성공: {result['file_path']}")
        print(f"   요약: {result['info']['summary']}")
        print(f"   함수: {len(result['info']['functions'])}개")
    else:
        print(f"❌ 분석 실패: {result['error']}")
