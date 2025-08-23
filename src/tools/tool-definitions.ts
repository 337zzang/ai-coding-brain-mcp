import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * AI Coding Brain MCP - Tool Definitions
 * 
 * 영속적 Python REPL 세션과 프로젝트 관리를 위한 MCP 도구 모음
 * 
 * @version 4.2.0
 * @updated 2025-07-23
 * @author AI Coding Brain Team
 */

// Tool schemas
import { executeCodeSchema } from './schemas/execute-code';
import { restartReplSchema } from './schemas/restart-repl';

/**
 * MCP 도구 정의 배열
 * 각 도구는 name, description, inputSchema를 포함합니다.
 */
export const toolDefinitions: Tool[] = [
  {
    name: 'execute_code',
    description: `Execute Python code in a persistent REPL session with advanced project management and workflow integration.
실행 Python 코드를 영속적 REPL 세션에서 실행하며 고급 프로젝트 관리 및 워크플로우 통합을 제공합니다.

⚠️ CRITICAL: MUST READ BEFORE USING / 사용 전 필독:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ALWAYS import these at the start / 항상 시작 시 import:
   import ai_helpers_new as h
   import sys
   import os
   from pathlib import Path
   from datetime import datetime

2. F-STRING RULES / F-문자열 규칙:
   ✅ CORRECT: f"Value: {variable}"
   ❌ WRONG: f"Dict: {dict}" → Use f"Dict: {{dict}}" for literal braces
   ❌ WRONG: f"Path: {path\file}" → Use raw string or forward slash
   
3. CORRECT API NAMES / 올바른 API 이름:
   ✅ h.search.files() - NOT search_files()
   ✅ h.file.info() returns {'ok': bool, 'data': {'size': int, 'lines': int}}
   ❌ NOT 'modified_relative' or 'modified_time'

🔥 Core Features / 핵심 기능:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Persistent Session: Variables and state preserved across all calls
   영속적 세션: 모든 호출 간 변수와 상태 유지
✅ Project Isolation: Each project has independent execution environment  
   프로젝트 격리: 각 프로젝트는 독립적인 실행 환경 보유
✅ AI Helpers v2.5: Enhanced 12-module helper system (134+ methods)
   AI 헬퍼 v2.5: 12개 모듈로 확장된 종합 헬퍼 시스템 (134개+ 메서드)
   • File operations with shutil integration / shutil 통합 파일 작업
   • Jupyter notebook native support / Jupyter 노트북 네이티브 지원
   • UV package manager (Rust-powered) / UV 패키지 매니저 (Rust 기반)
✅ Jupyter Integration: Native notebook support for data science workflows
   Jupyter 통합: 데이터 과학 워크플로우를 위한 네이티브 노트북 지원
✅ UV Package Manager: 10-100x faster Python package management
   UV 패키지 매니저: 10-100배 빠른 Python 패키지 관리
✅ Background Execution: Async AI consultation with o3 models
   백그라운드 실행: o3 모델을 통한 비동기 AI 상담
✅ Precision Code Editing: AST-based coordinate modification
   정밀 코드 수정: AST 기반 좌표로 정확한 수정

📦 AI Helpers v2.5 API (USE EXACTLY AS SHOWN) / 정확한 API 이름:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────┬──────────────────────────────────────────────────────────┐
│ Module      │ EXACT Method Names (대소문자 구분)                       │
├─────────────┼──────────────────────────────────────────────────────────┤
│ 📁 h.file   │ read, write, append, exists, info, read_json, write_json, copy, move, delete │
│ 🔧 h.code   │ parse, view, replace, insert, functions, classes        │
│ 🔍 h.search │ files (NOT search_files), code, grep, imports          │
│ 🤖 h.llm    │ ask, ask_async, ask_practical, check_status, get_result │
│ 🛠️ h.util   │ ok, err, is_ok, get_data, get_error                     │
│ 📊 h.git    │ status, add, commit, diff, log, branch, push, pull      │
│ 🌐 h.web    │ start, goto, click, close, screenshot                   │
│ 📓 h.jupyter│ create_notebook, read_notebook, add_cell, execute_notebook, convert_to_python │
│ ⚡ h.uv     │ install_uv, quick_setup, create_venv, pip_install, pip_sync │
└─────────────┴──────────────────────────────────────────────────────────┘

💡 Quick Start Examples / 빠른 시작 예시:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import ai_helpers_new as h

# 📁 File Operations / 파일 작업 (Facade Pattern)
content = h.file.read('file.py')['data']      # Read file / 파일 읽기
h.file.write('output.py', content)            # Write file / 파일 쓰기  
h.file.append('log.txt', 'new line\\n')        # Append to file / 파일 추가
result = h.file.exists('file.txt')            # Check existence / 존재 확인
# Returns: {'ok': True, 'data': True/False, 'path': 'file.txt'}

# 📋 JSON Operations / JSON 작업 
data = h.file.read_json('config.json')['data'] # Read JSON / JSON 읽기
h.file.write_json('output.json', data)        # Write JSON / JSON 쓰기

# 📂 File Management / 파일 관리 (NEW v2.5!)
h.file.copy('source.py', 'backup.py')         # Copy file with metadata / 메타데이터 포함 복사
h.file.copy('src_dir/', 'backup_dir/')        # Copy directory recursively / 디렉토리 재귀 복사
h.file.move('old_name.py', 'new_name.py')     # Rename/move file atomically / 원자적 이름변경/이동
h.file.move('src/', 'dest/')                  # Move entire directory tree / 전체 디렉토리 트리 이동
h.file.delete('temp.txt')                     # Safe delete single file / 안전한 단일 파일 삭제
h.file.delete('temp_dir/', force=True)        # Force delete directory tree / 디렉토리 트리 강제 삭제
# Note: All operations preserve timestamps & permissions / 모든 작업은 타임스탬프와 권한 보존

# 🔍 Code Analysis / 코드 분석
info = h.code.parse('module.py')              # Parse Python file / 파일 파싱
if info['ok']:
    functions = h.code.functions('module.py') # Get functions / 함수 목록
    classes = h.code.classes('module.py')     # Get classes / 클래스 목록

# ✏️ Code Modification / 코드 수정  
h.code.replace('file.py', 'old', 'new')       # Replace code / 코드 교체
h.code.view('file.py', 'function_name')       # View function / 함수 보기
h.code.insert('file.py', 'new line', line_num)# Insert line / 라인 삽입

# 🔎 Search Operations / 검색 작업
results = h.search.files('pattern', '.')      # Search files / 파일 검색
results = h.search.code('pattern', '.')       # Search in code / 코드 검색
results = h.search.grep('pattern', '.')       # Grep pattern / 패턴 검색
imports = h.search.imports('.')               # Find imports / import 찾기

# 📊 Git Operations / Git 작업
status = h.git.status()                       # Git status / 상태 확인
h.git.add('.')                                # Stage files / 파일 추가
h.git.commit('feat: new feature')             # Commit / 커밋
h.git.push()                                  # Push to remote / 푸시

# 🤖 LLM AI Tasks / LLM AI 작업
task_id = h.llm.ask_async("complex query")['data'] # Start async task
status = h.llm.check_status(task_id)              # Check status
h.llm.show_progress()                             # Show progress
result = h.llm.get_result(task_id)                # Get result

# 📓 Jupyter Notebook / 노트북 작업 (NEW v2.5!)
h.jupyter.create_notebook('analysis.ipynb')       # Create nbformat 4 notebook / nbformat 4 노트북 생성
h.jupyter.add_cell('analysis.ipynb', 'code', 'import pandas as pd') # Add code/markdown cell / 코드/마크다운 셀 추가
h.jupyter.execute_notebook('analysis.ipynb')      # Execute all cells in order / 모든 셀 순차 실행
h.jupyter.convert_to_python('analysis.ipynb')     # Export as executable .py / 실행가능한 .py로 내보내기
h.jupyter.install_kernel('myenv', 'My Kernel')    # Register IPython kernel / IPython 커널 등록
h.jupyter.clear_outputs('analysis.ipynb')         # Clear all cell outputs / 모든 셀 출력 제거
h.jupyter.merge_notebooks(['nb1.ipynb', 'nb2.ipynb']) # Merge multiple notebooks / 여러 노트북 병합

# ⚡ UV Package Manager / UV 패키지 관리 (10-100x faster than pip!)
h.uv.install_uv()                                 # Install UV via pip / pip으로 UV 설치
h.uv.quick_setup()                                # Auto venv + deps + git init / 자동 환경설정
h.uv.create_venv('3.11')                         # Create Python 3.11 venv / Python 3.11 가상환경
h.uv.pip_install(['pandas', 'numpy'])            # Lightning fast install / 초고속 설치 (Rust 기반)
h.uv.pip_sync('requirements.txt')                # Sync & lock deps / 의존성 동기화 및 잠금
h.uv.pip_compile('requirements.in')              # Generate locked requirements / 잠긴 요구사항 생성
h.uv.run('python script.py')                     # Run in UV environment / UV 환경에서 실행

# ⚠️ Error Handling Pattern / 에러 처리 패턴
result = h.file.read('missing.txt')
if not h.util.is_ok(result):
    print(h.util.get_error(result))           # Get error message

🌊 Flow System (Advanced Project Management) / Flow 시스템:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Flow API for structured project planning / 구조화된 프로젝트 계획
api = h.flow_api()                            # Get Flow API instance / API 인스턴스
api.create_plan("project", "description")     # Create new plan / 새 계획 생성
api.add_task("task name", "description")      # Add task to plan / 태스크 추가
api.complete_task(task_id)                    # Complete task / 태스크 완료
api.get_status()                              # Get project status / 상태 확인

# Direct Flow functions / 직접 Flow 함수
h.flow_project("project-name")                # Switch to project / 프로젝트 전환
plans = h.Plan.load_all()                     # Load all plans / 모든 계획 로드
task = h.Task("name", "desc", "pending")      # Create task / 태스크 생성

📊 Standard Return Format / 표준 반환 형식:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All helper functions return consistent dict format:
모든 헬퍼 함수는 일관된 dict 형식 반환:

{
  'ok': bool,           # Success status / 성공 여부
  'data': Any,          # Result data / 결과 데이터  
  'error': str | None,  # Error message if failed / 실패시 에러 메시지
  ...                   # Additional info / 추가 정보
}

❌ COMMON ERRORS TO AVOID / 피해야 할 일반적 오류:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. F-string errors / F-문자열 오류:
   ❌ f"Dict: {{'key': 'value'}}" → SyntaxError
   ✅ f"Dict: {str({'key': 'value'})}" or use json.dumps()
   
2. Method name errors / 메서드명 오류:
   ❌ h.search.search_files() → AttributeError
   ✅ h.search.files()
   
3. Key errors / 키 오류:
   ❌ info['modified_relative'] → KeyError
   ✅ info['data']['size'] or info['data']['lines']
   
4. Import errors / Import 오류:
   ❌ Using sys without import → NameError
   ✅ Always import sys, os, Path at start
   
5. Path errors / 경로 오류:
   ❌ "path\\to\\file" on Unix → Error
   ✅ Use Path("path/to/file") or forward slashes
   
6. File operation errors / 파일 작업 오류:
   ❌ h.file.copy('file.txt', 'existing_dir/') → May overwrite
   ✅ h.file.copy('file.txt', 'existing_dir/file_backup.txt')
   ❌ h.file.delete('important_dir/') → Fails without force
   ✅ h.file.delete('important_dir/', force=True)`,
    inputSchema: executeCodeSchema
  },
  {
    name: 'restart_json_repl',
    description: `Restart the Python REPL session with selective preservation options.
Python REPL 세션을 선택적 보존 옵션과 함께 재시작합니다.

🔄 Main Features / 주요 기능:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Memory Cleanup: Clear accumulated variables and state
   메모리 정리: 누적된 변수와 상태를 정리
✅ Selective Preservation: Optionally keep helpers object intact
   선택적 보존: helpers 객체를 선택적으로 유지 가능
✅ Persistent Data: Disk-stored data remains unaffected
   영속 데이터: 디스크에 저장된 데이터는 영향받지 않음
✅ Context Retention: Current project settings are preserved
   컨텍스트 유지: 현재 프로젝트 설정은 보존

📋 Use Cases / 사용 시나리오:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧹 Memory Management: Clean up when memory usage is high
   메모리 관리: 메모리 사용량이 높을 때 정리
🆕 Fresh Start: Initialize environment before new tasks
   새로운 시작: 새 작업 전 환경 초기화
🔧 Error Recovery: Recover from error states gracefully
   오류 복구: 오류 상태에서 안전하게 복구
🧪 Testing Environment: Prepare clean slate for testing
   테스트 환경: 테스트를 위한 깨끗한 환경 준비

💡 Example Usage / 사용 예시:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Basic restart - clears everything / 기본 재시작 - 모든 것 초기화
restart_json_repl()

# Keep helpers object / helpers 객체 유지
restart_json_repl(keep_helpers=True, reason="Memory cleanup")

# Full reset for testing / 테스트를 위한 완전 초기화
restart_json_repl(keep_helpers=False, reason="Test environment setup")

⚠️ Important Notes / 중요 사항:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Files on disk are NOT affected / 디스크의 파일은 영향받지 않음
• Project context is maintained / 프로젝트 컨텍스트는 유지됨
• Module cache is cleared / 모듈 캐시는 초기화됨
• Import statements need re-execution / import 문은 재실행 필요`,
    inputSchema: restartReplSchema
  }
];

/**
 * 도구 이름으로 도구 정의를 찾습니다
 * @param name 도구 이름
 * @returns 도구 정의 또는 undefined
 */
export function findToolByName(name: string): Tool | undefined {
  return toolDefinitions.find(tool => tool.name === name);
}

/**
 * 모든 도구 이름 목록을 반환합니다
 * @returns 도구 이름 배열
 */
export function getToolNames(): string[] {
  return toolDefinitions.map(tool => tool.name);
}
