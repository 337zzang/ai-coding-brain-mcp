"""
ProjectAnalyzer 통합 스크립트

기존 시스템과 ProjectAnalyzer를 통합합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analyzers.project_analyzer import ProjectAnalyzer
from analyzers.manifest_manager import ManifestManager


def integrate_with_enhanced_flow():
    """enhanced_flow.py와 통합하기 위한 함수"""
    print("🔧 enhanced_flow.py 통합 준비...\n")
    
    # 1. 기존 file_directory.md 마이그레이션
    manager = ManifestManager(project_root)
    file_dir_path = project_root / "memory" / "file_directory.md"
    
    if file_dir_path.exists():
        print(f"📄 기존 file_directory.md 발견")
        print(f"   크기: {file_dir_path.stat().st_size} bytes")
        
        response = input("\n🔄 project_manifest.json으로 마이그레이션하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            success = manager.migrate_from_file_directory(str(file_dir_path))
            if success:
                print("✅ 마이그레이션 완료!")
            else:
                print("❌ 마이그레이션 실패")
                return False
    
    # 2. 전체 프로젝트 분석
    print(f"\n🔍 전체 프로젝트 분석 시작...")
    analyzer = ProjectAnalyzer(project_root)
    
    response = input("전체 프로젝트를 분석하시겠습니까? (많은 시간이 걸릴 수 있습니다) (y/n): ")
    if response.lower() == 'y':
        result = analyzer.analyze_and_update()
        print(f"\n✅ 분석 완료!")
        print(f"   - 전체 파일: {result['total_files']}")
        print(f"   - 분석된 파일: {result['analyzed']}")
        
        # 구조 리포트 저장
        report = analyzer.generate_structure_report()
        report_path = project_root / "memory" / "project_structure_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"   - 구조 리포트 저장: {report_path}")
    
    # 3. 통합 코드 제안
    print(f"\n📝 enhanced_flow.py 통합 코드 제안:\n")
    
    integration_code = '''# enhanced_flow.py 수정 제안

# 기존 import 부분에 추가:
from analyzers.project_analyzer import ProjectAnalyzer

# flow_project 함수 내부 수정:
def flow_project(project_name: str) -> Dict[str, Any]:
    """향상된 flow_project - ProjectAnalyzer 통합"""
    
    # ... 기존 코드 ...
    
    # ProjectAnalyzer로 프로젝트 분석 (file_directory 생성 대체)
    analyzer = ProjectAnalyzer(project_path)
    
    # 빠른 업데이트 (변경된 파일만)
    analyzer.analyze_and_update()
    
    # 브리핑 데이터 가져오기
    briefing_data = analyzer.get_briefing_data()
    
    # 구조 리포트 생성 (기존 file_directory.md 대체)
    structure_report = analyzer.generate_structure_report()
    
    # ... 나머지 코드 ...
'''
    
    print(integration_code)
    
    return True


def cleanup_old_files():
    """구 시스템 파일들을 정리합니다."""
    print("\n🧹 구 시스템 파일 정리...\n")
    
    old_files = [
        "python/enhanced_file_directory_generator.py",
        "python/enhanced_file_directory_generator.backup.py",
        "python/file_directory_generator.py"
    ]
    
    print("삭제 대상 파일:")
    for file_path in old_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  - {file_path} ({full_path.stat().st_size} bytes)")
    
    response = input("\n이 파일들을 삭제하시겠습니까? (백업이 생성됩니다) (y/n): ")
    if response.lower() == 'y':
        backup_dir = project_root / "backups" / "old_file_generators"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in old_files:
            full_path = project_root / file_path
            if full_path.exists():
                # 백업
                backup_path = backup_dir / full_path.name
                import shutil
                shutil.copy2(full_path, backup_path)
                print(f"  📦 백업: {backup_path}")
                
                # 삭제
                full_path.unlink()
                print(f"  🗑️ 삭제: {file_path}")
        
        print("\n✅ 정리 완료!")
    
    return True


if __name__ == '__main__':
    print("🚀 ProjectAnalyzer 통합 스크립트\n")
    print("이 스크립트는 다음 작업을 수행합니다:")
    print("1. 기존 file_directory.md → project_manifest.json 마이그레이션")
    print("2. 전체 프로젝트 분석 실행")
    print("3. enhanced_flow.py 통합 코드 제안")
    print("4. 구 파일 정리\n")
    
    response = input("계속하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        # 통합 실행
        if integrate_with_enhanced_flow():
            # 구 파일 정리
            cleanup_old_files()
            
            print("\n🎉 통합 작업 완료!")
            print("\n💡 남은 작업:")
            print("1. enhanced_flow.py에 제안된 코드 적용")
            print("2. Wisdom 시스템과 통합")
            print("3. 전체 테스트")
    else:
        print("취소되었습니다.")
