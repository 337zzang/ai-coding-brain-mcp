"""
기존 Flow 시스템에서 폴더 기반 시스템으로 마이그레이션
- 중앙 flows.json → 프로젝트별 폴더 구조
- 백업 생성
- 검증 포함
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from .domain.models import Flow, Plan, Task
from .repository.folder_based_repository import FileFlowRepository, FilePlanRepository


class FlowMigrationTool:
    """Flow 마이그레이션 도구"""

    def __init__(self, old_base_path: str = ".ai-brain", backup: bool = True):
        """
        Args:
            old_base_path: 기존 .ai-brain 경로
            backup: 백업 생성 여부
        """
        self.old_base = Path(old_base_path)
        self.old_flows_json = self.old_base / "flows.json"
        self.backup_enabled = backup

        # 통계
        self.stats = {
            'total_flows': 0,
            'migrated_flows': 0,
            'total_plans': 0,
            'migrated_plans': 0,
            'total_tasks': 0,
            'errors': []
        }

    def migrate(self, target_projects: Dict[str, str] = None) -> Dict[str, Any]:
        """
        마이그레이션 실행

        Args:
            target_projects: {flow_id: project_path} 매핑
                           None이면 현재 디렉토리로 모두 마이그레이션

        Returns:
            마이그레이션 결과 통계
        """
        print("🚀 Flow 마이그레이션 시작")

        # 1. 기존 데이터 확인
        if not self._validate_source():
            return self.stats

        # 2. 백업 생성
        if self.backup_enabled:
            self._create_backup()

        # 3. 기존 데이터 로드
        old_data = self._load_old_data()
        if not old_data:
            print("❌ 마이그레이션할 데이터가 없습니다.")
            return self.stats

        # 4. 프로젝트 매핑 준비
        if target_projects is None:
            # 기본값: 현재 디렉토리
            target_projects = {}
            for flow_id in old_data.keys():
                target_projects[flow_id] = os.getcwd()

        # 5. 각 Flow 마이그레이션
        for flow_id, flow_data in old_data.items():
            self.stats['total_flows'] += 1

            # 대상 프로젝트 경로
            project_path = target_projects.get(flow_id, os.getcwd())

            try:
                self._migrate_flow(flow_id, flow_data, project_path)
                self.stats['migrated_flows'] += 1
                print(f"✅ Flow 마이그레이션 완료: {flow_id}")
            except Exception as e:
                error_msg = f"Flow {flow_id} 마이그레이션 실패: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"❌ {error_msg}")

        # 6. 결과 보고
        self._print_report()

        return self.stats

    def _validate_source(self) -> bool:
        """소스 데이터 검증"""
        if not self.old_flows_json.exists():
            print(f"❌ 기존 flows.json 파일이 없습니다: {self.old_flows_json}")
            return False

        try:
            with open(self.old_flows_json) as f:
                json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"❌ flows.json 파일이 손상되었습니다: {e}")
            return False

    def _create_backup(self) -> None:
        """백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.old_base / f"flows_backup_{timestamp}.json"

        shutil.copy2(self.old_flows_json, backup_path)
        print(f"✅ 백업 생성: {backup_path}")

    def _load_old_data(self) -> Dict[str, Any]:
        """기존 데이터 로드"""
        with open(self.old_flows_json) as f:
            data = json.load(f)

        # 형식 확인
        if isinstance(data, dict) and 'flows' in data:
            # 새로운 형식
            return data['flows']
        elif isinstance(data, dict):
            # 기존 형식 (flow_id: flow_data)
            return data
        else:
            print(f"❌ 알 수 없는 데이터 형식")
            return {}

    def _migrate_flow(self, flow_id: str, flow_data: Dict[str, Any], project_path: str) -> None:
        """개별 Flow 마이그레이션"""
        # Flow 폴더 경로
        flow_base = Path(project_path) / '.ai-brain' / 'flow'

        # Repository 초기화
        flow_repo = FileFlowRepository(str(flow_base))
        plan_repo = FilePlanRepository(str(flow_base))

        # 1. Flow 객체 생성
        flow = Flow.from_dict(flow_data)

        # plan_ids 추출
        plan_ids = []
        if 'plans' in flow_data:
            plan_ids = list(flow_data['plans'].keys())

        # Flow 메타데이터에 plan_ids 추가
        flow_meta = flow.to_dict()
        flow_meta['plan_ids'] = plan_ids
        if 'plans' in flow_meta:
            del flow_meta['plans']

        # Flow 저장 (메타데이터만)
        flow_repo.save_flow(Flow.from_dict(flow_meta))

        # 2. 각 Plan 마이그레이션
        if 'plans' in flow_data:
            for plan_id, plan_data in flow_data['plans'].items():
                self.stats['total_plans'] += 1

                try:
                    # Plan 객체 생성
                    plan = Plan.from_dict(plan_data)
                    plan.flow_id = flow_id

                    # Task 수 계산
                    if hasattr(plan, 'tasks'):
                        self.stats['total_tasks'] += len(plan.tasks)

                    # Plan 저장 (Tasks 포함)
                    plan_repo.save_plan(plan)
                    self.stats['migrated_plans'] += 1

                except Exception as e:
                    error_msg = f"Plan {plan_id} 마이그레이션 실패: {str(e)}"
                    self.stats['errors'].append(error_msg)

    def _print_report(self) -> None:
        """마이그레이션 보고서 출력"""
        print("\n" + "="*50)
        print("📊 마이그레이션 결과 보고서")
        print("="*50)
        print(f"총 Flow 수: {self.stats['total_flows']}")
        print(f"마이그레이션된 Flow: {self.stats['migrated_flows']}")
        print(f"총 Plan 수: {self.stats['total_plans']}")
        print(f"마이그레이션된 Plan: {self.stats['migrated_plans']}")
        print(f"총 Task 수: {self.stats['total_tasks']}")

        if self.stats['errors']:
            print(f"\n❌ 오류 ({len(self.stats['errors'])}개):")
            for error in self.stats['errors'][:5]:  # 처음 5개만
                print(f"  - {error}")
        else:
            print("\n✅ 모든 데이터가 성공적으로 마이그레이션되었습니다!")
        print("="*50)


def migrate_to_folder_flow(
    old_path: str = ".ai-brain",
    project_mappings: Dict[str, str] = None,
    backup: bool = True
) -> Dict[str, Any]:
    """
    편의 함수: Flow 시스템 마이그레이션

    사용 예:
        # 모든 Flow를 현재 프로젝트로
        migrate_to_folder_flow()

        # 특정 매핑으로
        migrate_to_folder_flow(project_mappings={
            'flow_project1_xxx': '/path/to/project1',
            'flow_project2_xxx': '/path/to/project2'
        })
    """
    tool = FlowMigrationTool(old_path, backup)
    return tool.migrate(project_mappings)


if __name__ == "__main__":
    # 직접 실행 시
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--no-backup":
        backup = False
    else:
        backup = True

    print("Flow 시스템 마이그레이션을 시작합니다...")
    result = migrate_to_folder_flow(backup=backup)

    if result['migrated_flows'] == result['total_flows']:
        print("\n✅ 마이그레이션이 완료되었습니다!")
        sys.exit(0)
    else:
        print("\n⚠️ 일부 데이터가 마이그레이션되지 않았습니다.")
        sys.exit(1)
