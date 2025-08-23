#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JSON REPL 메모리 설정 파일
대용량 처리를 위한 최적화 설정
"""

import psutil

# 시스템 메모리 기반 자동 계산
def calculate_optimal_settings():
    """시스템 메모리 기반 최적 설정 계산"""
    try:
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        
        # 보수적 설정 (사용 가능 메모리의 20%)
        conservative = {
            'MEMORY_THRESHOLD_MB': min(int(available_gb * 0.2 * 1024), 2048),
            'MAX_USER_VARS': min(int(available_gb * 2000), 20000),
            'MAX_HISTORY_SIZE': min(int(available_gb * 100), 1000),
            'GC_INTERVAL': 20
        }
        
        # 일반 설정 (사용 가능 메모리의 40%)
        normal = {
            'MEMORY_THRESHOLD_MB': min(int(available_gb * 0.4 * 1024), 4096),
            'MAX_USER_VARS': min(int(available_gb * 4000), 40000),
            'MAX_HISTORY_SIZE': min(int(available_gb * 200), 2000),
            'GC_INTERVAL': 30
        }
        
        # 대용량 처리 설정 (사용 가능 메모리의 60%)
        large = {
            'MEMORY_THRESHOLD_MB': min(int(available_gb * 0.6 * 1024), 8192),
            'MAX_USER_VARS': min(int(available_gb * 6000), 100000),
            'MAX_HISTORY_SIZE': min(int(available_gb * 500), 5000),
            'GC_INTERVAL': 50
        }
        
        return {
            'conservative': conservative,
            'normal': normal,
            'large': large
        }
    except:
        # psutil 사용 불가시 기본값
        return {
            'conservative': {
                'MEMORY_THRESHOLD_MB': 500,
                'MAX_USER_VARS': 5000,
                'MAX_HISTORY_SIZE': 500,
                'GC_INTERVAL': 20
            },
            'normal': {
                'MEMORY_THRESHOLD_MB': 1000,
                'MAX_USER_VARS': 10000,
                'MAX_HISTORY_SIZE': 1000,
                'GC_INTERVAL': 30
            },
            'large': {
                'MEMORY_THRESHOLD_MB': 2000,
                'MAX_USER_VARS': 20000,
                'MAX_HISTORY_SIZE': 2000,
                'GC_INTERVAL': 50
            }
        }

# 프로파일 선택 (conservative, normal, large)
PROFILE = 'large'  # 대용량 처리 모드

# 설정 로드
settings = calculate_optimal_settings()[PROFILE]

# === 메모리 최적화 설정 ===
MAX_USER_VARS = settings['MAX_USER_VARS']           # 사용자 변수 최대 개수
MAX_HISTORY_SIZE = settings['MAX_HISTORY_SIZE']     # 히스토리 최대 개수
MEMORY_THRESHOLD_MB = settings['MEMORY_THRESHOLD_MB']  # 메모리 임계값 (MB)
GC_INTERVAL = settings['GC_INTERVAL']               # 가비지 컬렉션 주기
CODE_PREVIEW_LENGTH = 100                           # 히스토리 코드 미리보기 길이 (확대)

# 추가 최적화 옵션
ENABLE_AGGRESSIVE_CLEANUP = False  # 공격적 메모리 정리 (성능 저하 가능)
ENABLE_MEMORY_PROFILING = True     # 메모리 프로파일링 활성화
COMPRESS_LARGE_VARS = True          # 큰 변수 자동 압축
LARGE_VAR_THRESHOLD_MB = 10        # 압축 대상 변수 크기 (MB)

def print_current_settings():
    """현재 설정 출력"""
    print(f"📊 JSON REPL 메모리 설정 (프로파일: {PROFILE})")
    print("=" * 60)
    print(f"  MAX_USER_VARS: {MAX_USER_VARS:,}개")
    print(f"  MAX_HISTORY_SIZE: {MAX_HISTORY_SIZE:,}개")
    print(f"  MEMORY_THRESHOLD_MB: {MEMORY_THRESHOLD_MB:,}MB")
    print(f"  GC_INTERVAL: {GC_INTERVAL}회")
    print(f"  CODE_PREVIEW_LENGTH: {CODE_PREVIEW_LENGTH}자")
    print(f"  COMPRESS_LARGE_VARS: {COMPRESS_LARGE_VARS}")
    
    if psutil:
        mem = psutil.virtual_memory()
        print(f"\n💾 시스템 메모리 상태:")
        print(f"  총 메모리: {mem.total / (1024**3):.1f}GB")
        print(f"  사용 가능: {mem.available / (1024**3):.1f}GB")
        print(f"  임계값/사용가능: {MEMORY_THRESHOLD_MB / (mem.available / (1024**2)) * 100:.1f}%")

if __name__ == "__main__":
    print_current_settings()
    
    print("\n🎯 사용 가능한 프로파일:")
    all_settings = calculate_optimal_settings()
    for profile_name, profile_settings in all_settings.items():
        print(f"\n  [{profile_name}]")
        for key, value in profile_settings.items():
            print(f"    {key}: {value:,}")