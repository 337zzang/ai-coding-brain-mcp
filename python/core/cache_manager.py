"""
캐시 관리 시스템 - 파일 변경 추적 및 자동 무효화
"""
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
import logging
from threading import Lock
from collections import defaultdict

logger = logging.getLogger(__name__)


class CacheManager:
    """중앙 집중식 캐시 관리자 - 파일 변경 추적 및 자동 무효화"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 캐시 메타데이터 파일
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        
        # 메모리 캐시
        self._cache: Dict[str, Any] = {}
        self._file_hashes: Dict[str, str] = {}  # 파일 경로 -> 해시
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)  # 캐시키 -> 의존 파일들
        
        # 스레드 안전성
        self._lock = Lock()
        
        # 설정
        self.ttl_seconds = 3600  # 기본 TTL 1시간
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        
        # 초기화
        self._load_metadata()
    
    def _load_metadata(self):
        """캐시 메타데이터 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self._file_hashes = data.get('file_hashes', {})
                    # dependencies는 set으로 변환
                    deps = data.get('dependencies', {})
                    self._dependencies = defaultdict(set)
                    for key, files in deps.items():
                        self._dependencies[key] = set(files)
            except Exception as e:
                logger.error(f"Failed to load cache metadata: {e}")
    
    def _save_metadata(self):
        """캐시 메타데이터 저장"""
        try:
            data = {
                'file_hashes': self._file_hashes,
                'dependencies': {k: list(v) for k, v in self._dependencies.items()},
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _calculate_file_hash(self, filepath: Path) -> Optional[str]:
        """파일의 해시 계산"""
        try:
            if not filepath.exists():
                return None
            
            # 작은 파일은 전체 해시, 큰 파일은 샘플링
            stat = filepath.stat()
            if stat.st_size < 1024 * 1024:  # 1MB 미만
                with open(filepath, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
            else:
                # 큰 파일은 처음, 중간, 끝 부분만 샘플링
                hasher = hashlib.md5()
                with open(filepath, 'rb') as f:
                    hasher.update(f.read(1024))  # 처음 1KB
                    f.seek(stat.st_size // 2)
                    hasher.update(f.read(1024))  # 중간 1KB
                    f.seek(-1024, 2)
                    hasher.update(f.read(1024))  # 마지막 1KB
                hasher.update(str(stat.st_mtime).encode())  # 수정 시간도 포함
                return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {filepath}: {e}")
            return None
    
    def _is_file_changed(self, filepath: Path) -> bool:
        """파일이 변경되었는지 확인"""
        filepath = Path(filepath).resolve()
        current_hash = self._calculate_file_hash(filepath)
        
        if current_hash is None:
            return True  # 파일이 없거나 읽을 수 없으면 변경된 것으로 간주
        
        stored_hash = self._file_hashes.get(str(filepath))
        if stored_hash != current_hash:
            self._file_hashes[str(filepath)] = current_hash
            return True
        
        return False
    
    def track_dependency(self, cache_key: str, filepath: Path):
        """캐시 항목이 의존하는 파일 추적"""
        with self._lock:
            filepath = Path(filepath).resolve()
            self._dependencies[cache_key].add(str(filepath))
            
            # 파일 해시 저장
            if str(filepath) not in self._file_hashes:
                hash_value = self._calculate_file_hash(filepath)
                if hash_value:
                    self._file_hashes[str(filepath)] = hash_value
    
    def check_invalidation(self, cache_key: str) -> bool:
        """캐시 항목이 무효화되어야 하는지 확인"""
        with self._lock:
            # 의존하는 파일들 확인
            dependent_files = self._dependencies.get(cache_key, set())
            
            for filepath in dependent_files:
                if self._is_file_changed(Path(filepath)):
                    logger.info(f"Cache key '{cache_key}' invalidated due to change in {filepath}")
                    return True
            
            return False
    
    def get(self, key: str, check_dependencies: bool = True) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self._lock:
            # 의존성 확인
            if check_dependencies and self.check_invalidation(key):
                self.invalidate(key)
                return None
            
            # 메모리 캐시 확인
            if key in self._cache:
                return self._cache[key]
            
            # 파일 캐시 확인
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # TTL 확인
                    if 'expires_at' in data:
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        if datetime.now(timezone.utc) > expires_at:
                            self.invalidate(key)
                            return None
                    
                    value = data.get('value')
                    self._cache[key] = value  # 메모리 캐시에 로드
                    return value
                except Exception as e:
                    logger.error(f"Failed to load cache {key}: {e}")
            
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            dependencies: Optional[List[Path]] = None):
        """캐시에 값 저장"""
        with self._lock:
            # 메모리 캐시에 저장
            self._cache[key] = value
            
            # 의존성 등록
            if dependencies:
                for filepath in dependencies:
                    self.track_dependency(key, filepath)
            
            # 파일에 저장
            cache_file = self.cache_dir / f"{key}.json"
            try:
                data = {
                    'value': value,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'expires_at': datetime.now(timezone.utc).timestamp() + (ttl or self.ttl_seconds)
                }
                
                with open(cache_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                # 메타데이터 저장
                self._save_metadata()
                
            except Exception as e:
                logger.error(f"Failed to save cache {key}: {e}")
    
    def invalidate(self, key: str):
        """특정 캐시 항목 무효화"""
        with self._lock:
            # 메모리 캐시에서 제거
            self._cache.pop(key, None)
            
            # 파일 캐시 제거
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
            
            # 의존성 정보 제거
            self._dependencies.pop(key, None)
            
            logger.info(f"Cache invalidated: {key}")
    
    def invalidate_by_file(self, filepath: Path) -> List[str]:
        """특정 파일에 의존하는 모든 캐시 무효화"""
        with self._lock:
            filepath = Path(filepath).resolve()
            invalidated = []
            
            # 파일이 변경되었는지 먼저 확인
            if not self._is_file_changed(filepath):
                return invalidated
            
            # 이 파일에 의존하는 모든 캐시 찾기
            for cache_key, dependencies in list(self._dependencies.items()):
                if str(filepath) in dependencies:
                    self.invalidate(cache_key)
                    invalidated.append(cache_key)
            
            # 메타데이터 저장
            self._save_metadata()
            
            return invalidated
    
    def clear_all(self):
        """모든 캐시 삭제"""
        with self._lock:
            # 메모리 캐시 클리어
            self._cache.clear()
            self._dependencies.clear()
            self._file_hashes.clear()
            
            # 파일 캐시 삭제
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file != self.metadata_file:
                    cache_file.unlink()
            
            # 메타데이터 저장
            self._save_metadata()
            
            logger.info("All cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self._lock:
            cache_files = list(self.cache_dir.glob("*.json"))
            cache_files = [f for f in cache_files if f != self.metadata_file]
            
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'memory_items': len(self._cache),
                'file_items': len(cache_files),
                'total_size_bytes': total_size,
                'tracked_files': len(self._file_hashes),
                'cache_keys_with_dependencies': len(self._dependencies),
                'cache_directory': str(self.cache_dir)
            }


# 전역 캐시 매니저 인스턴스
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_dir: Optional[Path] = None) -> CacheManager:
    """싱글톤 캐시 매니저 인스턴스 가져오기"""
    global _cache_manager
    
    if _cache_manager is None:
        if cache_dir is None:
            # 기본 캐시 디렉토리
            from python.path_utils import get_memory_path
            cache_dir = Path(get_memory_path("cache"))
        
        _cache_manager = CacheManager(cache_dir)
    
    return _cache_manager
