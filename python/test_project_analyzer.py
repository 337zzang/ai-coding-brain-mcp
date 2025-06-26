"""
ProjectAnalyzer 테스트 스크립트

새로 구현한 ProjectAnalyzer 시스템을 테스트합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analyzers.project_analyzer import ProjectAnalyzer
from analyzers.manifest_manager import ManifestManager


def test_project_analyzer():
    """ProjectAnalyzer 기본 기능 테스트"""
    print("🧪 ProjectAnalyzer 테스트 시작...\n")
    
    # 1. ProjectAnalyzer 생성
    analyzer = ProjectAnalyzer(project_root)
    print(f"✅ ProjectAnalyzer 생성 완료")
    print(f"   프로젝트: {analyzer.project_name}")
    print(f"   경로: {analyzer.project_root}\n")
    
    # 2. 간단한 분석 실행 (작은 범위로 테스트)
    print("📊 분석 실행 중... (python/analyzers 디렉토리만)")
    
    # 테스트를 위해 임시로 전체 스캔 대신 특정 디렉토리만 분석
    original_project_root = analyzer.project_root
    analyzer.project_root = project_root / "python" / "analyzers"
    
    result = analyzer.analyze_and_update(force_full_scan=True)
    
    print(f"\n📈 분석 결과:")
    print(f"   - 성공: {result['success']}")
    print(f"   - 전체 파일: {result['total_files']}")
    print(f"   - 분석된 파일: {result['analyzed']}")
    
    # 3. Manifest 확인
    analyzer.project_root = original_project_root  # 원래 경로로 복원
    manifest = analyzer.get_manifest()
    
    print(f"\n📄 Manifest 정보:")
    print(f"   - 프로젝트명: {manifest.get('project_name', 'N/A')}")
    print(f"   - 분석 시간: {manifest.get('last_analyzed', 'N/A')}")
    print(f"   - 파일 수: {len(manifest.get('files', {}))}")
    
    # 4. 분석된 파일 정보 샘플 출력
    files = manifest.get('files', {})
    if files:
        print(f"\n📁 분석된 파일 샘플:")
        for i, (file_path, file_info) in enumerate(list(files.items())[:3]):
            print(f"\n   [{i+1}] {file_path}")
            print(f"       - 요약: {file_info.get('summary', 'N/A')}")
            print(f"       - 언어: {file_info.get('language', 'N/A')}")
            print(f"       - 함수: {len(file_info.get('functions', []))}개")
            print(f"       - 클래스: {len(file_info.get('classes', []))}개")
    
    # 5. 브리핑 데이터 생성 테스트
    briefing = analyzer.get_briefing_data()
    print(f"\n📊 브리핑 데이터:")
    print(f"   - 프로젝트: {briefing['project_name']}")
    print(f"   - 파일 통계: {briefing['file_stats']}")
    
    # 6. 구조 리포트 생성 테스트
    print(f"\n📝 구조 리포트 생성 테스트...")
    report = analyzer.generate_structure_report()
    print(f"   리포트 크기: {len(report)} 글자")
    print(f"   첫 300자:\n{report[:300]}...")
    
    print(f"\n✅ 모든 테스트 완료!")


def test_manifest_manager():
    """ManifestManager 기능 테스트"""
    print("\n\n🧪 ManifestManager 테스트 시작...\n")
    
    manager = ManifestManager(project_root)
    
    # 1. 통계 확인
    stats = manager.get_statistics()
    print(f"📊 Manifest 통계:")
    print(f"   - 전체 파일: {stats['total_files']}")
    print(f"   - 분석된 파일: {stats['analyzed_files']}")
    print(f"   - Manifest 크기: {stats['manifest_size']} bytes")
    
    # 2. 요약 생성
    summary = manager.export_summary()
    print(f"\n📄 요약 생성 완료 ({len(summary)} 글자)")
    
    # 3. file_directory.md 마이그레이션 테스트 준비
    file_dir_path = project_root / "memory" / "file_directory.md"
    if file_dir_path.exists():
        print(f"\n🔄 file_directory.md 마이그레이션 가능")
        print(f"   경로: {file_dir_path}")
        # 실제 마이그레이션은 사용자 확인 후 실행
    
    print(f"\n✅ ManifestManager 테스트 완료!")


if __name__ == '__main__':
    try:
        test_project_analyzer()
        test_manifest_manager()
        
        print("\n" + "="*60)
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n💡 다음 단계:")
        print("1. enhanced_flow.py와 통합")
        print("2. 기존 file_directory 생성기 제거")
        print("3. Wisdom 시스템과 통합")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
