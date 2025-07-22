"""
Flow 데이터 저장소 구현
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..domain.models import Flow, Plan, Task


class FlowRepository:
    """Flow 데이터 저장소 추상 클래스"""

    def load_all(self) -> Dict[str, Flow]:
        """모든 Flow 로드"""
        raise NotImplementedError

    def save(self, flow: Flow) -> None:
        """Flow 저장"""
        raise NotImplementedError

    def save_all(self, flows: Dict[str, Flow]) -> None:
        """모든 Flow 저장"""
        raise NotImplementedError

    def delete(self, flow_id: str) -> bool:
        """Flow 삭제"""
        raise NotImplementedError

    def exists(self, flow_id: str) -> bool:
        """Flow 존재 여부 확인"""
        raise NotImplementedError


class JsonFlowRepository(FlowRepository):
    """JSON 파일 기반 Flow 저장소"""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            # 프로젝트별 .ai-brain 디렉토리 사용
            storage_path = os.path.join(os.getcwd(), ".ai-brain", "flows.json")

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 파일이 없으면 빈 파일 생성
        if not self.storage_path.exists():
            self._write_data({})

    def load_all(self) -> Dict[str, Flow]:
        """모든 Flow를 로드하여 도메인 객체로 변환"""
        try:
            data = self._read_data()
            flows = {}

            for flow_id, flow_data in data.items():
                if isinstance(flow_data, dict):
                    try:
                        flows[flow_id] = Flow.from_dict(flow_data)
                    except Exception as e:
                        print(f"Warning: Failed to load flow {flow_id}: {e}")
                        # 로드 실패한 flow는 건너뜀
                        continue

            return flows

        except Exception as e:
            print(f"Error loading flows: {e}")
            return {}

    def save(self, flow: Flow) -> None:
        """단일 Flow 저장"""
        flows = self.load_all()
        flows[flow.id] = flow
        self.save_all(flows)

    def save_all(self, flows: Dict[str, Flow]) -> None:
        """모든 Flow를 딕셔너리로 변환하여 저장"""
        data = {}
        for flow_id, flow in flows.items():
            if isinstance(flow, Flow):
                data[flow_id] = flow.to_dict()
            else:
                # 레거시 호환성: dict인 경우 그대로 저장
                data[flow_id] = flow

        self._write_data(data)

    def delete(self, flow_id: str) -> bool:
        """Flow 삭제"""
        flows = self.load_all()
        if flow_id in flows:
            del flows[flow_id]
            self.save_all(flows)
            return True
        return False

    def exists(self, flow_id: str) -> bool:
        """Flow 존재 여부 확인"""
        flows = self.load_all()
        return flow_id in flows

    def _read_data(self) -> Dict:
        """JSON 파일 읽기"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_data(self, data: Dict) -> None:
        """JSON 파일 쓰기"""
        # 백업 생성
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix('.backup')
            try:
                import shutil
                shutil.copy2(self.storage_path, backup_path)
            except Exception as e:
                print(f"Warning: Failed to create backup: {e}")

        # 데이터 저장
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class InMemoryFlowRepository(FlowRepository):
    """메모리 기반 Flow 저장소 (테스트용)"""

    def __init__(self):
        self._flows: Dict[str, Flow] = {}

    def load_all(self) -> Dict[str, Flow]:
        return self._flows.copy()

    def save(self, flow: Flow) -> None:
        self._flows[flow.id] = flow

    def save_all(self, flows: Dict[str, Flow]) -> None:
        self._flows = flows.copy()

    def delete(self, flow_id: str) -> bool:
        if flow_id in self._flows:
            del self._flows[flow_id]
            return True
        return False

    def exists(self, flow_id: str) -> bool:
        return flow_id in self._flows
