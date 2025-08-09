# Phase 2 - NAMING 분석

## O3 분석 결과

1. “나머지 15 %”를 바꿀 가치가 있는가?

가치가 있음
• 아직 15 %면 7~8개 파일을 열 때마다 한 개꼴로 스타일이 섞여 있다는 뜻이다. 리뷰·디버깅 시 ‘어 이건 이름이 왜 이렇지?’라는 인지적 전환(Context switch)을 계속 유발한다.  
• 새로 들어온 개발자는 “이 프로젝트는 snake_case 인가 PascalCase 인가?”를 묻지 않고 코드를 읽고, IDE-autocomplete 에서도 한 가지 규칙만 기억하면 된다.  
• 특히 목록에 있는 read / write / insert / delete 는 파괴적(Python 내장 메서드와 동일)·오버로드 위험이 있어, 통일하면서 더 명확한 접두사( file_read, record_delete …)를 붙이면 부수 효과로 API 자체 품질이 올라간다.

가치가 제한적일 수도 있음
• 이미 팀 내부 개발자들이 ‘안다’고 느끼는 부분이라면 체감 개선폭은 크지 않을 수 있다.  
• 외부(서드파티)에서 직접 import 해 쓰는 공개 API 라면, 이름 하나 바꿀 때마다 downstream 호환성·문서·예제 갱신 비용이 따라온다.  

결론
– 전체 코드베이스가 “라이브러리(외부 사용자 많음)”인가 “서비스(사내 전용)”인가, 그리고 새 릴리스에서 semver Major bump 가 가능한가에 따라 ROI 가 갈린다. 사내 서비스나 아직 1.0 이전 라이브러리라면 지금 손대는 편이 장기 유지보수비를 줄인다. 외부 사용자가 많고 이미 1.x 이상이라면 ‘느슨한 통일(별칭+​deprecation)’ 전략이 현실적이다.

2. 의존성 브레이크 포인트

Internal
• import 경로: from mypkg.utils import read  같은 내부 호출 모두.  
• 테스트 코드의 fixture, mock 이름.  
External
• 사용자 스크립트 / 파이프라인 / 노트북.  
• 튜토리얼, README, 블로그·세미나 슬라이드 등 문서.  
• 자동화된 툴(airflow DAG, CI job)에서 셸로 바로 호출하는 경우가 있는지.  

3. 자동화 도구로 얼마나 안전하게 바꿀 수 있나?

AST 기반 리팩터링 툴
• Bowler (Facebook, lib2to3 기반).  
• Rope (PyCharm, VS Code, Emacs 등 IDE 플러그인).  
• Pyrefact, RedBaron 등.  

절차
a. “공식 API” 모듈만 우선 rename 매핑 테이블 작성.  
b. Bowler ‑m mypkg --write 'select("Name").is_identifier("read").rename("read_data")' 식으로 룰을 선언.  
c. CI 에 ‘변경 건수 0’ assert, idempotency 체크.  
d. 미터제이션: 테스트 커버리지 80 % 이상 확보 후 수행.

주의
• 문자열 안( f"read {fname}" ), 주석, YAML, JSON 설정 파일 등은 AST 툴이 못 잡으므로 grep(-rw)으로 2차 검수.  
• SQLAlchemy, Django ORM 같이 “문자열 기반 리플렉션”을 쓰는 프레임워크는 런타임 에러가 남을 수 있다.

4. Deprecation(점진 제거) 전략

Step 0 – 릴리스 노트에 “이름 변경 예정” 예고  
Step 1 – vX.Y
    new_name = old_name  # 완전 별칭
    warnings.warn(
        "mypkg.read is deprecated; use mypkg.read_data",
        DeprecationWarning,
        stacklevel=2,
    )
    __all__ = ["read_data", "read"]  # autocomplete 호환  
Step 2 – vX+1.0
    • DeprecationWarning → PendingRemovalWarning 같은 자체 경고 클래스로 승격  
    • docs, 예제에서 old_name 삭제  
    • 내부 코드에서 old_name 호출 0% 확인  
Step 3 – vX+2.0
    old_name 완전 제거 (ImportError 발생)  

기간(가이드)
• 사내 전용: 한 달~한 분기(릴리스 1~2회)  
• 외부 라이브러리: 최소 한 minor 릴리스 이상, 보통 6~12개월  

툴 제공
• `python -m mypkg.rename_fix` 혹은 `pre-commit` 훅으로 자동 변환 스크립트 제공하면 사용자가 직접 대체 가능.

5. 실제 개발자 경험(DX) 영향

긍정
• IDE 자동 완성 목록이 단일 스타일이 되어 검색/탐색 속도 향상.  
• 코드리뷰에서 “함수 이름이 왜 Camel?” 같은 메타 코멘트가 사라져 본질적 논의(알고리즘/구조)에 집중.  
• future recruit: “Python=PEP 8” 상식과 일치 → 진입장벽 ↓.  

부정/리스크
• 릴리스 직후 downstream 빌드가 깨지면 ‘작은 이름 하나 바꾸려다 하루 날렸다’는 불만.  
• 별칭 + 경고가 IDE 에 “소음”이 될 수 있음(많은 호출마다 Warning). 필터링 가이드 필요.  

6. 비용-효과(ROI) 계산 예시

Assumption  
• 함수 18개, 내부 호출 300곳, 외부 호출 1,000곳(파이프라인 포함).  
• 자동화 리팩터링 90 % 커버, 나머지 수동 10 %.  
• 작업/검증/문서 업데이트 인건비 3 MD(개발 2, 테크라이터 1).  
• 릴리스 및 downstream 수정 대응 2 MD.  
총 5 MD × 인건비 $700/MD ≈ $3,500  

효과(정량)  
• 신규 인원 온보딩 시 “스타일 혼동”으로 소요되는 코드 탐색 시간 2h 감소, 연 5명 × 2h × $70/h ≈ $700/년  
• 리뷰·디버깅 시 1 % 시간 절약(팀 연간 1,000h) = 10h × $70 ≈ $700/년  
순효과 ≈ $1,400/년 → 2.5년이면 비용 회수

⇒ 프로젝트가 3년 이상 유지될 계획이라면 재무적으로도 손익분기(BEP) 돌파.

7. 결론: mixed_case 18개를 지금 바꿀지?

Yes, if
• 장기 유지보수 예정(3년+),  
• semver Major 혹은 pre-1.0 으로 API 단절이 가능한 시점,  
• 자동화 리팩터링 + deprecation 경로를 마련할 의지가 있다.  

Defer, if
• 실제 외부 사용자 수백~수천, “소규모 수정도 어렵다”는 피드백이 이미 존재,  
• 곧 EOL 예정이거나 6-12개월 내 대규모 리팩터·v2 계획이 있어 그때 같이 묶어도 무방,  
• 팀 리소스가 5 MD도 빠듯하다.  

실행 단계 요약
1) 영향 범위 정량화(스캔 + 통계)  
2) rename 매핑/스크립트 준비, Bowler 테스트  
3) 코드·문서·테스트 일괄 커밋, CI 100 % green  
4) Deprecation wrapper + 경고 + 릴노트  
5) 한 사이클 운영 후 제거

이상입니다.

## 메타 정보
- Reasoning Effort: high
- 분석 일시: 2025-08-09 16:44:00
