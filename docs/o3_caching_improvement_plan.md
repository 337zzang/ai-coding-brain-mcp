
# o3 제안 기반 캐싱 시스템 개선

## 문제점
- 파일 수정 작업이 캐싱되어 혼란 발생
- 사용자가 변경사항을 확인하기 어려움

## o3의 핵심 제안
1. 파일 작업은 캐싱에서 제외
2. 캐시 무효화 메커니즘
3. 해시 기반 변경 감지
4. 명시적 사용자 알림

## 구현 계획

## 📋 즉시 적용 가능한 개선사항

### 1단계: Quick Fix (즉시 적용)
- core.py의 track_execution 데코레이터 수정
- NO_CACHE_FUNCTIONS 목록 추가
- 파일 작업 함수들 캐싱 제외

### 2단계: 사용자 피드백 개선
- 캐시 사용 시 명시적 메시지 출력
- 파일 수정 시 변경 확인 메시지
- clear_cache() 사용법 안내

### 3단계: 파일 변경 감지 시스템
- FileChangeDetector 클래스 구현
- 해시 기반 변경 확인
- 자동 캐시 무효화

### 4단계: 사용자 인터페이스
- 캐시 상태 확인 명령
- 선택적 캐싱 on/off
- 캐시 통계 대시보드

## 📊 구현 우선순위
1. **긴급**: 파일 작업 함수 캐싱 제외 (1일)
2. **중요**: 명시적 피드백 시스템 (2일)
3. **개선**: 해시 기반 검증 (3일)
4. **향상**: 사용자 인터페이스 (1주)

## 💡 o3의 통찰력
- 파일 작업에 캐싱은 부적절
- 사용자에게 투명성 제공이 핵심
- 자동 무효화로 정확성 보장
- 제어권을 사용자에게


## Quick Fix 코드

# python/ai_helpers_v2/core.py 수정안

# 라인 69 근처의 track_execution 데코레이터 수정
NO_CACHE_FUNCTIONS = {
    'replace_block', 'create_file', 'write_file', 
    'append_to_file', 'git_add', 'git_commit',
    'git_push', 'delete_file', 'move_file'
}

def track_execution(func: Callable) -> Callable:
    """실행 추적 데코레이터 - 개선된 버전"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()

        # 파일/Git 작업은 캐싱하지 않음
        if func_name in NO_CACHE_FUNCTIONS:
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                protocol.track(func_name, args, kwargs, result, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                protocol.track(func_name, args, kwargs, None, duration)
                raise

        # 기존 캐싱 로직 (다른 함수들용)
        cache_key = protocol.get_cache_key(func_name, args, kwargs)
        cached_result = protocol.get_cached(cache_key)

        if cached_result is not None:
            # 캐시 사용 시 사용자에게 알림
            if os.getenv('SHOW_CACHE_INFO', '').lower() == 'true':
                print(f"📦 Using cached result for {func_name}")
            protocol.track(func_name, args, kwargs, cached_result, 0.0)
            return cached_result

        # ... 나머지 기존 코드


생성일: 2025-01-18
