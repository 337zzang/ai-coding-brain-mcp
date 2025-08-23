"""
System Monitoring Dashboard - 시스템 상태 모니터링 대시보드
전체 시스템 상태를 실시간으로 모니터링
생성일: 2025-08-23
"""

import os
import json
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import threading

class SystemMonitor:
    """시스템 모니터링 클래스"""

    def __init__(self, history_size: int = 100):
        """
        Args:
            history_size: 히스토리 보관 크기
        """
        self.history_size = history_size

        # 메트릭 히스토리
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)

        # 이벤트 로그
        self.events = deque(maxlen=1000)

        # 모니터링 스레드
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()

    def start_monitoring(self, interval: int = 5):
        """모니터링 시작"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_worker,
                args=(interval,),
                daemon=True
            )
            self.monitor_thread.start()

    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False

    def _monitor_worker(self, interval: int):
        """모니터링 워커 스레드"""
        while self.monitoring:
            metrics = self._collect_metrics()

            with self.lock:
                self.cpu_history.append(metrics['cpu'])
                self.memory_history.append(metrics['memory'])
                self.disk_history.append(metrics['disk'])

            time.sleep(interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)

            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used // (1024 * 1024)  # MB
            memory_total = memory.total // (1024 * 1024)  # MB

            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used // (1024 * 1024 * 1024)  # GB
            disk_total = disk.total // (1024 * 1024 * 1024)  # GB

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count()
                },
                'memory': {
                    'percent': memory_percent,
                    'used_mb': memory_used,
                    'total_mb': memory_total
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': disk_used,
                    'total_gb': disk_total
                }
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def add_event(self, event_type: str, message: str, level: str = "info"):
        """이벤트 추가"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'level': level  # info, warning, error
        }

        with self.lock:
            self.events.append(event)

    def get_current_status(self) -> Dict[str, Any]:
        """현재 시스템 상태"""
        metrics = self._collect_metrics()

        return {
            'current': metrics,
            'healthy': self._check_health(metrics)
        }

    def _check_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """시스템 건강 상태 체크"""
        issues = []

        # CPU 체크
        if 'cpu' in metrics and metrics['cpu'].get('percent', 0) > 80:
            issues.append("CPU 사용률 높음")

        # 메모리 체크
        if 'memory' in metrics and metrics['memory'].get('percent', 0) > 85:
            issues.append("메모리 사용률 높음")

        # 디스크 체크
        if 'disk' in metrics and metrics['disk'].get('percent', 0) > 90:
            issues.append("디스크 공간 부족")

        return {
            'status': 'healthy' if not issues else 'warning',
            'issues': issues
        }


class FlowSystemMonitor:
    """Flow 시스템 전용 모니터"""

    def __init__(self):
        self.stats = {
            'plans_created': 0,
            'tasks_created': 0,
            'tasks_completed': 0,
            'api_calls': 0,
            'errors': 0
        }

    def track_api_call(self, api_name: str, success: bool):
        """API 호출 추적"""
        self.stats['api_calls'] += 1
        if not success:
            self.stats['errors'] += 1

    def track_plan_created(self):
        """플랜 생성 추적"""
        self.stats['plans_created'] += 1

    def track_task_created(self):
        """태스크 생성 추적"""
        self.stats['tasks_created'] += 1

    def track_task_completed(self):
        """태스크 완료 추적"""
        self.stats['tasks_completed'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Flow 시스템 통계"""
        return self.stats


class MonitoringDashboard:
    """통합 모니터링 대시보드"""

    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.flow_monitor = FlowSystemMonitor()

        # 컴포넌트별 상태
        self.components = {
            'flow_api': {'status': 'unknown', 'last_check': None},
            'repl_pool': {'status': 'unknown', 'last_check': None},
            'file_cache': {'status': 'unknown', 'last_check': None},
            'git': {'status': 'unknown', 'last_check': None}
        }

    def render_dashboard(self) -> str:
        """대시보드 렌더링"""
        system_status = self.system_monitor.get_current_status()
        flow_stats = self.flow_monitor.get_stats()

        dashboard = []
        dashboard.append("=" * 70)
        dashboard.append("📊 AI CODING BRAIN MCP - 시스템 모니터링 대시보드")
        dashboard.append("=" * 70)
        dashboard.append(f"⏰ 현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        dashboard.append("")

        # 시스템 리소스
        dashboard.append("🖥️ 시스템 리소스")
        dashboard.append("-" * 50)

        if 'current' in system_status and 'cpu' in system_status['current']:
            cpu = system_status['current']['cpu']
            dashboard.append(f"  CPU: {self._progress_bar(cpu['percent'])} {cpu['percent']:.1f}%")

        if 'current' in system_status and 'memory' in system_status['current']:
            mem = system_status['current']['memory']
            dashboard.append(f"  RAM: {self._progress_bar(mem['percent'])} {mem['used_mb']}MB / {mem['total_mb']}MB")

        if 'current' in system_status and 'disk' in system_status['current']:
            disk = system_status['current']['disk']
            dashboard.append(f"  Disk: {self._progress_bar(disk['percent'])} {disk['used_gb']}GB / {disk['total_gb']}GB")

        dashboard.append("")

        # Flow 시스템 통계
        dashboard.append("🧠 Flow 시스템")
        dashboard.append("-" * 50)
        dashboard.append(f"  플랜 생성: {flow_stats['plans_created']}개")
        dashboard.append(f"  태스크 생성: {flow_stats['tasks_created']}개")
        dashboard.append(f"  태스크 완료: {flow_stats['tasks_completed']}개")
        dashboard.append(f"  API 호출: {flow_stats['api_calls']}회")
        dashboard.append(f"  에러: {flow_stats['errors']}회")
        dashboard.append("")

        # 컴포넌트 상태
        dashboard.append("🔧 시스템 컴포넌트")
        dashboard.append("-" * 50)

        for name, status in self.components.items():
            icon = "🟢" if status['status'] == 'healthy' else "🔴" if status['status'] == 'error' else "⚪"
            dashboard.append(f"  {icon} {name}: {status['status']}")

        dashboard.append("")

        # 건강 상태
        health = system_status.get('healthy', {})
        if health.get('status') == 'healthy':
            dashboard.append("✅ 시스템 상태: 정상")
        else:
            dashboard.append("⚠️ 시스템 경고:")
            for issue in health.get('issues', []):
                dashboard.append(f"  • {issue}")

        dashboard.append("")
        dashboard.append("=" * 70)

        return "\n".join(dashboard)

    def _progress_bar(self, percent: float, width: int = 20) -> str:
        """프로그레스 바 생성"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def check_component(self, component: str) -> Dict[str, Any]:
        """컴포넌트 상태 체크"""
        try:
            if component == 'flow_api':
                # Flow API 체크 로직
                from .flow_api import get_flow_api
                api = get_flow_api()
                api.list_plans()
                status = 'healthy'
            elif component == 'repl_pool':
                # REPL Pool 체크 로직
                from .repl_pool import get_pool_stats
                stats = get_pool_stats()
                status = 'healthy' if stats.get('pool_size', 0) > 0 else 'error'
            elif component == 'file_cache':
                # File Cache 체크 로직
                from .file_cache import get_cache_stats
                stats = get_cache_stats()
                status = 'healthy'
            elif component == 'git':
                # Git 체크 로직
                import subprocess
                result = subprocess.run(['git', 'status'], capture_output=True)
                status = 'healthy' if result.returncode == 0 else 'error'
            else:
                status = 'unknown'

            self.components[component] = {
                'status': status,
                'last_check': datetime.now().isoformat()
            }

            return {'ok': True, 'status': status}

        except Exception as e:
            self.components[component] = {
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
            return {'ok': False, 'error': str(e)}

    def get_summary(self) -> Dict[str, Any]:
        """대시보드 요약 데이터"""
        return {
            'system': self.system_monitor.get_current_status(),
            'flow': self.flow_monitor.get_stats(),
            'components': self.components,
            'timestamp': datetime.now().isoformat()
        }


# 싱글톤 인스턴스
_dashboard = MonitoringDashboard()

def show_dashboard():
    """대시보드 표시"""
    print(_dashboard.render_dashboard())

def get_dashboard_data() -> Dict[str, Any]:
    """대시보드 데이터 반환"""
    return _dashboard.get_summary()

def check_system_health() -> Dict[str, Any]:
    """시스템 건강 상태 체크"""
    summary = _dashboard.get_summary()

    issues = []
    if summary['system'].get('healthy', {}).get('status') != 'healthy':
        issues.extend(summary['system']['healthy'].get('issues', []))

    for comp, status in summary['components'].items():
        if status['status'] == 'error':
            issues.append(f"{comp} 오류")

    return {
        'ok': len(issues) == 0,
        'status': 'healthy' if len(issues) == 0 else 'warning',
        'issues': issues
    }


# Export
__all__ = [
    'SystemMonitor',
    'FlowSystemMonitor',
    'MonitoringDashboard',
    'show_dashboard',
    'get_dashboard_data',
    'check_system_health'
]
