
"""
EventStore - workflow_events.json 파일의 두 가지 포맷을 모두 지원하는 어댑터
o3의 조언을 바탕으로 구현
"""
import json
import os
import threading
from typing import Dict, List, Union
import uuid
from datetime import datetime


class EventStore:
    """이벤트 저장소 - 리스트/딕셔너리 포맷 모두 지원"""

    def __init__(self, path: str, lock: threading.Lock = None):
        self.path = path
        self._lock = lock or threading.Lock()
        self.max_events = 1000  # 최대 이벤트 수

    def _load_events(self) -> Union[List, Dict]:
        """파일에서 이벤트 데이터 로드"""
        if not os.path.exists(self.path):
            return []  # 기본값은 리스트

        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 이벤트 파일 로드 실패: {e}")
            return []

    def _save(self, data: Union[List, Dict]):
        """파일에 이벤트 데이터 저장 (atomic operation)"""
        tmp_path = f"{self.path}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # atomic rename
            if os.path.exists(self.path):
                os.replace(tmp_path, self.path)
            else:
                os.rename(tmp_path, self.path)
        except Exception as e:
            print(f"⚠️ 이벤트 파일 저장 실패: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def append(self, event: Dict):
        """이벤트 추가"""
        with self._lock:
            data = self._load_events()

            # ID가 없으면 생성
            if 'id' not in event:
                event['id'] = str(uuid.uuid4())

            # 리스트 포맷
            if isinstance(data, list):
                data.append(event)
                # 최대 개수 유지
                if len(data) > self.max_events:
                    data = data[-self.max_events:]

            # 딕셔너리 포맷
            elif isinstance(data, dict):
                if 'events' not in data:
                    data['events'] = []
                data['events'].append(event)
                # 최대 개수 유지
                if len(data['events']) > self.max_events:
                    data['events'] = data['events'][-self.max_events:]

            else:
                raise TypeError(f"지원하지 않는 이벤트 저장소 포맷: {type(data)}")

            self._save(data)

    def get_all(self) -> List[Dict]:
        """모든 이벤트 조회 (리스트로 통일하여 반환)"""
        with self._lock:
            data = self._load_events()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'events' in data:
                return data['events']
            else:
                return []

    def clear(self):
        """모든 이벤트 삭제"""
        with self._lock:
            self._save([])  # 리스트 포맷으로 초기화
