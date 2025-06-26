AI 코딩 브레인 MCP 구조 분석 (Context, Plan, Task, Build)
컨텍스트 (context) 관리 구조
AI Coding Brain MCP에서는 컨텍스트를 중앙에서 관리하여, 프로젝트의 상태와 대화 흐름을 유지합니다. 핵심은 UnifiedContextManager 싱글톤 클래스이며, 내부에 ProjectContext라는 Pydantic 모델 객체를 보관합니다
GitHub
GitHub
. ProjectContext는 프로젝트명, 경로, 생성/업데이트 시간 등의 기본 정보와 함께, 현재 계획(plan), 현재 작업(task), 작업 큐(tasks), 분석 정보 등을 속성으로 갖는 메인 컨텍스트 객체입니다
GitHub
GitHub
. UnifiedContextManager.initialize() 메서드는 컨텍스트를 초기화할 때 기존 상태를 복원하려고 시도합니다. 우선 인자로 이전 컨텍스트(existing_context)가 주어지면 그대로 사용하거나 dict를 모델로 변환하고
GitHub
, 없을 경우 캐시된 컨텍스트를 메모리 폴더에서 로드합니다
GitHub
. 캐시 파일들은 memory/.cache/ 디렉토리에 JSON 형태로 저장되며, 핵심 데이터(cache_core.json), 작업 목록(cache_tasks.json), 계획(cache_plan.json) 등으로 분리되어 있습니다
GitHub
GitHub
. initialize_context 호출 시 이들 파일을 모두 읽어 ProjectContext 객체로 복원하며, 성공 시 이전 작업 흐름을 그대로 이어받습니다
GitHub
GitHub
. 캐시가 없다면 새로운 컨텍스트를 생성합니다
GitHub
. 이처럼 새 대화가 시작되어도 이전 컨텍스트를 인식할 수 있는 구조 덕분에, AI 비서가 프로젝트의 연속성을 유지하면서 효율적으로 코딩을 도울 수 있습니다. 초기화 후에는 AIHelpers 유틸리티 객체를 준비하여 파일 검색, 코드 실행 등의 헬퍼 기능을 제공합니다
GitHub
. ProjectContext 자체는 Pydantic 데이터 모델로, 내부 필드에 타입 검증과 자동 JSON 직렬화 기능이 있습니다. 예를 들어 프로젝트의 현재 계획은 context.plan으로 저장되고 Plan 모델 객체를 가리킵니다
GitHub
. 현재 작업 ID는 context.current_task에, 그리고 작업 큐는 context.tasks에 딕셔너리로 관리됩니다
GitHub
GitHub
. tasks 필드는 {'next': [], 'done': []} 형태로 기본값이 설정되며, next 리스트에는 앞으로 수행할 작업들, done 리스트에는 완료된 작업들이 들어갑니다
GitHub
. 또한 작업 진행 추적을 위한 WorkTracking 정보(파일 접근 기록, 함수 편집 횟수 등)와 에러 로그, 단계별 보고 등도 ProjectContext에 포함되어 있어 프로젝트 상태를 폭넓게 담습니다
GitHub
GitHub
. 컨텍스트 매니저는 이러한 ProjectContext를 싱글톤으로 보관하며, 필요 시 언제든 get_context_manager().context로 접근할 수 있게 합니다
GitHub
. 컨텍스트 변경이 생기면 get_context_manager().save() 메서드로 즉시 캐시에 기록하여 안정성을 높입니다
GitHub
GitHub
. 저장 시에는 Pydantic 모델을 dict로 변환한 뒤, 핵심 정보와 세부 목록들을 개별 파일로 나누어 씁니다 (예: 주요 속성은 cache_core.json, tasks 리스트는 cache_tasks.json, plan 정보는 cache_plan.json 등)
GitHub
GitHub
. 이런 구조 덕분에 컨텍스트 용량이 커져도 일부만 업데이트하거나 필요 부분만 로드할 수 있고, 새로운 대화나 세션에서도 직전 상태를 신속히 복원하여 대화의 연속성을 유지합니다. 요약하면, 컨텍스트는 AI 코딩 비서의 기억 역할을 합니다. UnifiedContextManager + ProjectContext 모델의 조합으로, 프로젝트의 상태, 계획, 작업 이력을 일관되게 관리하고, 파일 캐싱을 통해 세션 간에도 이를 활용할 수 있도록 설계되어 있습니다.
계획 (plan) 구조와 동작
**Plan(계획)**은 프로젝트 개발 작업을 단계(Phase)와 작업(Task) 단위로 조직화한 구조입니다. core/models.py에 정의된 Plan 클래스는 Pydantic 모델로, 계획 이름(name), 설명(description), 생성/갱신 시각, 그리고 가장 중요한 phases 필드를 가집니다
GitHub
. phases는 Phase ID를 키로 하고 Phase 모델 객체를 값으로 하는 딕셔너리로, 각 Phase에는 자체 ID, 이름, 설명과 해당 단계의 작업 목록(tasks)이 들어 있습니다
GitHub
GitHub
. Plan은 현재 진행 중인 단계/작업을 가리키는 current_phase, current_task 속성도 유지하여 전체 진행 상황을 추적합니다
GitHub
. 또한 Plan 모델은 편의 메서드들을 제공하는데, 예를 들어 get_all_tasks()는 모든 Phase의 작업을 합쳐 반환하고
GitHub
, overall_progress 속성은 전체 작업 대비 완료된 작업 비율을 계산해줍니다
GitHub
. 이를 통해 AI가 계획 수준의 진행률이나 남은 작업을 손쉽게 파악할 수 있습니다. 실행 중인 프로젝트 컨텍스트 (ProjectContext)는 하나의 Plan을 포함하며, context.plan 속성으로 현재 계획을 참조합니다
GitHub
. 따라서 컨텍스트를 통해 Plan의 모든 정보에 접근 가능합니다. 계획이 수립되면, 컨텍스트의 progress 필드도 Plan의 overall_progress로 자동 갱신되어 전체 진행 상황을 기록합니다
GitHub
GitHub
. 계획을 생성하거나 관리하는 로직은 python/commands/plan.py 모듈에 구현되어 있습니다. cmd_plan 함수는 /plan 명령을 처리하며, 호출 방식에 따라 두 가지 모드로 동작합니다:
현재 계획 조회: 인자 없이 /plan을 호출하면 현재 컨텍스트의 계획을 읽어와 요약 정보를 출력합니다. 계획이 없으면 안내 메시지를 보여주고, 존재하면 계획 이름, 설명, 생성일, 현재 Phase 등을 표시합니다
GitHub
GitHub
. 또한 각 Phase별 완료된 작업 수/전체 작업 수와 진행 상태(진행 중: 🔄, 완료: ✅, 대기: ⏳ 등 이모지)를 나열하여 한눈에 볼 수 있게 합니다
GitHub
.
새 계획 생성: /plan 계획명 설명... 형태로 호출하면 새로운 Plan을 만들어 컨텍스트에 등록합니다. 이때 대화형(--interactive) 모드를 선택할 수도 있는데, interactive 모드에서는 터미널 입력으로 계획 설명과 기본 Phase/Task 조정 여부 등을 물어보며 사용자 참여 하에 계획을 세웁니다
GitHub
GitHub
. 반면 기본 모드에서는 자동으로 계획을 구성합니다.
새로운 계획을 만들 때 핵심 흐름은 다음과 같습니다:
프로젝트 분석: Plan 생성 전, 현재 프로젝트를 스캔하여 구조/특징 정보를 수집합니다. ProjectAnalyzer를 사용해 파일 수, 사용 언어, 주요 파일 등을 분석하고 요약(briefing)을 얻습니다
GitHub
. 분석 성공 시 파일 개수와 주요 언어 비율 등을 보고하고
GitHub
, 이 정보를 토대로 권장 작업(recommendations)을 준비합니다
GitHub
GitHub
. 예를 들어 TypeScript 프로젝트라면 "타입 안정성 개선", Python이면 "코드 스타일 검사 추가" 같은 자동 Task 제안을 생성합니다
GitHub
GitHub
. README 파일 유무 등 문서화 필요성도 확인하여 관련 작업을 추천합니다
GitHub
. (분석에 실패해도 계획 생성을 계속하지만, recommendations 리스트는 없을 수 있습니다
GitHub
.)
Plan 데이터 구조화: 새 Plan의 뼈대를 딕셔너리로 만든 뒤, 기본 Phase들과 Task들을 채웁니다. 기본적으로 3개의 Phase (분석/설계, 구현, 테스트/문서화) 틀을 사용하며, 각 Phase마다 대표적인 Task 3~4개를 미리 정의합니다
GitHub
GitHub
. 예컨대 Phase 1 "분석 및 설계"에 "현재 코드 구조 분석", Phase 2 "핵심 구현"에 "단위 테스트 작성", Phase 3 "테스트 및 문서화"에 "README 업데이트" 등이 기본으로 포함됩니다
GitHub
GitHub
. 이러한 기본 Task들은 우선순위(priority) HIGH, MEDIUM, LOW를 같이 지정하기도 하며, Task ID도 phase-1-task-1 같은 고유형식으로 부여됩니다
GitHub
GitHub
. (만약 계획 이름이나 설명에 "flow" 같은 특정 키워드가 있다면, AI Coding Brain 자체 개선에 관한 특별한 Phase/Task 셋을 사용하는 분기도 있습니다
GitHub
GitHub
. 이처럼 MCP 자체를 개선하는 시나리오도 고려하여 기본 Phase가 다르게 설정될 수 있습니다.)
권장 작업 추가: 앞 단계에서 준비된 recommendations가 있다면, 해당 작업들을 알맞은 Phase에 추가합니다. 각 추천 항목에는 대상 Phase, Task 이름, 우선순위가 있는데, Plan 딕셔너리에 해당 Phase가 있으면 그 Phase의 Task 리스트에 항목을 삽입합니다
GitHub
GitHub
. 예를 들어 Phase 1에 "타입 검사 도구 설정 (HIGH)" 같은 추천 작업이 있으면 Phase 1의 Task에 포함하고, 콘솔에 추가되었음을 알려줍니다
GitHub
GitHub
.
컨텍스트에 계획 저장: 완성된 계획 딕셔너리를 set_plan() 함수를 통해 컨텍스트에 적용합니다
GitHub
. 내부적으로 Plan Pydantic 객체로 변환되어 context.plan에 설정되고, 캐시에도 기록됩니다
GitHub
GitHub
. 이때 새 계획 생성 전에 존재하던 작업 큐(context.tasks['next'])를 초기화하여 이전 계획의 남은 작업들을 청소합니다
GitHub
GitHub
. 완료된 작업 목록(done)은 보존하지만, next는 새 계획에 맞게 비웁니다 (이 과정에서 제거한 작업 수를 출력하여 사용자에게 알림: 🧹 메시지)
GitHub
. 그리고 context.plan_history에 이번 계획을 기록하여 과거 계획들의 메타데이터를 남깁니다
GitHub
.
Phase 상태 및 안내: 계획이 성공적으로 생성되면, 컨텍스트 메타데이터의 phase 값을 "planning"으로 설정해 현재 단계가 계획 수립 중임을 표시합니다
GitHub
. 컨텍스트 저장 후 콘솔에는 계획 생성 완료 메시지와 함께 Phase/Task 개요를 요약해 줍니다
GitHub
GitHub
. 예를 들어 기본 Phase 3개가 생성되었다면 각 Phase 이름을 나열하고, “다음 단계” 가이드로서 task add로 작업 추가, next로 작업 시작, task done으로 작업 완료 등을 안내합니다
GitHub
. (만약 MCP Flow 시스템 개선 계획이라면 Phase와 Task 수가 더 많기에, 전체 개수를 집계하여 출력하고 HIGH 우선순위인 Task 몇 개를 하이라이트해주는 등 추가 안내를 합니다
GitHub
GitHub
.)
이상의 Plan 생성 흐름을 통해, AI와 사용자는 프로젝트의 큰 그림(phase)부터 구체 작업 목록까지 공유된 계획을 갖게 됩니다. Plan은 컨텍스트에 저장되어 이후 대화에서도 참조되며, AI는 이 구조를 토대로 "현재 어느 단계에 있고, 남은 할 일은 무엇인지" 이해하게 됩니다. 또한 Plan의 Pydantic 구조(Plan -> Phase -> Task) 덕분에, AI가 필요한 상세 정보를 프로그래밍적으로 얻을 수도 있습니다 (예: context.plan.phases["phase-2"].tasks[0].title로 Phase 2 첫 작업명 접근 등). 이런 계층적 계획 관리는 복잡한 프로젝트도 체계적으로 추적할 수 있게 해주며, AI 코딩 비서의 작업 분할 및 맥락 이해를 지원합니다.
작업 (task) 구조와 흐름
**Task(작업)**는 실제로 구현해야 할 개별 단위를 나타내며, Plan의 구성 요소이자 AI 코딩 브레인이 단계적으로 수행하는 액션의 단위입니다. core/models.py에 정의된 Task 클래스는 id, 제목, 설명, 상태, 우선순위 등의 필드를 가진 Pydantic 모델입니다
GitHub
. 상태(status)는 pending(대기), in_progress(진행 중), completed(완료), blocked(차단됨) 네 가지 중 하나로 제한되며, 우선순위(priority)도 high/medium/low 중 하나로 검증됩니다
GitHub
. Task에는 생성/시작/완료 시각과 완료 여부(completed bool)가 기록되고, 다른 작업에 대한 의존성 목록이나 관련 파일 목록을 속성으로 가질 수 있습니다
GitHub
. 또한 편의 메서드로 mark_completed(), mark_started() 등이 있어 객체 상태를 쉽게 갱신할 수 있습니다
GitHub
GitHub
. Plan의 각 Phase는 tasks: List[Task]를 포함하므로, 모든 작업은 어떤 Phase에 속해 있습니다
GitHub
. 그러나 AI Coding Brain MCP는 Plan에 구조화된 작업 외에, 작업 큐(queue) 개념을 도입하여 작업 진행을 제어합니다. ProjectContext.tasks 필드는 'next'와 'done' 두 리스트로 작업 ID들을 관리하는데, 이것은 Plan과는 별도로 즉시 수행할 작업 목록과 완료된 작업 목록을 트래킹하기 위함입니다
GitHub
GitHub
. 예를 들어 Plan에는 Phase별 수십 개 작업이 있을 수 있지만, 사용자는 우선순위나 의존성을 고려해 몇 개만 선정하여 착수할 수 있습니다. 그 “선정된 대기 작업들”이 tasks['next']에 담기고, AI는 이 큐의 맨 앞 작업부터 차례로 수행하는 식입니다. 한편 이미 끝낸 작업들은 tasks['done']에 기록해두어, 중복 수행을 피하고 성취 목록을 남깁니다. 컨텍스트의 current_task 속성은 현재 진행 중인 작업의 ID를 갖고 있어, AI에게 **“지금 무엇을 하고 있는가”**를 알려줍니다
GitHub
. 이제 python/commands/task.py의 cmd_task 함수가 어떻게 Task들을 관리하는지 살펴보겠습니다. /task 명령은 여러 액션을 지원하며, 첫 번째 인자로 그 하위 명령을 받습니다 (add, done, list, current 등이 구현됨)
GitHub
. 주요 동작별 흐름은 다음과 같습니다:
작업 추가 (task add): 새로운 작업을 계획에 추가하고, 작업 큐에 등록하는 기능입니다. 인자로 Phase ID, 작업 제목, 설명(선택)을 받습니다
GitHub
. 예를 들어 task add phase-2 "로그인 기능 구현" "OAuth 연동"이라고 하면 Phase 2에 "로그인 기능 구현" 작업을 설명과 함께 추가합니다. 구현 과정:
유효성 검사: 주어진 Phase ID가 현재 Plan에 존재하는지 확인합니다. 없으면 에러와 사용 가능한 Phase 목록을 출력하고 중단합니다
GitHub
.
Task 생성: 새로운 Task를 나타내는 new_task 딕셔너리를 만듭니다. ID는 <phase번호>-<작업순번> 형식으로 생성하며(예: phase-2에 세 번째 작업이면 "2-3"), 제목과 설명을 입력받은 대로 설정하고 상태는 pending으로, 생성시각/업데이트시각을 현재 시간으로 기록합니다
GitHub
. 관련 Phase와 우선순위 등의 필드도 필요한 경우 채웁니다 (우선순위는 명시 안 하면 기본 medium).
관련 파일 분석: (선택적) Task 제목에 따라 프로젝트 내 관련 파일을 찾아주는 기능이 있습니다. ProjectAnalyzer와 AIHelpers를 통해 제목의 키워드가 파일 이름이나 코드 내용에 등장하는지 검색하여 최대 5개까지 파일을 추천합니다
GitHub
GitHub
. 예컨대 "로그인" 키워드가 있으면 login으로 시작하는 파일이나 login 문자열이 등장하는 코드를 찾아, 결과를 new_task['related_files']에 경로와 이유를 포함해 저장합니다
GitHub
GitHub
. (이때 3글자 이하 키워드는 제외하는 등의 필터를 적용함
GitHub
.) 콘솔에도 몇 개 발견되었는지 출력하여 참고할 수 있게 합니다
GitHub
GitHub
. 파일 검색이 불가능한 환경이면 경고를 표시하고 넘어갑니다
GitHub
.
Plan에 추가: 준비된 new_task를 해당 Phase의 작업 리스트에 추가합니다
GitHub
. 그리고 Plan 딕셔너리의 updated_at 타임스탬프를 갱신하여 변경이 있음을 명시합니다
GitHub
. 곧바로 update_plan_in_context(context, plan_dict)를 호출해 Plan 변경사항을 컨텍스트에 반영합니다
GitHub
. 이 함수는 내부적으로 앞서 만든 plan_dict를 set_plan으로 저장하고 결과를 True/False로 리턴합니다
GitHub
.
작업 큐 갱신: Plan 저장에 성공하면, 이제 컨텍스트의 tasks['next'] 리스트에도 방금 만든 작업을 등록합니다
GitHub
. context.tasks['next']가 없는 경우를 대비해 초기화하고, 그 안에 {id, phase, title}로 구성된 간략 객체를 추가합니다
GitHub
GitHub
. 이렇게 하면 Plan에는 상세 작업 정보가, tasks 큐에는 실행 대기열이 설정됩니다. 곧바로 context_manager.save()로 컨텍스트를 디스크에 저장하고, 작업 추가 완료 메시지를 출력합니다 (예: ✅ Task 추가됨: [2-3] 로그인 기능 구현)
GitHub
. Phase 이름도 함께 표기해 어디에 추가됐는지 명확히 합니다
GitHub
.
이로써 새로운 작업이 Plan과 Task 큐에 모두 반영되어, AI가 인지할 수 있는 상태가 됩니다.
작업 완료 (task done): 지정한 작업을 완료 처리하고, 필요 시 현재 작업을 해제하며, 작업 큐에서도 이동시킵니다. 인자로 Task ID를 받지만, 생략하면 현재 작업(current_task)을 완료하는 동작을 합니다
GitHub
. 처리 순서:
대상 식별: 인자가 없으면 context.current_task 값을 가져와 현재 진행 중인 작업 ID를 쓰고, 없으면 사용법을 안내하고 중단합니다
GitHub
. 인자가 있으면 해당 ID를 그대로 사용합니다.
Plan에서 상태 변경: Plan의 모든 Phase를 돌며 해당 ID를 가진 Task를 찾습니다
GitHub
. 찾으면 그 Task의 status를 'completed'로 바꾸고 완료 시각(completed_at)과 업데이트 시각을 기록합니다
GitHub
. 이미 완료된 Task를 또 완료처리하려 하면 경고만 내고 끝냅니다
GitHub
.
그리고 만약 지금 완료한 Task가 context.current_task였다면, 즉 현재 수행 중인 작업을 마쳤다면 set_current_task(context, None)로 현재 작업을 해제합니다
GitHub
. 이는 컨텍스트의 current_task를 None으로 돌리고, 작업 추적 정보(current_task_work)도 비우는 효과가 있습니다 (이 부분은 context_manager 쪽에서도 처리).
작업 큐 업데이트: 컨텍스트의 tasks 리스트를 꺼내서, 완료된 작업을 next 목록에서 제거하고 done 목록에 추가합니다
GitHub
GitHub
. 구체적으로 context.tasks['next']를 해당 ID를 제외한 새 리스트로 치환함으로써 제거하고, context.tasks['done'] 리스트에는 작업 ID, 속한 Phase, 제목, 완료 시각을 딕셔너리로 기록합니다
GitHub
GitHub
. 이로써 UI 상으로도 해당 작업이 대기열에서 사라지고 완료 목록으로 이동하게 됩니다.
저장 및 출력: 변경된 plan_dict의 updated_at를 갱신하고, update_plan_in_context와 context_manager.save()를 호출하여 컨텍스트에 변동사항을 확실히 반영합니다
GitHub
. 그리고 "✅ Task [2-3] 로그인 기능 구현 완료!"처럼 완료 메시지를 출력합니다
GitHub
. 만약 이 작업으로 해당 Phase의 모든 Task가 완료되었다면 Phase 상태를 'completed'로 바꾸고 Phase 완료 메시지도 추가합니다 (🎉 Phase 2 완료! 형태)
GitHub
. 찾는 과정에서 대상 Task를 발견하지 못하면 오류 메시지를 알려줍니다
GitHub
.
작업 목록 조회 (task list): 현재 계획의 전체 작업 현황과 작업 큐 상태를 보여줍니다. Plan을 읽어 각 Phase별로 완료/전체 작업 수, 상태(이모지 표시)를 출력하고
GitHub
GitHub
, Phase 내의 각 Task를 순회하며 상태 아이콘과 제목, (현재 작업이면 👈 현재 표시) 그리고 설명이 있으면 아이콘과 함께 들여쓰기하여 표시합니다
GitHub
GitHub
. 또한 계획 전체의 진행률 퍼센트와 완료/총 작업 개수를 계산해 맨 위에 보여주고
GitHub
, 현재 진행 중인 작업이 있다면 따로 현재 작업: [ID]로 알려줍니다
GitHub
. 출력 예시:
less
복사
편집
📋 계획: Project Alpha
진행률: 33.3% (2/6)
현재 작업: [2-1]

⏳ Phase 1: 설계 (1/3 완료)
   📝 초벌 설계 문서 작성
   ✅ [1-1] 요구사항 수집  
   ⏳ [1-2] 아키텍처 설계 👈 현재  
   ⏳ [1-3] 기술 스택 결정

🔄 Phase 2: 구현 (1/2 완료)
   ... (Tasks 나열) ...

📊 작업 큐:
   - 대기: 3개
   - 완료: 2개
위처럼 모든 Phase와 Task 상태를 한눈에 볼 수 있어, 사용자는 진행 상황을 쉽게 파악할 수 있습니다
GitHub
GitHub
. 마지막에 작업 큐 요약(next 남은 개수와 done 완료 개수)도 제공되어 Plan 구조 외에 실제 큐 상태도 확인 가능합니다
GitHub
. 이는 Plan에 정의만 되고 아직 착수하지 않은 작업이 얼마나 있는지, 이미 끝낸 작업이 몇 개인지 대비해서 알려줍니다.
현재 작업 조회 (task current): 지금 진행 중인 작업의 상세를 보여줍니다. context.current_task를 확인하여 없다면 "현재 진행 중인 작업이 없습니다."라고 하고 끝내며
GitHub
, 값이 있다면 Plan에서 해당 작업을 찾아 ID, 제목, 속한 Phase 이름, 설명, 상태, 시작 시각 등을 출력합니다
GitHub
. 이로써 사용자는 현재 무엇을 하고 있었는지 대화 도중 확인할 수 있고, AI도 이 명령의 출력을 보면 맥락을 재확인할 수 있습니다.
정리하면, Task 관리는 Plan의 계층적 구조와 별도로 실제 작업 실행 흐름을 제어하기 위한 장치를 갖추고 있습니다. Plan은 전체 작업의 설계도라면, context.tasks['next'] 리스트는 실행 목록이라고 비유할 수 있습니다. cmd_task와 cmd_next 등을 통해 Plan에 있는 작업을 골라내어 큐에 넣고, 시작/완료하면서 Plan과 큐 양쪽을 업데이트함으로써 계획(Plan)과 실행(Task)을 연결합니다. 이러한 구조 덕분에 AI는 “전체 할 일 중 지금 무엇을 할지”를 결정하고 추적할 수 있으며, 사용자는 한눈에 현재 상태를 파악하고 제어 명령을 내릴 수 있습니다.
문서 빌드 (build) 구조
AI Coding Brain MCP에는 코드 작업뿐 아니라 프로젝트 문서화를 자동화하는 빌드 기능이 포함되어 있습니다. 여기서 build는 일반적인 빌드(컴파일)가 아니라, 프로젝트의 현재 컨텍스트를 바탕으로 README.md나 구성 문서들을 생성/갱신하는 것을 의미합니다
GitHub
. 이 기능은 python/project_context_builder.py에 구현되어 있으며, ProjectContextBuilder 클래스가 핵심 역할을 합니다
GitHub
. ProjectContextBuilder는 프로젝트 디렉토리를 스캔하고 정보를 모은 다음, 미리 정의된 템플릿에 따라 Markdown 문서를 만들어냅니다. 예를 들어:
프로젝트 구조 분석: analyze_project_structure() 메서드는 파일과 폴더를 모두 탐색하여 파일 개수, 언어별 파일 수, 디렉토리 구조 등을 집계합니다
GitHub
GitHub
. .git이나 node_modules 등 불필요한 경로는 무시하고, .py, .ts, .md 같은 주요 확장자의 개수를 세며, 최상위 디렉토리 목록도 수집합니다
GitHub
GitHub
. 이러한 통계는 나중에 README나 문서 본문에 활용됩니다 (예: "전체 파일: X개, Python 파일: Y개...").
README 생성: build_readme() 메서드는 프로젝트 이름, 설명, 버전 같은 기본 정보와 방금 계산한 프로젝트 통계를 조합해 README.md 내용을 문자열로 만듭니다
GitHub
GitHub
. 여기에는 주요 언어별 파일 수, 디렉토리 구조 개요 트리, 설치 및 실행 방법 템플릿, 문서 링크 등이 포함됩니다
GitHub
GitHub
. 또한 이 파일이 자동 생성되었다는 표시를 하단에 남겨둡니다
GitHub
.
프로젝트 컨텍스트 문서 생성: build_project_context() 메서드는 PROJECT_CONTEXT.md라는 별도 문서를 생성합니다
GitHub
. 이 문서는 README보다 자세하게, 프로젝트 개요와 아키텍처 (사용 기술 스택) 및 주요 디렉토리 설명 표를 넣고
GitHub
GitHub
, 의존성 목록, 설정 파일 목록, 통계 요약, 빠른 시작 가이드 등 프로젝트의 전반적인 맥락을 담습니다
GitHub
GitHub
. 이를 통해 다른 사람이 프로젝트를 이해하거나, AI 모델이 프로젝트 전반을 리뷰할 때 활용할 수 있는 상세 컨텍스트 문서가 마련됩니다. 이 문서 역시 /build 명령으로 생성되었다는 주석을 포함합니다
GitHub
.
저장: save_document(filename, content)는 생성된 Markdown 문자열을 파일로 기록합니다
GitHub
. 이미 존재하는 파일이면 업데이트하고, 없으면 새로 생성하며, 완료 시 콘솔에 성공 여부를 로그로 남깁니다.
이 빌드 과정은 대화 도중 AI가 명령어 호출로 수행할 수 있도록 연결되어 있습니다. Node.js 측 코드인 src/handlers/build-handler.ts에서 handleBuildProjectContext 함수가 이를 담당합니다. MCP 서버는 '/build'에 해당하는 도구/명령을 수신하면 (예: 사용자가 채팅에서 "/build"라고 입력하거나, AI가 필요한 시점에 이 도구를 내부적으로 호출), handleBuildProjectContext가 실행됩니다. 이 함수는 백그라운드에서 Python 스크립트를 호출하여 문서 생성을 수행하는데, 구체적으로:
project_context_builder.py 스크립트를 spawn('python', [scriptPath, '--update-readme', 'true/false', '--update-context', 'true/false', ...]) 형태로 별도 프로세스로 실행시킵니다
GitHub
GitHub
. 인자로 어떤 문서를 업데이트할지, 통계 출력 포함 여부 등을 전달합니다.
Python 프로세스의 표준 출력을 실시간으로 수집하면서 로그에도 기록하여 진행 상황을 파악합니다
GitHub
GitHub
.
프로세스 종료 후, 리턴 코드가 0이면 성공으로 간주하고, README.md와 PROJECT_CONTEXT.md 파일이 생성되었는지 확인하여 결과 객체에 담습니다
GitHub
. 그리고 추가로 file_directory.md (프로젝트 파일 구조 상세 문서)도 업데이트하기 위해 updateFileDirectory 함수를 호출합니다
GitHub
. 이 부분은 기존 flow에서 파일 목록을 관리하던 기능으로, 빌드 시 함께 수행되어 문서 일관성을 유지합니다.
모든 작업이 끝나면 성공 메시지와 생성된 문서 목록(예: ["README.md", "PROJECT_CONTEXT.md", "file_directory.md"])을 반환합니다
GitHub
. 대화 상에는 "✅ 프로젝트 컨텍스트 문서 빌드 완료" 같은 내용과 결과 정보가 나타나게 됩니다.
빌드 명령은 주로 프로젝트의 현 상태를 문서화하는 용도로, Plan이나 Task와 직접적인 데이터 주고받음은 없습니다. 하지만, ProjectContextBuilder는 내부적으로 analyze_project_structure에서 프로젝트 파일 구조 및 크기 통계 등을 계산할 때 context의 경로나 설정 파일(.ai-brain.config.json 등)을 참조합니다
GitHub
GitHub
. 따라서 정확한 문서화를 위해서는 컨텍스트가 올바르게 초기화되어 있어야 합니다. 다행히 /flow 명령 등으로 프로젝트 디렉토리를 ContextManager가 잡고 있으므로, 빌드 명령은 그 경로의 내용을 활용합니다. 또한 README에 context.config (프로젝트 이름, 설명, 버전 등)을 반영하는 부분이 있어, .ai-brain.config.json 파일이나 package.json의 필드를 읽어 프로젝트 설명을 채우기도 합니다
GitHub
GitHub
. 요약: /build 명령(문서 빌드)은 AI가 현재까지의 코딩 작업 결과를 정리하는 중요한 단계입니다. 예를 들어 여러 작업을 거쳐 코드가 많이 바뀌었을 때, AI에게 /build를 실행시키면 README와 문서가 최신 상태로 업데이트되어, 이후 대화나 협업 시 참조할 수 있는 프로젝트의 종합적인 그림이 산출됩니다. 이 과정은 MCP 시스템에 통합되어 자동화 가능하며 (일례로 Plan 완료 시 자동 빌드를 트리거하는 등의 활용도 가능), 실제로 문서 하단에 “이 문서는 /build 명령으로 자동 생성되었습니다.”라는 문구
GitHub
GitHub
를 넣어 사용자에게도 그 출처를 명확히 하고 있습니다. 결과적으로 AI 코딩 비서는 단순히 코드를 생성하는 것을 넘어, 문서까지 관리하는 도우미로서 역할을 수행하게 됩니다.
구성 요소 간의 연결 (Plan → Task → Build 흐름)
지금까지 개별적으로 설명한 Plan, Task, Build 구조는 AI 코딩 워크플로우에서 유기적으로 연결되어 작동합니다. 사용자와 AI의 typical 대화 흐름을 예로 들어 이 연결고리를 정리해보겠습니다:
프로젝트 흐름 시작 (/flow): 새로운 프로젝트를 시작하거나 전환할 때 /flow <프로젝트폴더> 명령이 사용됩니다. 이는 initialize_context를 호출하여 해당 경로로 컨텍스트를 세팅하고, 이전에 작업한 프로젝트라면 문맥을 복원합니다. (Flow 명령 내부 로직은 앞서 다룬 컨텍스트 초기화와 유사하며, helpers.cmd_flow_with_context로 구현되어 있습니다
GitHub
GitHub
.) 이 단계에서는 Plan이나 Task가 결정되지 않았으므로, AI는 주로 프로젝트 구조를 이해하거나 세팅을 확인합니다.
계획 수립 (/plan): AI와 사용자는 /plan 명령을 통해 개발 계획(Plan)을 수립합니다. 새 Plan이 만들어지면 컨텍스트에 저장되고, 단계적인 작업 목록이 정의됩니다. 이 시점부터 AI는 context.plan을 통해 프로젝트의 큰 그림을 파악하게 됩니다. 예를 들어 Phase 1: 설계, Phase 2: 구현 등의 개념적 단계와 그 하위 작업들을 인식하고, 이후 대화에서 "Phase 1의 작업부터 진행하겠습니다"처럼 언급할 수 있습니다. Plan 수립 직후에는 context.tasks['next']가 비어있거나 최소한으로만 채워진 상태인데, 곧이어 사용자 또는 AI가 구체 작업 추가로 넘어갑니다.
작업 추가 및 큐잉 (/task add): /plan 단계에서 기본 Task들이 생성되기도 하지만, 추가로 상세 작업을 넣거나 계획을 수정하려면 /task add를 사용합니다. 이는 Plan에 새로운 작업을 반영하고 동시에 tasks 큐(next)에 등록되므로, 실행 대기열이 생기는 순간입니다. 가령 Phase 1의 기본 작업 "요구사항 수집"이 Plan에는 있지만 당장 안 할 수도 있기 때문에 큐에 안 넣을 수도 있습니다. 대신 /task add phase-1 "API 명세 작성"을 하면 Plan에 없던 작업도 추가되며, next 큐에 들어가게 됩니다. 이렇게 필요한 작업들이 큐에 채워지면, AI는 무엇부터 할지 우선순위를 고려해 결정할 수 있습니다.
다음 작업 진행 (/next): /next 명령은 현재 작업이 없다면 큐에서 다음 할 일을 꺼내어 시작하는 동작입니다. cmd_next()는 context.current_task가 비어있는지 확인한 후, Plan과 tasks 큐를 대조하여 유효하지 않게 남아있는 작업이 큐에 있으면 제거(동기화)합니다
GitHub
. 그런 다음 tasks['next'] 리스트를 의존성 충족 여부와 우선순위 기반으로 정렬합니다
GitHub
GitHub
. 예를 들어 어떤 작업이 다른 Task 완료를 기다려야 한다면 blocked=True로 간주되어 뒤로 밀리고, 우선순위가 높은 작업은 앞으로 옵니다. 정렬된 리스트에서 가장 높은 우선순위의 가능한 작업을 선택하여 available_task로 정한 뒤, 이를 현재 진행할 작업으로 채택합니다
GitHub
GitHub
. 선택된 작업은 Plan 구조에서도 찾은 다음 상태를 in_progress로 바꾸고 시작 시각을 기록합니다
GitHub
. 해당 Phase의 상태도 in_progress로 변경하여 그 Phase가 진행 중임을 표시합니다
GitHub
. 컨텍스트에도 set_current_task(context, task_id)를 호출해 현재 작업 ID를 설정하고, Plan의 current_phase와 current_task를 갱신합니다
GitHub
GitHub
. 이러한 업데이트는 Plan과 컨텍스트 양쪽에 저장되어 일관성이 유지됩니다. 그리고 컨텍스트 메타데이터의 phase를 "development"로 변경하여 (만약 이전에 planning이었다면) 이제 실제 개발 단계로 들어섰음을 명시합니다
GitHub
. 모든 세팅 후에는 콘솔에 선택된 작업을 시작한다는 브리핑을 합니다
GitHub
. 예를 들면:
markdown
복사
편집
🚀 작업 시작: [1-2] 아키텍처 설계
   Phase: Phase 1: 설계
   설명: 주요 컴포넌트와 모듈 관계 정의
📋 작업 브리핑:
   1. 작업 ID: 1-2
   2. 제목: 아키텍처 설계
   3. Phase: Phase 1: 설계
💡 작업 완료 후 'task done'을 실행하세요.
이처럼 AI와 사용자에게 지금 어떤 작업을 수행하는지 상세히 알려주고, 관련 파일이나 서브태스크가 있으면 추가로 나열합니다
GitHub
GitHub
. 마지막 줄에는 완료 후 무엇을 해야 할지도 (예: task done) 힌트를 줌으로써 워크플로우를 자연스럽게 이어가도록 돕습니다
GitHub
. 이제 AI는 이 작업에 대한 코딩을 진행하며, 사용자는 필요한 경우 추가 지시를 내립니다. 만약 next 큐에 작업이 없을 때 /next를 호출하면 "대기 중인 작업이 없습니다" 메시지와 함께 Plan 내 pending 상태인 작업 목록을 보여주어 추가 작업 등록을 유도합니다
GitHub
GitHub
. 또한 작업은 있으나 모두 의존성 때문에 blocked인 경우, 착수 불가능하다는 안내와 함께 어떤 Task들이 어떤 의존성 때문에 막혀있는지 최대 5개까지 목록을 제공합니다
GitHub
GitHub
. 이를 통해 사용자는 선행 작업을 완료하거나 우선순위를 재조정할 수 있습니다.
작업 수행 및 완료 (/task done): AI가 코딩을 끝마치면, 사용자 혹은 AI의 다음 액션으로 해당 작업을 완료 처리합니다. 앞서 Task 완료 단계에서 설명한 것처럼, /task done은 Plan과 컨텍스트에 상태 변화를 주고 큐를 갱신합니다
GitHub
GitHub
. 결과적으로 현재 작업이 context.current_task에서 내려가고 tasks['next']에서도 빠지며, Plan에서는 해당 Task가 completed로 상태 변경됩니다
GitHub
GitHub
. 이때 자동으로 다음 작업을 시작하지는 않으므로(현재 cmd_next 호출은 사용자가 명시적으로 해야 함), 완료 후에는 상황에 따라 사용자가 다음 지시를 내립니다. 예컨대 같은 Phase에 다음 작업이 있다면 다시 /next를 호출하거나, 우선 다른 Phase 작업을 하고 싶다면 그 작업을 task add로 큐잉한 후 /next를 할 수 있습니다. Task 완료 시 출력되는 메시지와 Phase 완료 여부 체크
GitHub
는 사용자의 성취감을 높이고, Phase가 끝날 때마다 AI도 이를 인지해 다음 Phase로 넘어갈 준비를 합니다. context.progress도 update_progress()를 통해 업데이트되어, 전체 진행률이 올라갑니다
GitHub
. 만약 모든 Phase의 작업이 완료되면, Plan 전체가 사실상 종료된 것이므로 이후 단계로 빌드/마무리로 넘어갈 수 있겠습니다.
문서 빌드 (/build): 여러 작업이 완료되고 코드가 원하는 수준으로 작성되었다면, 프로젝트 문서를 업데이트할 시점입니다. 사용자는 AI에게 "/build" 명령을 내리거나, AI 스스로 필요하다고 판단하여 빌드 도구를 호출할 수 있습니다. 이 명령을 실행하면 앞서 설명한 ProjectContextBuilder가 동작하여 README.md, PROJECT_CONTEXT.md, file_directory.md 등을 최신 상태로 만들어줍니다. 예컨대 새로운 파일이 많이 생겼다면 README의 파일 통계가 갱신되고, 프로젝트 설명이나 버전이 변경되었으면 반영됩니다
GitHub
GitHub
. 또한 Plan이나 Task와 직접 연동되지는 않지만, project_wisdom.md 등 문서에 지난 작업에서 얻은 교훈이 기록되거나(project_wisdom.md는 Wisdom 시스템 관련) 최신 파일 구조가 반영되는 등, 코딩 단계의 산출물을 정리해 줍니다. 빌드 완료 메시지가 나타나면, 사용자는 깃헙 저장소 등에 바로 푸시하거나, 다른 팀원에게 공유할 수 있는 업데이트된 문서 셋을 얻게 됩니다.
이처럼 Plan → Task → Build로 이어지는 일련의 흐름은 MCP가 지향하는 AI 코딩의 단계적 프로세스를 보여줍니다. Plan으로 큰 그림을 세우고(Task 리스트화), Task 명령들과 Next로 그걸 하나씩 실행하며, Build로 결과물을 정리하는 구조입니다. 모든 단계에서 ProjectContext가 일종의 접착제 역할을 하여, Plan과 Task 진행 상황이 컨텍스트에 저장되고 공유됩니다. 특히 새 대화가 시작되더라도 initialize_context가 이전 상태를 로드하기 때문에
GitHub
GitHub
, 예를 들어 하루 쉬고 돌아와도 AI는 “어제 Phase 2의 두 번째 작업까지 완료되었다”는 것을 알고 있습니다. 이는 사용자가 불필요하게 맥락을 다시 설명해야 하는 수고를 덜어주며, AI의 연속적인 도움을 가능케 합니다. 또한, 이러한 연결 덕분에 AI는 Plan의 내용(예: 남은 Task의 제목이나 우선순위)을 대화 중에 참조하거나 언급할 수 있고, Task 진행 도중에도 Plan 전체 맥락을 놓치지 않습니다. 예를 들어 AI가 코드를 작성하다가 "이 기능은 Phase 3의 문서화 작업과 연관됩니다"라고 언급할 수도 있고, 또는 다음에 뭘 해야 할지 스스로 제안할 때 Plan의 다음 Task를 알려줄 수도 있습니다. 실제로 cmd_next의 구현을 보면, 작업 시작 시 "작업 브리핑"을 통해 AI에게 현재 Task 정보를 요약해주는 효과가 있습니다
GitHub
. 이런 정보를 대화 내에 노출함으로써, AI 모델이 해당 Task의 맥락을 잊지 않고 답변 생성에 활용할 수 있게 됩니다. 마지막으로 Build 단계는, 완료된 코드와 문서를 가지고 프로젝트를 종합적으로 점검하거나 새 계획을 수립하는 피드백 루프로 이어질 수 있습니다. 예컨대 README를 업데이트하고 나면, AI가 "/plan 리팩토링" 등을 통해 새로운 개선 계획(Plan)을 제안할 수도 있습니다. 이처럼 MCP 워크플로우는 반복적(iterative) 개발 사이클을 지원하며, 각 구성 요소(Context, Plan, Task, Build)가 그 사이클의 한 축을 담당합니다.
개선 및 리팩토링 가능성
현재 구조는 기능적으로 잘 동작하고 있으나, 코드 구조와 흐름을 개선하여 더욱 효율적인 AI 코딩 경험을 제공할 여지가 있습니다. 코드 분석을 바탕으로 몇 가지 리팩토링 및 개선 아이디어를 정리하면 다음과 같습니다:
Plan과 Task 큐 통합: Plan의 작업 목록과 컨텍스트의 tasks['next'] 큐를 이원화하여 관리하는 현 방식은 다소 복잡합니다. 이로 인해 Plan과 큐 사이에 동기화 작업이 필요한데, 실제 cmd_next에서는 Plan에 없는 작업을 큐에서 제거하는 정리 루틴이 존재합니다
GitHub
. 또한 Plan 업데이트 후 매번 tasks 큐를 별도로 조정해야 하므로, cmd_task add나 cmd_task done 등에 중복 로직이 생깁니다. 이를 개선하기 위해 단일한 작업 소스로 관리하는 방법을 고려할 수 있습니다. 예를 들어 Plan 자체에 "다음 실행할 작업" 목록이나 포인터를 두고, 컨텍스트 큐를 없애버리는 것입니다. Plan의 각 Task에 status 필드가 이미 있으므로, pending인 작업들 중 우선순위/의존성 조건을 만족하는 것을 바로 검색하면 tasks['next'] 없이도 다음 작업을 결정할 수 있습니다. 이렇게 하면 /next 시 매번 tasks 큐와 맞춰볼 필요 없이, Plan 정보만 참고해 진행이 가능해집니다. 큐를 유지하더라도, Plan <-> 큐 간 자동 동기화를 도입하면 수동 관리 부담을 줄일 수 있습니다. (예: Plan.add_task() 시 자동으로 context.tasks['next']에 넣고, Task.completed 변경 시 자동으로 큐 갱신 등.) 현재는 이러한 동기화가 코드 여러 곳에 퍼져있어 복잡도를 높이는데, 이를 일원화하면 코드가 단순해지고 오류 가능성도 낮아집니다.
Pydantic 모델 활용 극대화: MCP는 Pydantic 모델을 도입하여 타입 안전성과 직렬화를 얻었지만, 실제 조작 시 dict로 변환해서 처리하는 부분이 많습니다. 예컨대 cmd_task add에서 Plan을 다룰 때 plan_dict = plan_to_dict(plan)으로 받고 나서 dict 조작 후 update_plan_in_context로 저장하는 흐름을 취하고 있습니다
GitHub
GitHub
. 이보다는 모델 객체의 메서드와 속성을 직접 활용하는 편이 바람직합니다. 이미 Phase.add_task() 메서드가 존재하여 Task 객체를 추가할 수 있고
GitHub
, ProjectContext.update_progress()로 진행률 계산도 할 수 있습니다
GitHub
. 그런데 현재 코드는 Plan/Phase/Task 객체를 직접 수정하기보다 dict를 수정하므로, Pydantic의 validator나 일관성 보장 기능을 충분히 활용하지 못합니다. 개선안으로, Plan/Phase를 편집하는 함수들을 ContextManager나 별도 Manager 클래스로 만들어 Plan에 Task 추가, 상태 변경, 삭제 등을 캡슐화할 수 있습니다. 예를 들어 ContextManager.add_task(phase_id, title, desc)를 만들면 내부에서 context.plan.phases[phase_id].add_task()를 호출하고, 추가된 Task 객체를 context.tasks['next']에 넣고 저장까지 처리하도록 할 수 있습니다. 이렇게 하면 dict 변환이나 수동 업데이트 실수를 줄이고, Plan과 Context 간 동기화도 자연스럽게 이루어집니다. 또한 set_plan처럼 Plan을 한꺼번에 넣는 함수 대신, Plan 객체 자체에 plan.add_phase(name, desc)나 plan.phases[id].mark_completed() 같은 조작 메서드를 늘려 Plan을 객체 지향적으로 관리하면 가독성이 향상됩니다. 나아가 Plan/Phase/Task 모델에 post_init 또는 validator 등을 활용해, 상태 변화시 상위 객체를 갱신하거나, Task.status가 'completed'로 바뀌면 Task.completed_at 자동 설정 같은 로직을 넣을 수도 있습니다. 이처럼 모델 중심으로 리팩토링하면 명령어 코드(cmd_* 모듈)는 모델의 메서드를 호출하는 단순한 형태가 되어, 향후 유지보수가 쉬워지고 오류가 줄어들 것입니다.
명령어 로직 구조화 및 중복 제거: 현재 /plan, /task, /next 등이 별도의 파일에서 절차지향적으로 구현되어 있는데, 이를 일관된 인터페이스로 묶는 리팩토링을 제안합니다. 예를 들어 WorkflowManager 클래스(가칭)를 도입해서, 계획 수립 → 작업 관리 → 다음 작업 실행 순서의 함수들을 한 곳에 모을 수 있습니다. 이미 claude_code_ai_brain.py에서 /plan, /task, /next 명령을 파싱하여 해당 함수를 호출하는 구조를 가지고 있는데
GitHub
GitHub
, 이를 한 단계 발전시켜 WorkflowManager 내에 plan_project(), add_task(), complete_task(), start_next_task() 메서드를 마련하고, 내부에서 ContextManager와 Plan/Task 모델을 조작하게 하면 응집도가 높아집니다. 현재도 이러한 동작이 helpers(cmd_plan 등)로 감싸져 있긴 하지만
GitHub
GitHub
, 여전히 global 함수들이 많아서 테스트나 재사용이 어렵습니다. 객체 지향적으로 리팩토링하면 상태를 class 내부에 보관하거나 DI(Dependency Injection)로 주입하기 쉬워져, 나중에 여러 프로젝트 컨텍스트를 동시 관리하거나, 특정 부분만 모킹(mocking)하여 테스트하는 것이 수월해집니다. 또한 명령어별 출력 포맷과 로직의 유사점을 고려하면, 템플릿 메서드 패턴처럼 일부 공통 동작을 추상화할 수도 있습니다. 예를 들어 대부분의 명령에서 context = get_context_manager().context로 컨텍스트를 받아 확인하는 코드가 반복되는데, 이 체크를 Decorator나 base function으로 만들 수 있습니다. cmd_task, cmd_plan, cmd_next 모두 수행 전에 if not context: print("❌ 프로젝트가 선택되지 않았습니다.") 같은 검사를 하는데
GitHub
GitHub
, 이를 공통화하면 코드 중복이 줄겠지요. 이런 작은 리팩토링들이 모이면, 코드가 한결 깔끔해지고 이해하기 쉬워져서 AI가 코드 컨텍스트를 분석하거나 개선점을 제안할 때도 더 명확한 기준을 가질 수 있습니다.
상태 지속성과 복구 기능 강화: MCP는 컨텍스트를 저장/복원하여 세션 간 상태를 이어주는 훌륭한 특징이 있지만, 이를 더욱 견고하게 만들 여지도 있습니다. 예를 들어 현재는 context_manager.save()를 명시적으로 호출하는 곳이 여러 군데 있고
GitHub
GitHub
, 사용자가 실수로 save를 누락하면 마지막 상태가 유실될 수 있습니다. 이를 개선하려면 자동 저장 트리거를 도입할 수 있습니다. 작업 완료나 계획 변경 시마다 save를 호출하는 대신, UnifiedContextManager에 데코레이터나 컨텍스트 매니저 패턴을 적용해 중요한 변화 함수 내에서 자동으로 save하도록 변경할 수 있습니다. 또는 일정 시간 간격으로 주기적 백업을 하거나, SIGINT/종료 시그널을 가로채 종료 전에 저장하도록 할 수도 있습니다. 캐시 파일 관리도 개선 포인트입니다. 현재는 다섯 개 정도의 JSON 파일로 분리하여 저장하는데
GitHub
, 이는 필요한 부분만 갱신/로드하기 위한 성능상의 선택으로 보입니다. 다만 파일 수가 많아지면 I/O overhead나 일관성 문제가 생길 수 있으므로, 단일 데이터베이스 파일(예: SQLite)로 통합하거나, 반대로 더 세분화하여 각 Task나 Phase별 파일로 관리하는 방법도 있습니다. SQLite 같은 경우 트랜잭션으로 일관성을 쉽게 유지하고 질의도 가능하며, JSON보다는 구조적 관리에 용이합니다. 한편 현재 JSON 캐시는 사람이 읽기에도 쉬운데, 용량이 커지면 부담될 수 있습니다. 예를 들어 analyzed_files나 work_tracking 정보가 방대해지면 JSON 파싱에 시간 걸릴 수 있는데, 이때는 해당 부분을 캐시에 포함시키지 않고 필요할 때만 불러오는 lazy loading 전략도 고려할 수 있습니다. 이런 저장소 구조의 개선은 사용자에게 직접 보이는 부분은 아니지만, MCP의 성능과 안정성을 높여 궁극적으로 AI 코딩 경험을 부드럽게 만듭니다.
대화 컨텍스트와의 연계: MCP의 컨텍스트는 내부적으로 잘 유지되지만, 대화 상의 컨텍스트 활용은 더욱 최적화될 수 있습니다. 현재도 작업 브리핑이나 리스트 명령 출력을 통해 AI에게 정보를 주입하고 있지만, 체계적이진 않습니다. 한 아이디어로, 시스템 프롬프트에 현재 ProjectContext 요약을 넣는 기능을 생각해볼 수 있습니다. 이를테면 대화가 시작될 때 "이 프로젝트는 무엇이며, 현재 어떤 Phase의 어떤 작업을 진행 중" 같은 정보를 요약해 AI에게 알려주면, 모델이 답변을 생성할 때 항상 최신 맥락을 인지하게 됩니다. MCP가 자체적으로 이러한 요약을 생성하려면, context 객체를 직렬화하거나 중요한 필드만 발췌하여 문장으로 만들 수 있어야 합니다. 예를 들어 context.project_name, context.plan.current_phase와 context.current_task를 조합해 "[프로젝트명] 진행 중 (Phase 2: 구현, 현재 작업: 로그인 API 구현)" 같은 한 줄 요약을 시스템 메시지로 넣어줄 수 있습니다. 이런 기능은 아직 MCP 코드에 직접 구현되지는 않았지만, 충분히 시도해볼 만한 개선입니다. 또한 AI가 자동으로 다음 동작을 결정하게 하려면, 컨텍스트 정보를 토대로 판단해야 하는데 현재는 사용자가 명시적으로 next_task 도구를 호출해야만 다음 작업으로 넘어갑니다
GitHub
. 개선안으로, AI가 알아서 "모든 완료, 다음 Phase로 넘어가겠습니다"라고 판단하도록 유도하려면, Plan/Task 상태를 모델 입력에 명확히 주어야 합니다. 예를 들어 Phase 완료 시 🎉 Phase 1 완료! 같은 문구가 모델 입력에 있고, 다음 Phase에 pending 작업들이 있다는 정보도 입력에 있다면, 모델이 다음 단계 제안을 하기 쉬워집니다. 따라서 대화창 맥락에 Plan/Task 진행 상황을 의도적으로 노출하는 전략은 AI의 주도적 도움을 강화해줄 것입니다.
우선순위 및 의존성 관리 개선: 현재 Task의 priority와 dependencies 필드는 정의만 되어 있고, 이를 활용하는 로직은 cmd_next의 정렬 과정에 일부 반영되어 있습니다
GitHub
GitHub
. 그러나 우선순위가 단순 HIGH/MEDIUM/LOW 세 값인 점, 의존성은 완료 여부만 체크하는 점 등은 비교적 단순한 로직입니다. 현실 프로젝트에서는 우선순위가 수시로 바뀌거나, 의존성도 동적일 수 있지요. 개선 포인트는 우선순위 기반 자동 Task 재정렬이나 의존성 그래프 시각화/관리 기능입니다. 예컨대 사용자가 Task의 priority를 변경하면(task edit 명령 등 상정), tasks['next'] 큐 순서도 바로 바뀌게 하거나, 특정 Task가 blocked 상태일 때 그를 막고 있는 선행 Task들을 쉽게 조회하는 명령을 추가할 수 있습니다. 이런 기능은 AI에게도 유용하여, "X 작업은 Y가 끝나야 할 수 있다"는 걸 더 명확히 파악하고 계획을 조정하는 데 도움이 됩니다. 현재 코드에서도 blocked Task를 출력해주고 있지만
GitHub
, 더 나아가 **“왜 이 작업이 막혔는가”**를 자동으로 Reasoning하여 알려줄 수도 있습니다. 이는 Wisdom 시스템과도 연계될 수 있는 부분으로서, MCP의 지능적인 작업 관리 측면을 강화합니다.
以上の改良点々を総合すると (위 개선점들을 종합하면), AI 코딩 브레인 MCP는 구조적 단순화와 정보 활용 증대로 더욱 강력한 도구가 될 수 있습니다. Plan-Task 간 중복 제거로 워크플로우 처리 효율이 올라가고, 모델에게 더 풍부한 맥락을 제공함으로써 AI 보조의 지능이 향상됩니다. 또한 지속적 자동 저장과 상태 관리 개선으로 시스템 안정성이 강화되어, 장시간 또는 대규모 프로젝트에서도 끊김 없이 운영할 수 있습니다. 결과적으로 사용자는 덜 고민하고도 AI와 함께 복잡한 코딩 작업을 진행할 수 있고, AI는 더 많은 것을 이해한 상태에서 정확하고 창의적인 코딩 제안을 할 수 있게 될 것입니다.
효율적인 AI 코딩 흐름을 위한 제안
위에서 도출한 개선점들을 토대로, AI 코딩 흐름을 한층 효율적으로 만들기 위한 제안을 정리합니다:
데이터 구조 단순화로 인한 명료성 향상: Plan과 Task 정보의 단일화 또는 통합 관리는 개발 흐름을 명확히 합니다. 현재 구조에서는 Plan의 작업과 실행 큐가 분리돼 있어 AI가 두 구조를 모두 신경 써야 하지만, 이를 일원화하면 AI가 참조할 데이터가 줄어들어 맥락 파악이 빨라집니다. 예를 들어 모든 작업의 상태를 Plan 하나로 관리하면, AI는 context.plan만 확인해서 바로 다음 할 일을 결정할 수 있습니다. 이는 곧 응답 생성 시 고려해야 할 조건이 줄어들어 모델의 추론 부담을 낮추고 정확성을 높이는 효과를 냅니다.
중복 코드 제거에 따른 유지보수 및 확장성 증가: 내부 구현을 리팩토링하여 중복을 없애고 객체 지향적으로 바꾸면, 코드 변경이 쉬워집니다. 이는 새로운 기능 추가나 수정이 빈번한 AI 개발 보조 도구에 매우 중요합니다. 예컨대 /task edit(기존 작업 편집)이나 /task remove(작업 삭제) 같은 기능을 추가한다면, 지금 구조에서는 plan_dict와 context.tasks 양쪽을 또 다뤄야 하지만, 개선된 구조에서는 한 번의 메서드 호출로 처리 가능할 것입니다. 코드가 단순해질수록 AI의 코드 이해력도 높아져, 사용자가 "왜 이 기능이 동작하지 않는지" 물을 때 AI가 디버깅 도움을 주기도 수월해집니다. 즉, 내부 품질 개선이 결국 사용자 경험 개선으로 이어지는 선순환이 기대됩니다.
맥락 정보의 적극적 활용: AI에게 현재 프로젝트 상황을 충분히 알려주는 것은 중요한 효율 요소입니다. 컨텍스트 로딩으로 이전 상태를 기억하는 것은 기본이고, 나아가 그 정보를 대화에 녹여내는 자동화가 있다면 사용자는 맥락 설명에 시간을 쓰지 않고 바로 작업에 집중할 수 있습니다. 예를 들어 "다음 작업으로 어떤 걸 진행할까요?"라고 묻는 사용자의 질문에, AI가 Plan에 남은 작업을 참고해 구체적으로 답할 수 있을 것입니다. 현재도 task list 결과를 보면 AI가 남은 할 일을 알 수 있지만
GitHub
, 이것이 시스템 차원에서 늘 주어지면 AI의 상황 대응 능력이 크게 향상됩니다. 이를 통해 AI는 진정한 의미에서 컨텍스트 인식 코딩 비서가 되어, 맥락을 벗어나지 않는 답변과 제안을 지속적으로 할 수 있습니다.
자동화된 문서화 및 학습 사이클: /build 명령은 문서화를 한 번에 해주지만, 더 나아가 지속적인 문서 동기화를 고려할 수 있습니다. 예를 들어 매 Task 완료 시마다 README의 변경 로그 섹션에 항목 추가를 제안하거나, 일정 시간이 지난 후 AI가 "문서 갱신을 권장"하는 프롬프트를 주는 식입니다. 문서는 프로젝트의 얼굴이자 AI가 프로젝트를 학습하는 교재 같은 역할도 합니다. 프로젝트 진행 중간중간 문서를 갱신하면, AI도 그 내용을 보고 새로운 통찰을 얻거나 오류를 줄이는 데 도움이 될 수 있습니다. (물론 문서 내용은 AI 모델에게 추가 컨텍스트로 주입해야 효과가 있지만, 최소한 사용자에게 최신 정보를 제공하고, 향후 세션에 활용될 수 있다는 점에서 중요합니다.) 이러한 코드-문서 병행 관리는 AI 코딩 흐름을 더욱 프로페셔널하고 완성도 있게 만들어 줄 것입니다.
Wisdom 시스템 및 품질 개선의 활용: MCP에는 Wisdom이라는 오류 패턴 추적 및 모범 사례 축적 시스템이 있음을 엿볼 수 있었습니다
GitHub
GitHub
. 아직 질문 범위에는 직접 등장하지 않았지만, track_mistake나 wisdom_stats 같은 도구들이 암시하는 것은, AI가 작업 중에 배운 교훈을 데이터베이스화하고 있다는 것입니다. 이러한 피드백 루프를 적극 활용하면, AI 코딩 흐름의 효율이 시간에 따라 점점 증가할 수 있습니다. 예컨데 "이전에 5번의 작업에서 3번은 테스트 코드를 빼먹었다"는 패턴을 안다면, AI는 다음 Task 진행 시 이를 미리 알려줄 수 있습니다. 또는 "task done 직후 git 커밋을 안 해서 유실 위험 발생" 패턴을 인지했다면, 완료 시 자동 git_commit_smart() 실행을 제안하는 등 사전 예방적 조치가 가능하겠죠. 결국 Plan → Task → Build의 사이클에 Wisdom 기반 개선점 제안 단계를 추가하여, 매 사이클이 돌 때마다 프로젝트 품질과 AI 지원의 질이 함께 향상되는 효과를 노릴 수 있습니다.
以上、AI 코딩 브레인 MCP의 구조 분석과 개선 제안을 모두 살펴보았습니다. 😀 이러한 리팩토링과 전략들을 적용하면, 사용자는 새 대화를 시작할 때 일일이 상황을 설명하지 않아도 되고, AI는 축적된 컨텍스트와 계획을 바탕으로 더 정확한 도움을 줄 수 있습니다. 결과적으로 사람-AI 협업의 생산성이 높아지고, 프로젝트의 일관성 및 문서화 수준도 향상될 것입니다. 미래 버전의 AI Coding Brain MCP가 제안된 방향으로 발전하여, 더욱 똑똑하고 효율적인 코딩 파트너로 거듭나길 기대합니다! 🚀
GitHub
GitHub