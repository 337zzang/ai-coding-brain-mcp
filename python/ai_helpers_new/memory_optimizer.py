"""
Memory Optimizer for AI Coding Brain MCP
메모리 시스템 최적화 및 개선 모듈
"""
import json
import os
import gc
import gzip
import shutil
import asyncio
import aiofiles
import threading
import weakref
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from collections import OrderedDict
import psutil

# 통합 로거 설정
log_dir = Path('.ai-brain/logs')
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'memory.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai-coding-brain-memory')


class JsonHelper:
    """JSON 처리 통합 유틸리티"""
    
    @staticmethod
    def safe_load(path: Union[str, Path], default=None) -> Dict[str, Any]:
        """안전한 JSON 로드 with 에러 처리"""
        try:
            path = Path(path)
            if not path.exists():
                logger.debug(f"파일 없음: {path}")
                return default or {}
            
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패 {path}: {e}")
            return default or {}
        except Exception as e:
            logger.error(f"JSON 로드 실패 {path}: {e}")
            return default or {}
    
    @staticmethod
    def safe_save(path: Union[str, Path], data: dict, backup: bool = True) -> bool:
        """안전한 JSON 저장 with 백업"""
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 백업 생성
            if backup and path.exists():
                backup_path = path.with_suffix(f'{path.suffix}.backup')
                shutil.copy(path, backup_path)
                logger.debug(f"백업 생성: {backup_path}")
            
            # 원자적 쓰기
            temp_path = path.with_suffix(f'{path.suffix}.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 원자적 이동
            temp_path.replace(path)
            logger.debug(f"JSON 저장 성공: {path}")
            return True
            
        except Exception as e:
            logger.error(f"JSON 저장 실패 {path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    @staticmethod
    def stream_load(path: Union[str, Path]):
        """대용량 JSON 스트리밍 로드"""
        try:
            import ijson
            path = Path(path)
            with open(path, 'rb') as f:
                parser = ijson.items(f, 'item')
                for item in parser:
                    yield item
        except ImportError:
            logger.warning("ijson 없음, 일반 로드 사용")
            data = JsonHelper.safe_load(path, [])
            for item in data:
                yield item


class SmartLRUCache:
    """개선된 LRU 캐시 with 자동 정리"""
    
    def __init__(self, max_size: int = 128, ttl: int = 3600, auto_cleanup: bool = True):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
        self._shutdown = False
        
        if auto_cleanup:
            self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """백그라운드 자동 정리 스레드"""
        def cleanup_worker():
            while not self._shutdown:
                try:
                    threading.Event().wait(self.ttl // 4)  # TTL의 1/4마다 실행
                    expired = self.clear_expired()
                    if expired > 0:
                        logger.debug(f"캐시 정리: {expired}개 항목 제거")
                except Exception as e:
                    logger.error(f"캐시 정리 에러: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True, name="cache-cleanup")
        self._cleanup_thread.start()
        logger.info("캐시 자동 정리 스레드 시작")
    
    def get(self, key: str, default=None):
        """캐시에서 값 가져오기"""
        with self.lock:
            if key in self.cache:
                # TTL 확인
                if datetime.now().timestamp() - self.timestamps[key] > self.ttl:
                    del self.cache[key]
                    del self.timestamps[key]
                    self.miss_count += 1
                    return default
                
                # LRU 업데이트
                self.cache.move_to_end(key)
                self.hit_count += 1
                return self.cache[key]
            
            self.miss_count += 1
            return default
    
    def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        with self.lock:
            # 기존 키 업데이트
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                # 크기 제한 확인
                if len(self.cache) >= self.max_size:
                    # 가장 오래된 항목 제거
                    oldest = next(iter(self.cache))
                    del self.cache[oldest]
                    del self.timestamps[oldest]
            
            self.cache[key] = value
            self.timestamps[key] = datetime.now().timestamp()
    
    def clear_expired(self) -> int:
        """만료된 항목 정리"""
        with self.lock:
            current_time = datetime.now().timestamp()
            expired_keys = [
                k for k, ts in self.timestamps.items()
                if current_time - ts > self.ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
                del self.timestamps[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': f"{hit_rate:.2f}%",
                'ttl': self.ttl
            }
    
    def shutdown(self):
        """캐시 종료"""
        self._shutdown = True
        logger.info("캐시 시스템 종료")


class MemoryOptimizedSync:
    """메모리 최적화된 동기화 시스템"""
    
    def __init__(self, base_path: str = '.ai-brain'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # WeakReference로 메모리 누수 방지
        self._session_cache = weakref.WeakValueDictionary()
        self._cache = SmartLRUCache(max_size=256, ttl=1800)
        self._lock = threading.RLock()
        
        # 메모리 모니터링
        self._monitor_thread = None
        self._start_memory_monitor()
    
    def _start_memory_monitor(self):
        """메모리 사용량 모니터링"""
        def monitor_worker():
            while not hasattr(self, '_shutdown'):
                try:
                    stats = self.get_memory_usage()
                    if stats['memory_mb'] > 500:  # 500MB 초과 시
                        logger.warning(f"메모리 사용량 높음: {stats['memory_mb']:.1f}MB")
                        self.cleanup_memory()
                    threading.Event().wait(60)  # 1분마다 체크
                except Exception as e:
                    logger.error(f"메모리 모니터 에러: {e}")
        
        self._monitor_thread = threading.Thread(target=monitor_worker, daemon=True, name="memory-monitor")
        self._monitor_thread.start()
    
    def cleanup_memory(self):
        """명시적 메모리 정리"""
        with self._lock:
            # 캐시 정리
            self._cache.clear_expired()
            
            # 약한 참조 정리
            self._session_cache.clear()
            
            # 가비지 컬렉션
            collected = gc.collect()
            logger.info(f"메모리 정리 완료: {collected}개 객체 수집")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """현재 메모리 사용량"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'cache_size': len(self._session_cache),
                'gc_objects': len(gc.get_objects()),
                'cache_stats': self._cache.get_stats()
            }
        except Exception as e:
            logger.error(f"메모리 사용량 조회 실패: {e}")
            return {}
    
    async def sync_flow_async(self, flow_data: Dict[str, Any]):
        """비동기 Flow 동기화"""
        tasks = [
            self._sync_plans_async(flow_data.get('plans', {})),
            self._sync_tasks_async(flow_data.get('tasks', {})),
            self._sync_stats_async(flow_data.get('stats', {}))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 에러 처리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"동기화 실패 [{i}]: {result}")
        
        return self._merge_sync_results(results)
    
    async def _sync_plans_async(self, plans: Dict):
        """플랜 비동기 동기화"""
        sync_path = self.base_path / 'flow' / 'plans.json'
        async with aiofiles.open(sync_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(plans, indent=2, ensure_ascii=False))
        return {'plans': len(plans)}
    
    async def _sync_tasks_async(self, tasks: Dict):
        """태스크 비동기 동기화"""
        sync_path = self.base_path / 'flow' / 'tasks.json'
        async with aiofiles.open(sync_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(tasks, indent=2, ensure_ascii=False))
        return {'tasks': len(tasks)}
    
    async def _sync_stats_async(self, stats: Dict):
        """통계 비동기 동기화"""
        sync_path = self.base_path / 'flow' / 'stats.json'
        async with aiofiles.open(sync_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(stats, indent=2, ensure_ascii=False))
        return {'stats': len(stats)}
    
    def _merge_sync_results(self, results: List) -> Dict:
        """동기화 결과 병합"""
        merged = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }
        
        for result in results:
            if isinstance(result, dict):
                merged['details'].update(result)
            else:
                merged['success'] = False
        
        return merged


class MemoryCompressor:
    """메모리 압축 시스템"""
    
    def __init__(self, base_path: str = '.ai-brain'):
        self.base_path = Path(base_path)
        self.archive_path = self.base_path / 'archive'
        self.archive_path.mkdir(parents=True, exist_ok=True)
    
    def compress_old_sessions(self, days: int = 30) -> Dict[str, Any]:
        """오래된 세션 압축"""
        cutoff = datetime.now() - timedelta(days=days)
        compressed_count = 0
        saved_bytes = 0
        
        session_path = self.base_path / 'claude_sessions'
        if not session_path.exists():
            return {'compressed': 0, 'saved_mb': 0}
        
        for session_file in session_path.glob('*.json'):
            # 수정 시간 확인
            mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
            if mtime < cutoff:
                original_size = session_file.stat().st_size
                
                # 압축
                compressed_path = self.archive_path / f"{session_file.stem}.json.gz"
                with open(session_file, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                compressed_size = compressed_path.stat().st_size
                saved_bytes += original_size - compressed_size
                
                # 원본 삭제
                session_file.unlink()
                compressed_count += 1
                
                logger.info(f"압축 완료: {session_file.name} ({original_size} → {compressed_size} bytes)")
        
        return {
            'compressed': compressed_count,
            'saved_mb': saved_bytes / 1024 / 1024,
            'archive_path': str(self.archive_path)
        }
    
    def decompress_session(self, session_id: str) -> Optional[Dict]:
        """압축된 세션 복원"""
        compressed_path = self.archive_path / f"{session_id}.json.gz"
        if not compressed_path.exists():
            return None
        
        try:
            with gzip.open(compressed_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"세션 압축 해제 실패 {session_id}: {e}")
            return None
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """압축 통계"""
        total_original = 0
        total_compressed = 0
        file_count = 0
        
        for gz_file in self.archive_path.glob('*.gz'):
            file_count += 1
            total_compressed += gz_file.stat().st_size
        
        # 원본 크기 추정 (평균 압축률 70% 가정)
        total_original = total_compressed * 3.3
        
        return {
            'archived_files': file_count,
            'total_size_mb': total_compressed / 1024 / 1024,
            'estimated_saved_mb': (total_original - total_compressed) / 1024 / 1024,
            'compression_ratio': f"{(1 - total_compressed/total_original)*100:.1f}%" if total_original > 0 else "0%"
        }


class EventDrivenMemory:
    """이벤트 기반 메모리 시스템"""
    
    def __init__(self):
        self.event_handlers = {}
        self.event_queue = asyncio.Queue()
        self.running = False
        
        # 기본 이벤트 핸들러 등록
        self.subscribe('session.created', self._on_session_created)
        self.subscribe('session.completed', self._on_session_completed)
        self.subscribe('memory.threshold', self._on_memory_threshold)
    
    def subscribe(self, event_type: str, handler):
        """이벤트 구독"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"이벤트 구독: {event_type}")
    
    async def emit(self, event_type: str, data: Any):
        """이벤트 발행"""
        await self.event_queue.put({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def start(self):
        """이벤트 처리 시작"""
        self.running = True
        logger.info("이벤트 기반 메모리 시스템 시작")
        
        while self.running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"이벤트 처리 에러: {e}")
    
    async def _process_event(self, event: Dict):
        """이벤트 처리"""
        event_type = event['type']
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"이벤트 핸들러 에러 [{event_type}]: {e}")
    
    async def _on_session_created(self, event: Dict):
        """세션 생성 이벤트 처리"""
        session_id = event['data'].get('session_id')
        logger.info(f"새 세션 생성: {session_id}")
        # 세션 초기화 로직
    
    async def _on_session_completed(self, event: Dict):
        """세션 완료 이벤트 처리"""
        session_id = event['data'].get('session_id')
        logger.info(f"세션 완료: {session_id}")
        # 세션 정리 및 압축
    
    async def _on_memory_threshold(self, event: Dict):
        """메모리 임계점 이벤트 처리"""
        usage = event['data'].get('usage_mb')
        logger.warning(f"메모리 임계점 도달: {usage}MB")
        # 긴급 메모리 정리


# 테스트 및 사용 예시
def test_memory_optimizer():
    """메모리 최적화 시스템 테스트"""
    print("=== 메모리 최적화 시스템 테스트 ===\n")
    
    # 1. JSON Helper 테스트
    print("1. JSON Helper 테스트:")
    test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
    test_path = Path('.ai-brain/test/test.json')
    
    if JsonHelper.safe_save(test_path, test_data):
        loaded = JsonHelper.safe_load(test_path)
        print(f"   ✓ JSON 저장/로드 성공: {loaded}")
    
    # 2. Smart LRU Cache 테스트
    print("\n2. Smart LRU Cache 테스트:")
    cache = SmartLRUCache(max_size=10, ttl=60)
    
    for i in range(15):
        cache.set(f"key_{i}", f"value_{i}")
    
    stats = cache.get_stats()
    print(f"   ✓ 캐시 상태: {stats}")
    
    # 3. Memory Optimizer 테스트
    print("\n3. Memory Optimizer 테스트:")
    optimizer = MemoryOptimizedSync()
    usage = optimizer.get_memory_usage()
    print(f"   ✓ 메모리 사용량: {usage.get('memory_mb', 0):.2f}MB")
    
    # 4. Compressor 테스트
    print("\n4. Memory Compressor 테스트:")
    compressor = MemoryCompressor()
    compression_stats = compressor.get_compression_stats()
    print(f"   ✓ 압축 통계: {compression_stats}")
    
    print("\n=== 테스트 완료 ===")
    
    # 정리
    cache.shutdown()
    return True


if __name__ == "__main__":
    # 로깅 레벨 설정
    logging.getLogger().setLevel(logging.DEBUG)
    
    # 테스트 실행
    test_memory_optimizer()