# 캐싱 시스템 개선 구현안
# Based on o3's suggestions
# 생성일: 2025-01-18


# 개선안 1: 캐싱 제외 함수 목록
NO_CACHE_FUNCTIONS = [
    'replace_block',
    'create_file', 
    'write_file',
    'append_to_file',
    'git_add',
    'git_commit'
]

def track_execution(func: Callable) -> Callable:
    """개선된 실행 추적 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__

        # 파일 수정 작업은 캐싱하지 않음
        if func_name in NO_CACHE_FUNCTIONS:
            print(f"🔄 {func_name}: 캐싱 없이 실행")
            return func(*args, **kwargs)

        # 캐시 확인
        cache_key = protocol.get_cache_key(func_name, args, kwargs)
        cached_result = protocol.get_cached(cache_key)

        if cached_result is not None:
            print(f"📦 {func_name}: 캐시된 결과 사용")
            return cached_result

        # 실제 실행
        result = func(*args, **kwargs)

        # 빠른 작업만 캐싱
        if duration < 1.0:
            protocol.set_cache(cache_key, result)
            print(f"💾 {func_name}: 결과 캐싱됨")

        return result
    return wrapper

# 개선안 2: 파일 변경 감지
import hashlib

class FileChangeDetector:
    def __init__(self):
        self.file_hashes = {}

    def get_file_hash(self, filepath: str) -> str:
        """파일의 MD5 해시 계산"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def has_changed(self, filepath: str) -> bool:
        """파일 변경 여부 확인"""
        current_hash = self.get_file_hash(filepath)
        prev_hash = self.file_hashes.get(filepath)
        self.file_hashes[filepath] = current_hash
        return prev_hash is not None and prev_hash != current_hash

    def invalidate_cache_for_file(self, filepath: str):
        """파일 관련 캐시 무효화"""
        # 파일 경로를 포함하는 모든 캐시 키 찾아서 삭제
        keys_to_remove = []
        for key in protocol.cache:
            if filepath in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del protocol.cache[key]
            print(f"🗑️ 캐시 무효화: {key}")

# 개선안 3: 사용자 알림 개선
def replace_block_improved(filepath: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """개선된 replace_block - 명시적 피드백 제공"""
    print(f"📝 파일 수정 중: {filepath}")

    # 변경 전 해시
    detector = FileChangeDetector()
    before_hash = detector.get_file_hash(filepath)

    # 실제 수정 작업
    result = original_replace_block(filepath, old_code, new_code)

    # 변경 확인
    if result['success']:
        after_hash = detector.get_file_hash(filepath)
        if before_hash != after_hash:
            print(f"✅ 파일 수정 완료! (해시 변경 확인)")
            print(f"   변경 전: {before_hash[:8]}...")
            print(f"   변경 후: {after_hash[:8]}...")

            # 관련 캐시 무효화
            detector.invalidate_cache_for_file(filepath)
        else:
            print("⚠️ 파일 내용이 변경되지 않았습니다.")

    return result
