"""
Workflow v3 마이그레이션 CLI
명령줄에서 v2 데이터를 v3로 마이그레이션
"""
import sys
import argparse
from pathlib import Path

# 경로 설정
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from python.workflow.v3.migration import WorkflowMigrator, BatchMigrator
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def migrate_project(project_name: str, force: bool = False):
    """특정 프로젝트 마이그레이션"""
    print(f"\n🔄 프로젝트 마이그레이션: {project_name}")
    print("-" * 50)
    
    migrator = WorkflowMigrator(project_name)
    
    # 마이그레이션 필요 여부 확인
    needed, reason = migrator.check_migration_needed()
    print(f"상태: {reason}")
    
    if not needed and not force:
        print("ℹ️ 마이그레이션이 필요하지 않습니다.")
        return
        
    # 마이그레이션 실행
    result = migrator.migrate(force)
    
    if result['success']:
        print("✅ 마이그레이션 성공!")
        stats = result.get('stats', {})
        print(f"  - 생성된 이벤트: {stats.get('total_events', 0)}개")
        print(f"  - 현재 플랜: {stats.get('current_plan', 'None')}")
        
        # 이벤트 타입별 통계
        event_types = stats.get('event_types', {})
        if event_types:
            print("  - 이벤트 타입:")
            for event_type, count in event_types.items():
                print(f"    * {event_type}: {count}개")
    else:
        print("❌ 마이그레이션 실패!")
        print(f"  - 이유: {result.get('reason', result.get('error', 'Unknown'))}")
        
    # 로그 출력
    if result.get('log'):
        print("\n📋 마이그레이션 로그:")
        for log_entry in result['log'][-5:]:  # 마지막 5개만
            print(f"  [{log_entry['level']}] {log_entry['message']}")
            

def migrate_all(force: bool = False):
    """모든 프로젝트 마이그레이션"""
    print("\n🔄 전체 프로젝트 마이그레이션")
    print("=" * 50)
    
    migrator = BatchMigrator()
    result = migrator.migrate_all(force)
    
    print(f"\n📊 마이그레이션 결과:")
    print(f"  - 총 프로젝트: {result['total_projects']}개")
    print(f"  - 성공: {result['successful']}개")
    print(f"  - 실패: {result['failed']}개")
    
    if result['projects']:
        print("\n📋 프로젝트별 결과:")
        for project in result['projects']:
            status = "✅" if project['result']['success'] else "❌"
            print(f"  {status} {project['project_name']}")
            

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Workflow v2에서 v3로 마이그레이션'
    )
    
    parser.add_argument(
        'project',
        nargs='?',
        help='마이그레이션할 프로젝트 이름 (생략시 전체)'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='기존 v3 파일이 있어도 강제 마이그레이션'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='모든 프로젝트 마이그레이션'
    )
    
    args = parser.parse_args()
    
    print("🚀 Workflow v3 마이그레이션 도구")
    
    if args.all or not args.project:
        migrate_all(args.force)
    else:
        migrate_project(args.project, args.force)
        
    print("\n✨ 마이그레이션 작업 완료!")
    

if __name__ == '__main__':
    main()
