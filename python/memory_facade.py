#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧠 Smart Memory Management Facade
실시간 메모리 모니터링과 자동 정리 시스템
"""

import sys
import gc
import psutil
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

class MemoryManager:
    """스마트 메모리 관리자"""
    
    def __init__(self):
        # 메모리 임계값 설정 (GB 단위)
        self.MEMORY_WARNING_THRESHOLD = 70  # 70% 사용 시 경고
        self.MEMORY_CRITICAL_THRESHOLD = 85  # 85% 사용 시 강제 정리
        self.MEMORY_LIMIT_GB = 16  # 최대 16GB 사용 (대폭 증가)
        
        # 변수 관리 설정 - 대용량 처리 가능하도록 대폭 증가
        self.MAX_VARIABLES = 1000  # 변수 1000개까지 허용 (기존 500개에서 증가)
        self.MAX_VAR_SIZE_MB = 1024  # 변수당 1GB까지 (기존 50MB에서 대폭 증가)
        
        # 통계
        self.stats = {
            'total_executions': 0,
            'gc_runs': 0,
            'memory_peaks': [],
            'last_gc_time': None
        }
        
        # 공유 변수 저장소
        self.shared_variables = {}
        self.variable_access_time = {}  # LRU 캐시용
    
    def get_memory_status(self) -> Dict[str, Any]:
        """현재 메모리 상태 조회"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        # MB 단위로 변환
        used_mb = memory_info.rss / 1024 / 1024
        available_mb = system_memory.available / 1024 / 1024
        total_mb = system_memory.total / 1024 / 1024
        percent = system_memory.percent
        
        return {
            'used_mb': round(used_mb, 2),
            'available_mb': round(available_mb, 2),
            'total_mb': round(total_mb, 2),
            'percent_used': percent,
            'variables_count': len(self.shared_variables),
            'warning': percent > self.MEMORY_WARNING_THRESHOLD,
            'critical': percent > self.MEMORY_CRITICAL_THRESHOLD
        }
    
    def should_clean_memory(self) -> bool:
        """메모리 정리가 필요한지 확인"""
        status = self.get_memory_status()
        
        # 임계값 초과 시
        if status['critical']:
            return True
        
        # 변수 개수 초과 시
        if status['variables_count'] > self.MAX_VARIABLES * 0.9:
            return True
        
        # 사용량이 제한 초과 시
        if status['used_mb'] > self.MEMORY_LIMIT_GB * 1024:
            return True
        
        return False
    
    def clean_memory(self, force: bool = False) -> Dict[str, Any]:
        """메모리 정리 수행"""
        before = self.get_memory_status()
        
        cleaned_vars = 0
        
        # 1. 큰 변수 정리 (50MB 초과)
        for key in list(self.shared_variables.keys()):
            try:
                size_mb = sys.getsizeof(self.shared_variables[key]) / 1024 / 1024
                if size_mb > self.MAX_VAR_SIZE_MB:
                    del self.shared_variables[key]
                    cleaned_vars += 1
            except:
                pass
        
        # 2. LRU 기반 오래된 변수 정리
        if len(self.shared_variables) > self.MAX_VARIABLES * 0.7:
            # 접근 시간 기준 정렬
            sorted_vars = sorted(
                self.variable_access_time.items(),
                key=lambda x: x[1]
            )
            
            # 오래된 30% 삭제
            to_remove = int(len(sorted_vars) * 0.3)
            for key, _ in sorted_vars[:to_remove]:
                if key in self.shared_variables:
                    del self.shared_variables[key]
                    cleaned_vars += 1
        
        # 3. 가비지 컬렉션 실행
        gc.collect()
        self.stats['gc_runs'] += 1
        self.stats['last_gc_time'] = datetime.now().isoformat()
        
        after = self.get_memory_status()
        
        return {
            'before': before,
            'after': after,
            'cleaned_variables': cleaned_vars,
            'memory_freed_mb': round(before['used_mb'] - after['used_mb'], 2),
            'gc_runs': self.stats['gc_runs']
        }
    
    def set_variable(self, key: str, value: Any) -> Dict[str, Any]:
        """변수 저장 with 메모리 체크"""
        # 크기 체크
        size_mb = sys.getsizeof(value) / 1024 / 1024
        
        if size_mb > self.MAX_VAR_SIZE_MB:
            return {
                'ok': False,
                'error': f'Variable too large: {size_mb:.2f}MB (max: {self.MAX_VAR_SIZE_MB}MB)'
            }
        
        # 메모리 체크
        if self.should_clean_memory():
            self.clean_memory()
        
        # 저장
        self.shared_variables[key] = value
        self.variable_access_time[key] = time.time()
        
        return {
            'ok': True,
            'key': key,
            'size_mb': round(size_mb, 2),
            'total_vars': len(self.shared_variables)
        }
    
    def get_variable(self, key: str) -> Any:
        """변수 조회 with LRU 업데이트"""
        if key in self.shared_variables:
            self.variable_access_time[key] = time.time()
            return self.shared_variables[key]
        return None

# 전역 메모리 매니저
MEMORY_MANAGER = MemoryManager()

def execute_code_with_memory_check(code: str) -> Dict[str, Any]:
    """메모리 체크가 포함된 코드 실행"""
    
    # 실행 전 메모리 상태
    before_status = MEMORY_MANAGER.get_memory_status()
    MEMORY_MANAGER.stats['total_executions'] += 1
    
    # stdout에 메모리 상태 출력
    print(f"[MEM] 실행 전: {before_status['used_mb']:.1f}MB 사용 중 ({before_status['percent_used']:.1f}%)")
    print(f"[MEM] 변수: {before_status['variables_count']}개")
    
    # 메모리 임계값 체크
    if before_status['critical']:
        print("[MEM] ⚠️ 메모리 임계값 초과! 자동 정리 시작...")
        clean_result = MEMORY_MANAGER.clean_memory(force=True)
        print(f"[MEM] ✅ 정리 완료: {clean_result['memory_freed_mb']:.1f}MB 해제")
    
    # 실제 코드 실행
    try:
        namespace = {
            '__builtins__': __builtins__,
            'mem': MEMORY_MANAGER,  # 메모리 매니저 접근 제공
            'set_var': MEMORY_MANAGER.set_variable,
            'get_var': MEMORY_MANAGER.get_variable,
        }
        
        exec(code, namespace)
        
        # 실행 후 메모리 상태
        after_status = MEMORY_MANAGER.get_memory_status()
        memory_delta = after_status['used_mb'] - before_status['used_mb']
        
        # 메모리 증가량이 크면 경고
        if memory_delta > 100:  # 100MB 이상 증가
            print(f"[MEM] ⚠️ 메모리 급증: +{memory_delta:.1f}MB")
        
        print(f"[MEM] 실행 후: {after_status['used_mb']:.1f}MB ({after_status['percent_used']:.1f}%)")
        
        # 피크 기록
        MEMORY_MANAGER.stats['memory_peaks'].append({
            'time': datetime.now().isoformat(),
            'used_mb': after_status['used_mb']
        })
        
        # 최근 10개 피크만 유지
        if len(MEMORY_MANAGER.stats['memory_peaks']) > 10:
            MEMORY_MANAGER.stats['memory_peaks'] = MEMORY_MANAGER.stats['memory_peaks'][-10:]
        
        return {
            'ok': True,
            'memory': {
                'before': before_status,
                'after': after_status,
                'delta_mb': round(memory_delta, 2)
            },
            'namespace': {k: v for k, v in namespace.items() if not k.startswith('__')}
        }
        
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'memory': MEMORY_MANAGER.get_memory_status()
        }

def get_memory_report() -> str:
    """메모리 상태 리포트 생성"""
    status = MEMORY_MANAGER.get_memory_status()
    stats = MEMORY_MANAGER.stats
    
    report = f"""
📊 메모리 상태 리포트
{'=' * 40}
현재 사용: {status['used_mb']:.1f}MB / {status['total_mb']:.1f}MB ({status['percent_used']:.1f}%)
사용 가능: {status['available_mb']:.1f}MB
변수 개수: {status['variables_count']} / {MEMORY_MANAGER.MAX_VARIABLES}

📈 통계
- 총 실행 횟수: {stats['total_executions']}
- GC 실행 횟수: {stats['gc_runs']}
- 마지막 GC: {stats['last_gc_time'] or 'N/A'}

⚠️ 상태: {'🔴 위험' if status['critical'] else '🟡 주의' if status['warning'] else '🟢 정상'}
"""
    
    if stats['memory_peaks']:
        report += "\n📊 최근 메모리 피크:\n"
        for peak in stats['memory_peaks'][-5:]:
            report += f"  - {peak['time']}: {peak['used_mb']:.1f}MB\n"
    
    return report

# Facade 함수들
def mem_status():
    """간단한 메모리 상태 확인"""
    return MEMORY_MANAGER.get_memory_status()

def mem_clean():
    """수동 메모리 정리"""
    return MEMORY_MANAGER.clean_memory()

def mem_report():
    """메모리 리포트 출력"""
    print(get_memory_report())

if __name__ == "__main__":
    # 테스트
    print("Memory Management Facade Initialized")
    print(get_memory_report())