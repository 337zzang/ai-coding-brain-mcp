
class FlowSession:
    """Flow 시스템 세션 관리자

    전역 변수 대신 세션 기반으로 상태를 관리합니다.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._manager = None
        self._flow_api = None
        self._initialized = True

    @property
    def manager(self):
        if self._manager is None:
            from .ultra_simple_flow_manager import UltraSimpleFlowManager
            self._manager = UltraSimpleFlowManager()
        return self._manager

    @property
    def flow_api(self):
        if self._flow_api is None:
            from .flow_api import FlowAPI
            self._flow_api = FlowAPI(self.manager)
        return self._flow_api

    def reset(self):
        """세션 초기화"""
        self._manager = None
        self._flow_api = None


# 전역 세션 인스턴스
_session = FlowSession()


def get_flow_session():
    """Flow 세션 반환"""
    return _session
