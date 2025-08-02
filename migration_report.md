# AI Helpers Migration Report

Generated: 2025-08-03 01:23:13

## Summary
- Modified files: 27
- Total changes: 255
- Backup folder: `migration_backup_20250803_012312`

## Detailed Changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\code.py
Changes: 17

**Line 82**: `append` function
- Before: `self._current_class['methods'].append(func_info)`
- After: `self._current_class['methods'].h.append(func_info)`

**Line 84**: `append` function
- Before: `self.functions.append(func_info)`
- After: `self.functions.h.append(func_info)`

**Line 99**: `append` function
- Before: `self.classes.append(class_info)`
- After: `self.classes.h.append(class_info)`

**Line 108**: `append` function
- Before: `self.imports.append(alias.name)`
- After: `self.imports.h.append(alias.name)`

**Line 112**: `append` function
- Before: `self.imports.append(node.module)`
- After: `self.imports.h.append(node.module)`

... and 12 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\context_integration.py
Changes: 9

**Line 62**: `append` function
- Before: `context["actions"].append(action)`
- After: `context["actions"].h.append(action)`

**Line 98**: `append` function
- Before: `doc_info["actions"].append(action)`
- After: `doc_info["actions"].h.append(action)`

**Line 107**: `insert` function
- Before: `docs_context["recent_activities"].insert(0, recent_activity)`
- After: `docs_context["recent_activities"].h.insert(0, recent_activity)`

**Line 133**: `append` function
- Before: `docs_context["references"].append(reference)`
- After: `docs_context["references"].h.append(reference)`

**Line 140**: `append` function
- Before: `docs_context["documents"][doc]["references"].append(reference)`
- After: `docs_context["documents"][doc]["references"].h.append(reference)`

... and 4 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\context_reporter.py
Changes: 4

**Line 133**: `append` function
- Before: `slow_ops.append({`
- After: `slow_ops.h.append({`

**Line 209**: `append` function
- Before: `slow_methods.append((method, stat['avg_ms']))`
- After: `slow_methods.h.append((method, stat['avg_ms']))`

**Line 221**: `append` function
- Before: `error_methods.append((method, error_rate))`
- After: `error_methods.h.append((method, error_rate))`

**Line 243**: `replace` function
- Before: `flow_id = dirs[0].replace('flow_', '')`
- After: `flow_id = dirs[0].h.replace('flow_', '')`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\doc_context_helper.py
Changes: 2

**Line 21**: `write` function
- Before: `f.write(content)`
- After: `f.h.write(content)`

**Line 42**: `append` function
- Before: `contexts.append(doc_context)`
- After: `contexts.h.append(doc_context)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\excel.py
Changes: 1

**Line 535**: `append` function
- Before: `sheets.append(manager.workbook.Worksheets(i).Name)`
- After: `sheets.h.append(manager.workbook.Worksheets(i).Name)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\file.py
Changes: 16

**Line 27**: `exists` function
- Before: `if not p.exists():`
- After: `if not p.h.exists():`

**Line 52**: `append` function
- Before: `lines.append(line.rstrip('\n'))`
- After: `lines.h.append(line.rstrip('\n'))`

**Line 68**: `append` function
- Before: `lines.append(line.rstrip('\n'))`
- After: `lines.h.append(line.rstrip('\n'))`

**Line 75**: `append` function
- Before: `lines.append(line.rstrip('\n'))`
- After: `lines.h.append(line.rstrip('\n'))`

**Line 106**: `exists` function
- Before: `if backup and p.exists():`
- After: `if backup and p.h.exists():`

... and 11 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\git.py
Changes: 14

**Line 118**: `git_log` function
- Before: `log_info = git_log(limit=1)`
- After: `log_info = h.git_log(limit=1)`

**Line 152**: `append` function
- Before: `args.append(branch)`
- After: `args.h.append(branch)`

**Line 162**: `append` function
- Before: `args.append(branch)`
- After: `args.h.append(branch)`

**Line 189**: `git_status` function
- Before: `# DEPRECATED: git_status() 함수가 이제 모든 기능을 포함합니다.`
- After: `# DEPRECATED: h.git_status() 함수가 이제 모든 기능을 포함합니다.`

**Line 190**: `git_status` function
- Before: `# 이 함수는 하위 호환성을 위해 유지되지만 git_status()를 사용하세요.`
- After: `# 이 함수는 하위 호환성을 위해 유지되지만 h.git_status()를 사용하세요.`

... and 9 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\llm.py
Changes: 24

**Line 55**: `insert` function
- Before: `messages.insert(0, {"role": "system", "content": context})`
- After: `messages.h.insert(0, {"role": "system", "content": context})`

**Line 311**: `write` function
- Before: `f.write(content)`
- After: `f.h.write(content)`

**Line 333**: `append` function
- Before: `tasks.append({`
- After: `tasks.h.append({`

**Line 391**: `append` function
- Before: `to_remove.append(task_id)`
- After: `to_remove.h.append(task_id)`

**Line 423**: `read` function
- Before: `result = read(str(path))`
- After: `result = h.read(str(path))`

... and 19 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\project.py
Changes: 3

**Line 34**: `append` function
- Before: `lines.append(line)`
- After: `lines.h.append(line)`

**Line 118**: `get_current_project` function
- Before: `proj_info = get_current_project()`
- After: `proj_info = h.get_current_project()`

**Line 160**: `git_status` function
- Before: `git_result = git_status()`
- After: `git_result = h.git_status()`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\project_refactored.py
Changes: 2

**Line 37**: `exists` function
- Before: `"type": "node" if (project_path / "package.json").exists() else "python",`
- After: `"type": "node" if (project_path / "package.json").h.exists() else "python",`

**Line 38**: `exists` function
- Before: `"has_git": (project_path / ".git").exists(),`
- After: `"has_git": (project_path / ".git").h.exists(),`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\search.py
Changes: 12

**Line 27**: `search_files` function
- Before: `search_files("*.py")  # 모든 .py 파일`
- After: `h.search_files("*.py")  # 모든 .py 파일`

**Line 28**: `search_files` function
- Before: `search_files("test")  # 'test'가 포함된 모든 파일`
- After: `h.search_files("test")  # 'test'가 포함된 모든 파일`

**Line 29**: `search_files` function
- Before: `search_files("test*", "src/", max_depth=2)  # src/ 아래 2단계까지`
- After: `h.search_files("test*", "src/", max_depth=2)  # src/ 아래 2단계까지`

**Line 56**: `append` function
- Before: `found_files.append(rel_path)`
- After: `found_files.h.append(rel_path)`

**Line 105**: `search_files` function
- Before: `files_result = search_files(file_pattern, path, recursive=True)`
- After: `files_result = h.search_files(file_pattern, path, recursive=True)`

... and 7 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\simple_flow_commands.py
Changes: 43

**Line 50**: `flow` function
- Before: `flow()                    # 현재 상태 표시`
- After: `h.flow()                    # 현재 상태 표시`

**Line 51**: `flow` function
- Before: `flow("/list")            # Plan 목록`
- After: `h.flow("/list")            # Plan 목록`

**Line 52**: `flow` function
- Before: `flow("/create 계획이름")  # 새 Plan 생성`
- After: `h.flow("/create 계획이름")  # 새 Plan 생성`

**Line 53**: `flow` function
- Before: `flow("/select plan_id")  # Plan 선택`
- After: `h.flow("/select plan_id")  # Plan 선택`

**Line 54**: `flow` function
- Before: `flow("/task add 작업명")  # Task 추가`
- After: `h.flow("/task add 작업명")  # Task 추가`

... and 38 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\task_logger.py
Changes: 8

**Line 58**: `get_current_project` function
- Before: `project_info = get_current_project()`
- After: `project_info = h.get_current_project()`

**Line 97**: `write` function
- Before: `f.write(json.dumps(event, ensure_ascii=False) + '\n')`
- After: `f.h.write(json.dumps(event, ensure_ascii=False) + '\n')`

**Line 281**: `exists` function
- Before: `if not self.log_file.exists():`
- After: `if not self.log_file.h.exists():`

**Line 301**: `append` function
- Before: `events.append(event)`
- After: `events.h.append(event)`

**Line 373**: `replace` function
- Before: `safe_title = task_title.replace(' ', '_').replace('.', '').replace('/', '_')`
- After: `safe_title = task_title.h.replace(' ', '_').h.replace('.', '').h.replace('/', '_')`

... and 3 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\ultra_simple_flow_manager.py
Changes: 1

**Line 89**: `append` function
- Before: `plans.append(plan)`
- After: `plans.h.append(plan)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\wrappers.py
Changes: 4

**Line 108**: `scan_directory` function
- Before: `"""DEPRECATED: Use scan_directory(path, output='dict') instead`
- After: `"""DEPRECATED: Use h.scan_directory(path, output='dict') instead`

**Line 111**: `scan_directory` function
- Before: `scan_directory(path, max_depth=max_depth, output='dict')를 사용하세요.`
- After: `h.scan_directory(path, max_depth=max_depth, output='dict')를 사용하세요.`

**Line 115**: `scan_directory` function
- Before: `"scan_directory_dict is deprecated. Use scan_directory(output='dict')",`
- After: `"scan_directory_dict is deprecated. Use h.scan_directory(output='dict')",`

**Line 119**: `scan_directory` function
- Before: `return scan_directory(path, max_depth=max_depth, output='dict')`
- After: `return h.scan_directory(path, max_depth=max_depth, output='dict')`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\core\fs.py
Changes: 3

**Line 61**: `exists` function
- Before: `if not p_root.exists():`
- After: `if not p_root.h.exists():`

**Line 86**: `replace` function
- Before: `path_str = str(relative_path).replace(os.sep, '/')`
- After: `path_str = str(relative_path).h.replace(os.sep, '/')`

**Line 95**: `append` function
- Before: `result.append(path_str)`
- After: `result.h.append(path_str)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\repository\enhanced_ultra_simple_repository.py
Changes: 11

**Line 75**: `exists` function
- Before: `if legacy_file.exists() and not plan_dir.exists():`
- After: `if legacy_file.h.exists() and not plan_dir.h.exists():`

**Line 85**: `exists` function
- Before: `if not plan_file.exists():`
- After: `if not plan_file.h.exists():`

**Line 107**: `exists` function
- Before: `if self.plans_dir.exists():`
- After: `if self.plans_dir.h.exists():`

**Line 109**: `exists` function
- Before: `if plan_dir.is_dir() and (plan_dir / "plan.json").exists():`
- After: `if plan_dir.is_dir() and (plan_dir / "plan.json").h.exists():`

**Line 110**: `append` function
- Before: `plan_ids.append(plan_dir.name)`
- After: `plan_ids.h.append(plan_dir.name)`

... and 6 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\repository\ultra_simple_repository.py
Changes: 1

**Line 65**: `append` function
- Before: `plan_ids.append(plan_file.stem)`
- After: `plan_ids.h.append(plan_file.stem)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\service\lru_cache.py
Changes: 1

**Line 88**: `append` function
- Before: `expired_keys.append(key)`
- After: `expired_keys.h.append(key)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\ai_helpers_new\utils\safe_wrappers.py
Changes: 4

**Line 63**: `append` function
- Before: `safe_functions.append({`
- After: `safe_functions.h.append({`

**Line 94**: `append` function
- Before: `matching.append(func)`
- After: `matching.h.append(func)`

**Line 134**: `append` function
- Before: `results.append({'index': i, 'item': item, 'result': result.get('data')})`
- After: `results.h.append({'index': i, 'item': item, 'result': result.get('data')})`

**Line 136**: `append` function
- Before: `errors.append({'index': i, 'item': item, 'error': result.get('error')})`
- After: `errors.h.append({'index': i, 'item': item, 'error': result.get('error')})`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\example_javascript_execution.py
Changes: 8

**Line 21**: `web_start` function
- Before: `web_start(headless=False)`
- After: `h.web_start(headless=False)`

**Line 22**: `web_goto` function
- Before: `web_goto("https://example.com")`
- After: `h.web_goto("https://example.com")`

**Line 43**: `web_start` function
- Before: `web_start(headless=False)`
- After: `h.web_start(headless=False)`

**Line 44**: `web_goto` function
- Before: `web_goto("https://quotes.toscrape.com")`
- After: `h.web_goto("https://quotes.toscrape.com")`

**Line 76**: `web_start` function
- Before: `web_start(headless=False)`
- After: `h.web_start(headless=False)`

... and 3 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\web_automation_errors.py
Changes: 3

**Line 194**: `append` function
- Before: `call_stack.append({`
- After: `call_stack.h.append({`

**Line 223**: `append` function
- Before: `serialized.append(repr(arg))`
- After: `serialized.h.append(repr(arg))`

**Line 225**: `append` function
- Before: `serialized.append(f"<{type(arg).__name__} object>")`
- After: `serialized.h.append(f"<{type(arg).__name__} object>")`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\web_automation_extraction.py
Changes: 1

**Line 28**: `replace` function
- Before: `'float': lambda x: float(re.sub(r'[^0-9.-]', '', str(x).replace(',', ''))),`
- After: `'float': lambda x: float(re.sub(r'[^0-9.-]', '', str(x).h.replace(',', ''))),`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\web_automation_helpers.py
Changes: 25

**Line 72**: `web_start` function
- Before: `>>> web_start()`
- After: `>>> h.web_start()`

**Line 73**: `web_goto` function
- Before: `>>> web_goto("https://example.com")`
- After: `>>> h.web_goto("https://example.com")`

**Line 74**: `web_click` function
- Before: `>>> web_click("button")`
- After: `>>> h.web_click("button")`

**Line 105**: `web_start` function
- Before: `return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}`
- After: `return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}`

**Line 119**: `web_start` function
- Before: `return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}`
- After: `return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}`

... and 20 more changes

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\web_automation_integrated.py
Changes: 4

**Line 526**: `append` function
- Before: `script_lines.append(f'    "{k}": "{v}",')`
- After: `script_lines.h.append(f'    "{k}": "{v}",')`

**Line 527**: `append` function
- Before: `script_lines.append('}')`
- After: `script_lines.h.append('}')`

**Line 528**: `append` function
- Before: `script_lines.append('')`
- After: `script_lines.h.append('')`

**Line 603**: `write` function
- Before: `f.write(script)`
- After: `f.h.write(script)`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\web_automation_manager.py
Changes: 1

**Line 82**: `append` function
- Before: `instances.append({`
- After: `instances.h.append({`

### C:\Users\82106\Desktop\ai-coding-brain-mcp\python\api\web_automation_recorder.py
Changes: 33

**Line 44**: `append` function
- Before: `self.actions.append(action)`
- After: `self.actions.h.append(action)`

**Line 148**: `append` function
- Before: `lines.append(f'            # 액션 {index + 1}: {action_type}')`
- After: `lines.h.append(f'            # 액션 {index + 1}: {action_type}')`

**Line 152**: `append` function
- Before: `lines.append(f'            print("🌐 페이지 이동: {url}")')`
- After: `lines.h.append(f'            print("🌐 페이지 이동: {url}")')`

**Line 153**: `append` function
- Before: `lines.append(f'            result = web.go_to_page("{url}")')`
- After: `lines.h.append(f'            result = web.go_to_page("{url}")')`

**Line 154**: `append` function
- Before: `lines.append('            if not result["success"]:')`
- After: `lines.h.append('            if not result["success"]:')`

... and 28 more changes

