# Flow 시스템 성능 분석 보고서

생성일: 2025-07-23T00:43:18.130835
분석 도구: o3 (high effort)

## 분석 결과

1. 병목 지점 정리

┌──────────────┬────────────────────────────────────────────────────────────┐
│ 구간         │ 현재 동작                                                │
├──────────────┼────────────────────────────────────────────────────────────┤
│ flows 프로퍼티│ 접근할 때마다 _sync_flows_from_service()                  │
│              │ – 전체 JSON 다시 로드, File I/O                           │
│              │ – dict → Flow 변환 반복                                   │
├──────────────┼────────────────────────────────────────────────────────────┤
│ JsonFlowRepo │ save() → load_all() → _load_from_disk()                   │
│              │ – 캐시가 있어도 파일 쓰기 뒤에 무효화 됨 → 다음 호출 때   │
│              │   다시 전체 로드                                          │
│              │ – save_all() 은 매번 전체 JSON 파일 백-업 및 재-쓰기       │
├──────────────┼────────────────────────────────────────────────────────────┤
│ 데이터 변환   │ _load_from_disk : dict → Flow                            │
│              │ save_all          : Flow → dict                           │
│              │ load_all          : 깊은 복사(copy())                     │
└──────────────┴────────────────────────────────────────────────────────────┘

이 구조 때문에  
 • 호출 한 번마다 O(N) I/O · JSON 파싱 · 직렬화  
 • N(Flow 수) × K(호출 횟수) 만큼 중복 비용 발생  
 • 파일 크기가 커질수록 save/backup 시간 선형 증가  

2. 최적화 목표

A. “읽기” : flows 프로퍼티가 자주 호출돼도 디스크 접근 0 ~ 1 회  
B. “쓰기” : 단일 Flow 저장 시 전체 JSON 재-쓰기를 피하거나 최소화  
C. 데이터 변환 / 깊은 복사 제거  
D. 백업∙동기화는 필요한 시점에만 수행

3. 개선 방안

─────────────────────────────────────────────────────────────────────────
3-1. 캐싱 + TTL/버전 체크
─────────────────────────────────────────────────────────────────────────
class FlowService:
    _flows_cache: Dict[str, Flow] = {}
    _last_synced: float = 0
    _sync_interval = 5          # seconds or use etag/time-stamp

    @property
    def flows(self) -> Mapping[str, Flow]:
        now = time.time()
        if not self._flows_cache or now - self._last_synced > self._sync_interval:
            self._sync_flows_from_service()           # ← 실제 동기화
            self._last_synced = now
        return self._flows_cache                     # 깊은 복사 X

✓ flows 접근 10 만 번 → 디스크 1 ~ 2 회  
✓ 필요 시 force_refresh() 제공

─────────────────────────────────────────────────────────────────────────
3-2. JsonFlowRepository 구조 개선
─────────────────────────────────────────────────────────────────────────
(1) 읽기 캐시 고정
    • _cache 는 최초 1회만 채우고, save/flush 가 끝난 뒤 직접 갱신  
    • load_all() 에서 copy() 대신 MappingProxyType 반환해 불변성을 보장  
      (깊은 복사 제거):

from types import MappingProxyType
def load_all(self) -> Mapping[str, Flow]:
    if self._cache is None:
        self._cache = self._load_from_disk()
    return MappingProxyType(self._cache)

(2) Dirty-set & 지연 플러시
    • 메모리 캐시만 갱신하고 실제 파일 쓰기는
      ‑ 명시적 flush()  
      ‑ 일정 주기 background-thread  
      ‑ contextmanager (__enter__/__exit__) 중 선택

class JsonFlowRepository:
    _dirty: set[str] = set()

    def save(self, flow: Flow, flush: bool = False) -> None:
        if self._cache is None:
            self.load_all()           # 캐시 확보
        self._cache[flow.id] = flow
        self._dirty.add(flow.id)
        if flush:
            self.flush()

    def flush(self) -> None:
        if not self._dirty:
            return
        self._rewrite_partial()
        self._dirty.clear()

(3) 부분 재-쓰기(_rewrite_partial)
    방법 ① Flow 단위 파일 분리
         ./flows/{flow_id}.json  로 저장  
         • 저장/백업 시 O(1) I/O  
         • load_all 는 glob() 으로 병렬 파싱 가능
    방법 ② JSONL(Newline-delimited)
         flows.jsonl 마지막에 {"id":…, "op":"upsert", ...} append  
         → flush 시에는 append 만, 주기적으로 compaction
    방법 ③ SQLite/Key-Value(DBM, TinyDB 등)
         update flows set blob=? where id=?  
         → 가장 단순하면서 신뢰성 높음

▶ 간단한 예 – “폴더 분리” 방식

def _path(self, flow_id): return self.base / f"{flow_id}.json"

def save(self, flow: Flow, flush=True):
    with open(self._path(flow.id), "w") as f:
        json.dump(flow.to_dict(), f, indent=2)
    self._cache[flow.id] = flow     # 캐시 유지
    if flush and self._enable_backup:
        self._backup_file(self._path(flow.id))

전체 flows.json 을 다시 쓰지 않으므로 시간 복잡도 O(1).

(4) 백업 최적화
    • 파일 전체 백업 대신 changed-file 백업  
    • 보존 주기는 날짜/버전으로 제한 (예: 하루 1회)  
    • gzip 압축해 디스크 사용량 ↓

─────────────────────────────────────────────────────────────────────────
3-3. 데이터 변환/메모리
─────────────────────────────────────────────────────────────────────────
• Flow 를 dataclass(slots=True) 로 선언 → 인스턴스 메모리 40-60 % 절감  
• _load_from_disk 단계에서 dict 그대로 cache 하고, Flow 객체는 필요할 때만
  lazy conversion:

class LazyFlow(dict):
    _obj: Flow | None = None
    def as_flow(self) -> Flow:
        if self._obj is None:
            self._obj = Flow.from_dict(self)
        return self._obj

• to_dict() 역시 Flow 안에 _original_dict caching

─────────────────────────────────────────────────────────────────────────
3-4. 동시성 / 멀티프로세스
─────────────────────────────────────────────────────────────────────────
• 파일 기반 유지 시 fcntl/flock 으로 쓰기 잠금  
• SQLite 선택 시 WAL 모드 + connection-pool 사용

4. 예상 효과(폴더 분리 + 캐시 기준)

                         기존                 개선(예상)
────────────────────────────────────────────────────────
flows 1,000개, save 1개  1,000 × R/W         1 × R/W
save 시간               200-300 ms           < 5 ms
메모리 복사량           N×size               0 (view 반환)
flows 속성 1만 번 호출  1만 × disk scan      1 × disk scan
────────────────────────────────────────────────────────

5. 단계별 적용 로드맵

Step 1  flows 캐싱 + TTL                           (변경 최소)
Step 2  JsonFlowRepository 캐시 고정 + dirty-flush (코드 50줄 내)
Step 3  저장 방식 분리(JSONL or per-file)          (데이터 마이그레이션)
Step 4  장기적으로 SQLite 등으로 이동             (트랜잭션, 스키마 관리)

6. 결론

핵심은  
• “읽기”-측 캐시 고정으로 I/O 제거  
• “쓰기”-측 부분 업데이트로 전체 재-쓰기를 없애는 것.  
두 가지만 반영해도 호출당 소요 시간이 10-100 배 단축된다.  
장기적으로는 파일 포맷을 로그 구조(JSONL) 또는 경량 DB 로 전환해
백업/동시성까지 자연스럽게 해결하는 것을 권장한다.
