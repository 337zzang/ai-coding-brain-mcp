
[🎯 핵심 질문]
AI Helpers V2 로드 실패 - import 함수 불일치 문제 해결 방법

[📊 현재 상황]
- 프로젝트: ai-coding-brain-mcp  
- 파일: python/json_repl_session.py가 ai_helpers_v2 모듈 import 시도
- 현상: ImportError - 'parse_file' 등 여러 함수를 찾을 수 없음

[🔍 분석 결과]
1. json_repl_session.py가 요구하는 함수들:
   - parse_file, extract_functions, extract_code_elements (없음)
   - fp, flow_project, scan_directory, workflow (없음)
   - 기타 31개 함수

2. ai_helpers_v2 모듈의 실제 구조:
   - __init__.py에서 from .xxx_ops import * 사용
   - parse_file 대신 parse_with_snippets만 존재
   - workflow 관련 함수들이 별도 workflow 디렉토리에 있음

3. 문제의 핵심:
   - 함수 이름 불일치 (parse_file vs parse_with_snippets)
   - 일부 함수가 다른 모듈에 있음 (workflow)
   - json_repl_session.py의 import 목록이 구버전 기준인 듯

[💻 관련 코드]
```python
# json_repl_session.py (라인 70-84)
from ai_helpers_v2 import (
    # ...
    parse_file, extract_functions, extract_code_elements,  # 없음
    # ...
    fp, flow_project, scan_directory,  # 없음
    workflow  # 없음
)
```

[⚡ 긴급도]  
☑ 즉시 (블로킹 이슈)

[🎯 요청사항]
1. 최소한의 코드 수정으로 import 문제 해결 방법
2. 함수 별칭(alias) 생성 vs import 목록 수정 중 어느 것이 나은가?
3. workflow 관련 함수들을 ai_helpers_v2에 통합해야 하는가?
4. 장기적으로 안정적인 구조를 위한 권장 방안
