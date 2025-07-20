# o3 프로젝트 구조 분석

생성일: 2025-07-19 22:25:36

## 현재 상황

- 헬퍼 관련 경로: 73개
- 백업 파일: 47개
- 중복 파일 다수

## o3 분석 결과

📌 1. 현재 상황 진단
────────────────────────
1) 강한 결합  
   • json_repl_session.py  →  from ai_helpers_v2 import … (하드코딩)  
   • ai_helpers_new 는 import 시도-실패 → 모듈 경로가 패키지로 인식되지 않거나 sys.path 에 없음.

2) 파일·폴더 난립  
   • “helper” 라는 이름을 가진 경로 73개, 백업( *.bak, *.old, *~, *.orig 등) 47개  
   • __init__.py 7곳, workflow_helper.py 2중복 → import 충돌·섀도잉 발생.

3) 결과  
   • 어느 헬퍼를 로드해야 하는지 불명확  
   • pylint / mypy / IDE 가 동일 심볼을 여러 곳에서 찾아 경고  
   • 테스트·릴리스 시 예상치 못한 모듈이 로드될 가능성 ↑


📌 2. 헬퍼 시스템 통합 전략
────────────────────────
Step 1) 두 버전 diff·머지
   a. 디렉터리 수준 diff (예: diff -r ai_helpers_v2 ai_helpers_new)  
   b. 기능 매트릭스 작성:  
       - v2 에만 있는 util   ‑-→ 포함 여부 결정  
       - new 에만 있는 개선 기능 ‑-→ 유지

Step 2) 최종 패키지 이름 결정  
   • 프로젝트 전반에 “ai_helpers” 단일 패키지만 남기는 것을 강력 권장.  
   • new 를 기준으로 삼고, v2 의 필요한 함수/클래스만 porting.  
   • 버전 suffix 는 git 태그, pypi version, 또는 __version__ 으로 관리.  
     (디렉터리 이름에 버전 붙이지 않음)

Step 3) shim(호환 레이어) 제공 (선택)  
   • ai_helpers_v2  디렉터리는 남기지 말고, 아래와 같이 ‘얇은’ 모듈만 둔다.  
     python/ai_helpers_v2/__init__.py
     ------------------------------------------------
     from warnings import warn
     warn("ai_helpers_v2 는 deprecated, ai_helpers 로 이동했습니다", DeprecationWarning)
     from ai_helpers import *
     ------------------------------------------------
   • 3rd-party 코드가 아직 v2 를 import 하더라도 정상 동작.


📌 3. 폴더 구조 재편성
────────────────────────
권장 최종 구조
mcp/
 ├ python/
 │   ├ ai_helpers/           # 통합 헬퍼
 │   │   ├ __init__.py
 │   │   ├ workflow_helper.py
 │   │   └ …
 │   ├ json_repl/            # REPL 관련 코드(모놀리식을 모듈화)
 │   │   ├ __init__.py
 │   │   └ repl_session.py   # ← 기존 json_repl_session.py 리네이밍 권장
 │   └ utils/                # 범용 유틸
 ├ tests/
 ├ docs/
 ├ requirements.txt / pyproject.toml
 └ mcp.json

정리 스크립트 예시  (GNU/Linux)
find . -type f \( -name "*~" -o -name "*.bak" -o -name "*.old" -o -name "*.orig" \) -delete
find python -type f -name "workflow_helper.py" | grep -v "ai_helpers" | xargs rm

주의: git 사용 중이라면 위 명령 전에 모든 변경 커밋 → 안전.


📌 4. import 문제 해결
────────────────────────
1) 패키지화(PEP 420 규칙 준수)
   • python/ 경로가 패키지 루트 → PYTHONPATH 에 자동 포함되게 하려면  
     – editable install:  pip install -e .  
     – 또는 외부 스크립트에서  export PYTHONPATH="$PWD/python:$PYTHONPATH"

2) json_repl_session.py 수정 예
------------------------------------------------
# python/json_repl/repl_session.py
import importlib, os

HELPER_PACKAGE = os.getenv("AICB_HELPER", "ai_helpers")   # 환경변수로 전환
helpers = importlib.import_module(HELPER_PACKAGE)

# 명시적 import 필요하다면
from importlib import import_module
workflow_helper = import_module(f"{HELPER_PACKAGE}.workflow_helper")

# 기존 코드 ↓↓↓
# wf = workflow_helper.WorkflowHelper(...)
------------------------------------------------
장점  
• 런타임에 버전을 바꿀 수 있고 테스트가 용이  
• 코드베이스에는 ai_helpers 만 등장 → 가독성

3) 상대 vs 절대 import
   • 패키지 내부에서는 절대 import 사용 (PEP 8 권장)
     from ai_helpers.workflow_helper import WorkflowHelper
   • 테스트 폴더에서는 sys.path 조작하지 말고  python -m pytest  형태로 실행.


📌 5. 단계별 실행 플랜
────────────────────────
Phase 0  백업 전체 저장소(또는 Git branch cut)  
Phase 1  ai_helpers_v2 ↔ ai_helpers_new 기능 diff → 통합  
Phase 2  새로운 ai_helpers 패키지 완성, unit-test 작성  
Phase 3  전역 검색-치환  
         sed -i 's/ai_helpers_v2/ai_helpers/g' $(git ls-files '*.py')  
Phase 4  shim 모듈만 남기고 나머지 v2/new 폴더 삭제  
Phase 5  백업·중복 파일 일괄 삭제 (find 명령 참조)  
Phase 6  CI 파이프라인/requirements/pyproject 갱신 → 빌드 테스트  
Phase 7  PR / Code-Review → main 머지

안전 삭제 대상(예시)  
• *_backup.py, *.bak, *~, *.orig, .DS_Store  
• 중복 workflow_helper.py (ai_helpers 디렉터리 외)  
• ai_helpers_v2/**  내부 실제 구현 파일 (shim 제외)  
• ai_helpers_new/**  (통합 완료 후)

필수 보존 파일  
• python/ai_helpers/**   (통합본)  
• python/json_repl/repl_session.py  
• mcp.json, tests/, docs/  
• setup.cfg / pyproject.toml / requirements.txt


📌 6. 추가 권장 사항
────────────────────────
• 도메인 로직과 CLI(UI) 레이어를 분리 → import 의존 최소화  
• __all__ = [...] 지정해 public API 명시  
• mypy / pylint / ruff 로 정적 분석 → 서서히 타입힌트 추가  
• GitHub Actions 등 CI 로 ‘import check’ 및 ‘pytest’ 자동화  
• 버저닝:  ai_helpers/__init__.py 에 __version__ = "0.3.0" 등 명시  
• 패키지 배포 예정이면  pyproject.toml 작성으로 표준화

이렇게 정리하면
1) import 에러 사라지고,  
2) 두 버전 공존 문제 해결,  
3) 유지보수 난이도가 대폭 감소합니다.