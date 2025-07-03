"""
간단한 작업 추적 시스템
작업 실행 통계를 수집하고 저장
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time


class SimpleOperationTracker:
    """작업 실행 추적 및 통계 관리"""
    
    def __init__(self, log_file: str = "memory/tracking.json"):
        """
        Args:
            log_file: 추적 데이터 저장 파일 경로
        """
        self.log_file = log_file
        self.current_session = {
            'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now().isoformat(),
            'operations': []
        }
        self._ensure_file_exists()
        self._start_time = {}  # 작업별 시작 시간 추적
        
    def _ensure_file_exists(self):
        """추적 파일 존재 확인 및 생성"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        if not os.path.exists(self.log_file):
            initial_data = {
                'sessions': [],
                'total_stats': {
                    'total_operations': 0,
                    'total_errors': 0,
                    'total_duration_seconds': 0,
                    'operation_counts': {},
                    'error_counts': {},
                    'first_tracked': datetime.now().isoformat()
                }
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict[str, Any]:
        """추적 데이터 로드"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 추적 데이터 로드 실패: {str(e)}")
            return {'sessions': [], 'total_stats': {}}
    
    def _save_data(self, data: Dict[str, Any]):
        """추적 데이터 저장"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 추적 데이터 저장 실패: {str(e)}")
    
    def start_operation(self, operation_type: str, operation_name: str, 
                       metadata: Optional[Dict] = None):
        """작업 시작 추적"""
        key = f"{operation_type}:{operation_name}"
        self._start_time[key] = time.time()
        
        # 메타데이터 로깅 (선택적)
        if metadata:
            print(f"🔄 작업 시작: {operation_type} - {operation_name}")
    
    def track_operation(self, operation_type: str, operation_name: str, 
                       success: bool = True, duration: Optional[float] = None,
                       error: Optional[str] = None, metadata: Optional[Dict] = None):
        """작업 실행 추적"""
        key = f"{operation_type}:{operation_name}"
        
        # 시간 계산
        if duration is None and key in self._start_time:
            duration = time.time() - self._start_time.pop(key, time.time())
        elif duration is None:
            duration = 0
        
        # 작업 기록
        operation_record = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'name': operation_name,
            'success': success,
            'duration_seconds': round(duration, 3),
            'error': error,
            'metadata': metadata or {}
        }
        
        self.current_session['operations'].append(operation_record)
        
        # 즉시 통계 업데이트 (성능을 위해 주기적으로 저장)
        if len(self.current_session['operations']) % 10 == 0:
            self._update_total_stats()
    
    def _update_total_stats(self):
        """전체 통계 업데이트"""
        data = self._load_data()
        stats = data.get('total_stats', {})
        
        for op in self.current_session['operations'][-10:]:  # 최근 10개만 처리
            # 전체 카운트
            stats['total_operations'] = stats.get('total_operations', 0) + 1
            if not op['success']:
                stats['total_errors'] = stats.get('total_errors', 0) + 1
            
            # 작업별 카운트
            op_key = f"{op['type']}:{op['name']}"
            if 'operation_counts' not in stats:
                stats['operation_counts'] = {}
            stats['operation_counts'][op_key] = stats['operation_counts'].get(op_key, 0) + 1
            
            # 에러 카운트
            if not op['success'] and op.get('error'):
                if 'error_counts' not in stats:
                    stats['error_counts'] = {}
                stats['error_counts'][op_key] = stats['error_counts'].get(op_key, 0) + 1
            
            # 총 실행 시간
            stats['total_duration_seconds'] = stats.get('total_duration_seconds', 0) + op['duration_seconds']
        
        data['total_stats'] = stats
        self._save_data(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        data = self._load_data()
        stats = data.get('total_stats', {})
        
        # 성공률 계산
        total_ops = stats.get('total_operations', 0)
        total_errors = stats.get('total_errors', 0)
        success_rate = ((total_ops - total_errors) / total_ops * 100) if total_ops > 0 else 0
        
        # 가장 많이 사용된 작업
        op_counts = stats.get('operation_counts', {})
        top_operations = sorted(op_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 가장 많이 실패한 작업
        error_counts = stats.get('error_counts', {})
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_operations': total_ops,
            'total_errors': total_errors,
            'success_rate': round(success_rate, 1),
            'total_duration_seconds': round(stats.get('total_duration_seconds', 0), 2),
            'average_duration': round(stats.get('total_duration_seconds', 0) / total_ops, 3) if total_ops > 0 else 0,
            'top_operations': top_operations,
            'top_errors': top_errors,
            'tracking_since': stats.get('first_tracked', 'N/A'),
            'current_session_ops': len(self.current_session['operations'])
        }
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """일일 통계 조회"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        data = self._load_data()
        daily_ops = []
        
        # 모든 세션에서 해당 날짜의 작업 수집
        for session in data.get('sessions', []):
            for op in session.get('operations', []):
                if op['timestamp'].startswith(date):
                    daily_ops.append(op)
        
        # 현재 세션에서도 수집
        for op in self.current_session['operations']:
            if op['timestamp'].startswith(date):
                daily_ops.append(op)
        
        # 통계 계산
        total = len(daily_ops)
        errors = len([op for op in daily_ops if not op['success']])
        total_duration = sum(op['duration_seconds'] for op in daily_ops)
        
        # 시간대별 분포
        hourly_dist = defaultdict(int)
        for op in daily_ops:
            hour = datetime.fromisoformat(op['timestamp']).hour
            hourly_dist[hour] += 1
        
        return {
            'date': date,
            'total_operations': total,
            'total_errors': errors,
            'success_rate': round((total - errors) / total * 100, 1) if total > 0 else 0,
            'total_duration_seconds': round(total_duration, 2),
            'average_duration': round(total_duration / total, 3) if total > 0 else 0,
            'hourly_distribution': dict(hourly_dist),
            'peak_hour': max(hourly_dist.items(), key=lambda x: x[1])[0] if hourly_dist else None
        }
    
    def save_session(self):
        """현재 세션 저장"""
        if not self.current_session['operations']:
            return
        
        self.current_session['end_time'] = datetime.now().isoformat()
        
        data = self._load_data()
        data['sessions'].append(self.current_session)
        
        # 최근 100개 세션만 유지 (메모리 관리)
        if len(data['sessions']) > 100:
            data['sessions'] = data['sessions'][-100:]
        
        # 최종 통계 업데이트
        self._update_total_stats()
        
        self._save_data(data)
        print(f"💾 추적 세션 저장 완료: {len(self.current_session['operations'])} 작업")
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 작업 조회"""
        return self.current_session['operations'][-limit:]
    
    def print_summary(self):
        """통계 요약 출력"""
        stats = self.get_statistics()
        
        print("\n📊 작업 추적 통계 요약")
        print("=" * 50)
        print(f"총 작업 수: {stats['total_operations']}")
        print(f"총 오류 수: {stats['total_errors']}")
        print(f"성공률: {stats['success_rate']}%")
        print(f"총 실행 시간: {stats['total_duration_seconds']}초")
        print(f"평균 실행 시간: {stats['average_duration']}초")
        
        if stats['top_operations']:
            print("\n🔝 가장 많이 사용된 작업:")
            for op, count in stats['top_operations']:
                print(f"  - {op}: {count}회")
        
        if stats['top_errors']:
            print("\n❌ 가장 많이 실패한 작업:")
            for op, count in stats['top_errors']:
                print(f"  - {op}: {count}회")
        
        print(f"\n📅 추적 시작: {stats['tracking_since']}")
        print(f"🔄 현재 세션 작업: {stats['current_session_ops']}개")


# 전역 추적기 인스턴스
_global_tracker = None


def get_tracker() -> SimpleOperationTracker:
    """전역 추적기 인스턴스 반환"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = SimpleOperationTracker()
    return _global_tracker


# 편의 함수들
def track(operation_type: str, operation_name: str, **kwargs):
    """작업 추적 (편의 함수)"""
    tracker = get_tracker()
    tracker.track_operation(operation_type, operation_name, **kwargs)


def start_tracking(operation_type: str, operation_name: str, **kwargs):
    """작업 시작 추적 (편의 함수)"""
    tracker = get_tracker()
    tracker.start_operation(operation_type, operation_name, **kwargs)


def end_tracking(operation_type: str, operation_name: str, success: bool = True, **kwargs):
    """작업 종료 추적 (편의 함수)"""
    tracker = get_tracker()
    tracker.track_operation(operation_type, operation_name, success=success, **kwargs)


def print_stats():
    """통계 출력 (편의 함수)"""
    tracker = get_tracker()
    tracker.print_summary()


# 데코레이터
def track_operation_decorator(operation_type: str):
    """작업 추적 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            operation_name = func.__name__
            tracker = get_tracker()
            
            start_time = time.time()
            success = True
            error = None
            result = None
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                tracker.track_operation(
                    operation_type, 
                    operation_name,
                    success=success,
                    duration=duration,
                    error=error
                )
            
            return result
        
        return wrapper
    return decorator


# 사용 예제
if __name__ == "__main__":
    # 추적기 테스트
    tracker = SimpleOperationTracker()
    
    # 몇 가지 작업 추적
    tracker.track_operation("file", "create", success=True, duration=0.5)
    tracker.track_operation("file", "read", success=True, duration=0.1)
    tracker.track_operation("code", "parse", success=False, duration=1.2, error="SyntaxError")
    tracker.track_operation("git", "commit", success=True, duration=0.8)
    
    # 통계 출력
    tracker.print_summary()
    
    # 세션 저장
    tracker.save_session()
