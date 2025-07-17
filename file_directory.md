# 📁 프로젝트 파일·디렉터리 구조

생성일시: 2025-07-17 10:47:42

```
ai-coding-brain-mcp/
├── .env
├── .gitignore
├── ai-coding-brain-mcp_7490a912_design_v2.md
├── ai-coding-brain-mcp_7490a912_report_20250714.md
├── ai-coding-brain-preferences-v4.md
├── ai_coding_brain_helpers.py.backup2_20250715_143829
├── build.sh
├── check_compile.bat
├── check_find_function.py
├── CLAUDE.md
├── claude_todos.json
├── code_modification_guide.md
├── code_ops_guide.md
├── compile_check.bat
├── dist/
│   ├── core/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── file.d.ts
│   │   │   │   ├── file.d.ts.map
│   │   │   │   ├── file.js
│   │   │   │   ├── file.js.map
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.d.ts.map
│   │   │   │   ├── index.js
│   │   │   │   ├── index.js.map
│   │   │   │   ├── project.d.ts
│   │   │   │   ├── project.d.ts.map
│   │   │   │   ├── project.js
│   │   │   │   └── project.js.map
│   │   │   ├── index.d.ts
│   │   │   ├── index.d.ts.map
│   │   │   ├── index.js
│   │   │   ├── index.js.map
│   │   │   └── repositories/
│   │   │       ├── file-repository.d.ts
│   │   │       ├── file-repository.d.ts.map
│   │   │       ├── file-repository.js
│   │   │       ├── file-repository.js.map
│   │   │       ├── index.d.ts
│   │   │       ├── index.d.ts.map
│   │   │       ├── index.js
│   │   │       ├── index.js.map
│   │   │       ├── project-repository.d.ts
│   │   │       ├── project-repository.d.ts.map
│   │   │       ├── project-repository.js
│   │   │       └── project-repository.js.map
│   │   ├── index.d.ts
│   │   ├── index.d.ts.map
│   │   ├── index.js
│   │   ├── index.js.map
│   │   └── infrastructure/
│   │       ├── filesystem/
│   │       │   ├── fs-file-repository.d.ts
│   │       │   ├── fs-file-repository.d.ts.map
│   │       │   ├── fs-file-repository.js
│   │       │   ├── fs-file-repository.js.map
│   │       │   ├── fs-project-repository.d.ts
│   │       │   ├── fs-project-repository.d.ts.map
│   │       │   ├── fs-project-repository.js
│   │       │   ├── fs-project-repository.js.map
│   │       │   ├── index.d.ts
│   │       │   ├── index.d.ts.map
│   │       │   ├── index.js
│   │       │   ├── index.js.map
│   │       │   ├── repository-factory.d.ts
│   │       │   ├── repository-factory.d.ts.map
│   │       │   ├── repository-factory.js
│   │       │   └── repository-factory.js.map
│   │       ├── index.d.ts
│   │       ├── index.d.ts.map
│   │       ├── index.js
│   │       └── index.js.map
│   ├── handlers/
│   │   ├── execute-code-handler.d.ts
│   │   ├── execute-code-handler.d.ts.map
│   │   ├── execute-code-handler.js
│   │   └── execute-code-handler.js.map
│   ├── index.d.ts
│   ├── index.d.ts.map
│   ├── index.js
│   ├── index.js.map
│   ├── services/
│   │   ├── logger.d.ts
│   │   ├── logger.d.ts.map
│   │   ├── logger.js
│   │   └── logger.js.map
│   ├── tools/
│   │   ├── schemas/
│   │   │   ├── execute-code.d.ts
│   │   │   ├── execute-code.d.ts.map
│   │   │   ├── execute-code.js
│   │   │   ├── execute-code.js.map
│   │   │   ├── restart-repl.d.ts
│   │   │   ├── restart-repl.d.ts.map
│   │   │   ├── restart-repl.js
│   │   │   └── restart-repl.js.map
│   │   ├── tool-definitions.d.ts
│   │   ├── tool-definitions.d.ts.map
│   │   ├── tool-definitions.js
│   │   ├── tool-definitions.js.map
│   │   ├── tool-definitions_backup.d.ts
│   │   ├── tool-definitions_backup.d.ts.map
│   │   ├── tool-definitions_backup.js
│   │   └── tool-definitions_backup.js.map
│   ├── types/
│   │   ├── tool-interfaces.d.ts
│   │   ├── tool-interfaces.d.ts.map
│   │   ├── tool-interfaces.js
│   │   └── tool-interfaces.js.map
│   └── utils/
│       ├── helpers_integration.d.ts
│       ├── helpers_integration.d.ts.map
│       ├── helpers_integration.js
│       ├── helpers_integration.js.map
│       ├── hybrid-helper-system.d.ts
│       ├── hybrid-helper-system.d.ts.map
│       ├── hybrid-helper-system.js
│       ├── hybrid-helper-system.js.map
│       ├── indent-helper.d.ts
│       ├── indent-helper.d.ts.map
│       ├── indent-helper.js
│       ├── indent-helper.js.map
│       ├── logger.d.ts
│       ├── logger.d.ts.map
│       ├── logger.js
│       ├── logger.js.map
│       ├── python-path.d.ts
│       ├── python-path.d.ts.map
│       ├── python-path.js
│       └── python-path.js.map
├── docs/
│   ├── AI_HELPERS_GUIDE.md
│   ├── ai_helpers_v2_verification_report.md
│   ├── design/
│   │   └── python_helpers_validation_task03_code_analysis_design_20250714.md
│   ├── development_process_quick_ref.md
│   ├── diagnostics/
│   │   └── workflow_protocol_diagnostic_report.md
│   ├── error/
│   ├── event_system_analysis.json
│   ├── execute_code_advanced_guide.md
│   ├── execute_code_ai_revolution.md
│   ├── execute_code_migration_guide.md
│   ├── execute_code_user_prompt_supplement.md
│   ├── execution_tracking_system.md
│   ├── ez_code_guide.md
│   ├── helper_result_practical_examples.md
│   ├── helper_result_return_values.md
│   ├── helper_result_usage_guide.md
│   ├── HELPERS_METHOD_TYPES.md
│   ├── helpers_read_file_guide.md
│   ├── integrated_workflow_guide.md
│   ├── integration/
│   │   ├── flow_project_workflow_integration.md
│   │   ├── summary.txt
│   │   └── workflow_helper_integration.md
│   ├── integration_report_v2.md
│   ├── interactive_system_guide.md
│   ├── kanban_workflow_guide.md.backup_1752595517
│   ├── plan_summary_08b58fa6.md
│   ├── plan_summary_62416255.md
│   ├── plan_summary_a9023775.md
│   ├── project_management_quick_ref.md
│   ├── protocol/
│   │   └── workflow_protocol_communication.md
│   ├── protocol_api_documentation.md
│   ├── protocol_migration_guide.md
│   ├── repl_playwright_complete_guide.md
│   ├── repl_playwright_usage.md
│   ├── report/
│   │   ├── git_add_error_fix_report_20250714.md
│   │   ├── git_module_cleanup_report_20250714.md
│   │   └── system_efficiency_evaluation_20250714.md
│   ├── safe_execution_v2_guide.md
│   ├── safe_helper_functions.md
│   ├── safe_helpers_guide.md
│   ├── tasks/
│   │   ├── 20250713_task_1b12e231.md
│   │   ├── 20250713_task_21dfb9f3.md
│   │   ├── 20250713_task_23799501.md
│   │   ├── 20250713_task_2f06d570.md
│   │   ├── 20250713_task_320615c4.md
│   │   ├── 20250713_task_39f7486a.md
│   │   ├── 20250713_task_55d7f55d.md
│   │   ├── 20250713_task_5d669107.md
│   │   ├── 20250713_task_abdbaf7d.md
│   │   ├── 20250713_task_ac583af0.md
│   │   ├── 20250713_task_faf7c331.md
│   │   └── 20250713_task_fd1aac4c.md
│   ├── user_preferences_v50.md
│   ├── user_preferences_v51.md
│   ├── user_prompt_ai_autonomy.md
│   ├── user_prompt_guide.md
│   ├── user_prompt_v2.md
│   ├── v2_integration_report.md
│   ├── web_automation_recorder_design.md
│   ├── web_automation_recording_guide.md
│   ├── workflow_integration_report.md
│   ├── workflow_migration_guide.md
│   ├── workflow_protocol_integration_report.md
│   ├── workflow_replacement_complete.md
│   ├── workflow_replacement_guide.md
│   └── workflow_reports/
│       ├── ai-coding-brain-mcp_commands_implementation_report_20250714_004244.md
│       ├── ai-coding-brain-mcp_error_analysis_20250714_003640.md
│       ├── ai-coding-brain-mcp_filesystem_test_report_20250714.md
│       ├── ai-coding-brain-mcp_git_test_7490a912_complete_20250714_062129.md
│       ├── ai-coding-brain-mcp_git_test_7490a912_error_20250714_062046.md
│       ├── ai-coding-brain-mcp_helpers_test_plan_design_v1.md
│       ├── ai-coding-brain-mcp_jwt_auth_error_ImportError_205451.md
│       ├── ai-coding-brain-mcp_jwt_auth_system_jwt_token_design_v1.md
│       ├── ai-coding-brain-mcp_jwt_auth_system_jwt_token_report_20250713.md
│       ├── ai-coding-brain-mcp_test_duplicate_task_design_v1.md
│       ├── ai-coding-brain-mcp_test_duplicate_task_report_20250714.md
│       └── ai-coding-brain-mcp_workflow_test_final_report_20250714_003350.md
├── examples/
│   ├── test_async_web.py
│   └── web_automation_recording_examples.py
├── file_directory.md
├── generated_scripts/
│   ├── naver_allstar_search_manual.py
│   ├── naver_simple.py
│   ├── README.md
│   ├── web_auto_20250713_164354.json
│   └── web_auto_20250713_164354.py
├── google_playwright_search.png
├── helper_test_final_results.json
├── helper_test_results.json
├── logs/
│   ├── active_ai_instruction.json
│   ├── active_errors.json
│   ├── ai_instructions.json
│   ├── error_history.json
│   ├── file/
│   │   └── file_20250710.jsonl
│   ├── git/
│   │   └── git_20250710.jsonl
│   ├── log_manager_config.json
│   ├── system/
│   │   └── system_20250710.jsonl
│   ├── task_completions.json
│   └── workflow/
│       └── workflow_20250710.jsonl
├── mcp.json
├── memory/
│   ├── backup_test-project-1_1752530534.json
│   ├── backup_test-project-1_1752530579.json
│   ├── backup_test-project-2_1752530534.json
│   ├── backups/
│   │   ├── backup_ai-coding-brain-mcp_1752531932.json
│   │   └── backup_ai-coding-brain-mcp_1752554358.json
│   ├── checkpoints/
│   │   ├── checkpoint_1.json
│   │   ├── checkpoint_10.json
│   │   ├── checkpoint_100.json
│   │   ├── checkpoint_101.json
│   │   ├── checkpoint_102.json
│   │   ├── checkpoint_103.json
│   │   ├── checkpoint_104.json
│   │   ├── checkpoint_105.json
│   │   ├── checkpoint_106.json
│   │   ├── checkpoint_107.json
│   │   ├── checkpoint_108.json
│   │   ├── checkpoint_109.json
│   │   ├── checkpoint_11.json
│   │   ├── checkpoint_110.json
│   │   ├── checkpoint_111.json
│   │   ├── checkpoint_112.json
│   │   ├── checkpoint_113.json
│   │   ├── checkpoint_114.json
│   │   ├── checkpoint_115.json
│   │   ├── checkpoint_116.json
│   │   ├── checkpoint_117.json
│   │   ├── checkpoint_118.json
│   │   ├── checkpoint_119.json
│   │   ├── checkpoint_12.json
│   │   ├── checkpoint_120.json
│   │   ├── checkpoint_121.json
│   │   ├── checkpoint_122.json
│   │   ├── checkpoint_123.json
│   │   ├── checkpoint_124.json
│   │   ├── checkpoint_125.json
│   │   ├── checkpoint_126.json
│   │   ├── checkpoint_127.json
│   │   ├── checkpoint_128.json
│   │   ├── checkpoint_129.json
│   │   ├── checkpoint_13.json
│   │   ├── checkpoint_130.json
│   │   ├── checkpoint_131.json
│   │   ├── checkpoint_132.json
│   │   ├── checkpoint_133.json
│   │   ├── checkpoint_134.json
│   │   ├── checkpoint_135.json
│   │   ├── checkpoint_136.json
│   │   ├── checkpoint_137.json
│   │   ├── checkpoint_138.json
│   │   ├── checkpoint_139.json
│   │   ├── checkpoint_14.json
│   │   ├── checkpoint_140.json
│   │   ├── checkpoint_141.json
│   │   ├── checkpoint_142.json
│   │   ├── checkpoint_143.json
│   │   ├── checkpoint_144.json
│   │   ├── checkpoint_145.json
│   │   ├── checkpoint_146.json
│   │   ├── checkpoint_147.json
│   │   ├── checkpoint_148.json
│   │   ├── checkpoint_149.json
│   │   ├── checkpoint_15.json
│   │   ├── checkpoint_150.json
│   │   ├── checkpoint_151.json
│   │   ├── checkpoint_152.json
│   │   ├── checkpoint_153.json
│   │   ├── checkpoint_154.json
│   │   ├── checkpoint_155.json
│   │   ├── checkpoint_156.json
│   │   ├── checkpoint_157.json
│   │   ├── checkpoint_158.json
│   │   ├── checkpoint_159.json
│   │   ├── checkpoint_16.json
│   │   ├── checkpoint_160.json
│   │   ├── checkpoint_161.json
│   │   ├── checkpoint_162.json
│   │   ├── checkpoint_163.json
│   │   ├── checkpoint_164.json
│   │   ├── checkpoint_165.json
│   │   ├── checkpoint_166.json
│   │   ├── checkpoint_167.json
│   │   ├── checkpoint_168.json
│   │   ├── checkpoint_169.json
│   │   ├── checkpoint_17.json
│   │   ├── checkpoint_170.json
│   │   ├── checkpoint_171.json
│   │   ├── checkpoint_172.json
│   │   ├── checkpoint_173.json
│   │   ├── checkpoint_174.json
│   │   ├── checkpoint_175.json
│   │   ├── checkpoint_176.json
│   │   ├── checkpoint_177.json
│   │   ├── checkpoint_178.json
│   │   ├── checkpoint_179.json
│   │   ├── checkpoint_18.json
│   │   ├── checkpoint_180.json
│   │   ├── checkpoint_181.json
│   │   ├── checkpoint_182.json
│   │   ├── checkpoint_183.json
│   │   ├── checkpoint_184.json
│   │   ├── checkpoint_185.json
│   │   ├── checkpoint_186.json
│   │   ├── checkpoint_187.json
│   │   ├── checkpoint_188.json
│   │   ├── checkpoint_189.json
│   │   ├── checkpoint_19.json
│   │   ├── checkpoint_190.json
│   │   ├── checkpoint_191.json
│   │   ├── checkpoint_192.json
│   │   ├── checkpoint_193.json
│   │   ├── checkpoint_2.json
│   │   ├── checkpoint_20.json
│   │   ├── checkpoint_21.json
│   │   ├── checkpoint_22.json
│   │   ├── checkpoint_23.json
│   │   ├── checkpoint_24.json
│   │   ├── checkpoint_25.json
│   │   ├── checkpoint_26.json
│   │   ├── checkpoint_27.json
│   │   ├── checkpoint_28.json
│   │   ├── checkpoint_29.json
│   │   ├── checkpoint_3.json
│   │   ├── checkpoint_30.json
│   │   ├── checkpoint_31.json
│   │   ├── checkpoint_32.json
│   │   ├── checkpoint_33.json
│   │   ├── checkpoint_34.json
│   │   ├── checkpoint_35.json
│   │   ├── checkpoint_36.json
│   │   ├── checkpoint_37.json
│   │   ├── checkpoint_38.json
│   │   ├── checkpoint_39.json
│   │   ├── checkpoint_4.json
│   │   ├── checkpoint_40.json
│   │   ├── checkpoint_41.json
│   │   ├── checkpoint_42.json
│   │   ├── checkpoint_43.json
│   │   ├── checkpoint_44.json
│   │   ├── checkpoint_45.json
│   │   ├── checkpoint_46.json
│   │   ├── checkpoint_47.json
│   │   ├── checkpoint_48.json
│   │   ├── checkpoint_49.json
│   │   ├── checkpoint_5.json
│   │   ├── checkpoint_50.json
│   │   ├── checkpoint_51.json
│   │   ├── checkpoint_52.json
│   │   ├── checkpoint_53.json
│   │   ├── checkpoint_54.json
│   │   ├── checkpoint_55.json
│   │   ├── checkpoint_56.json
│   │   ├── checkpoint_57.json
│   │   ├── checkpoint_58.json
│   │   ├── checkpoint_59.json
│   │   ├── checkpoint_6.json
│   │   ├── checkpoint_60.json
│   │   ├── checkpoint_61.json
│   │   ├── checkpoint_62.json
│   │   ├── checkpoint_63.json
│   │   ├── checkpoint_64.json
│   │   ├── checkpoint_65.json
│   │   ├── checkpoint_66.json
│   │   ├── checkpoint_67.json
│   │   ├── checkpoint_68.json
│   │   ├── checkpoint_69.json
│   │   ├── checkpoint_7.json
│   │   ├── checkpoint_70.json
│   │   ├── checkpoint_71.json
│   │   ├── checkpoint_72.json
│   │   ├── checkpoint_73.json
│   │   ├── checkpoint_74.json
│   │   ├── checkpoint_75.json
│   │   ├── checkpoint_76.json
│   │   ├── checkpoint_77.json
│   │   ├── checkpoint_78.json
│   │   ├── checkpoint_79.json
│   │   ├── checkpoint_8.json
│   │   ├── checkpoint_80.json
│   │   ├── checkpoint_81.json
│   │   ├── checkpoint_82.json
│   │   ├── checkpoint_83.json
│   │   ├── checkpoint_84.json
│   │   ├── checkpoint_85.json
│   │   ├── checkpoint_86.json
│   │   ├── checkpoint_87.json
│   │   ├── checkpoint_88.json
│   │   ├── checkpoint_89.json
│   │   ├── checkpoint_9.json
│   │   ├── checkpoint_90.json
│   │   ├── checkpoint_91.json
│   │   ├── checkpoint_92.json
│   │   ├── checkpoint_94.json
│   │   ├── checkpoint_96.json
│   │   ├── checkpoint_97.json
│   │   ├── checkpoint_98.json
│   │   └── checkpoint_99.json
│   ├── cleanup_plan.json
│   ├── context.json
│   ├── project_context.json
│   ├── protocol_test_report.json
│   ├── refactoring_analysis.json
│   ├── session_state.json
│   ├── workflow.json
│   ├── workflow_backup.json
│   ├── workflow_events.json
│   ├── workflow_history.json
│   └── workflows/
│       └── unified_test_project/
│           └── workflow_WF_1752503643039_0001_e66123.json
├── naver_baseball.png
├── naver_main.png
├── npm_builder_design_from_o3.md
├── package-lock.json
├── package.json
├── PROJECT_CONTEXT.md
├── projects/
│   ├── ai-coding-brain-mcp/
│   │   ├── context.json
│   │   ├── docs/
│   │   ├── file_directory.md
│   │   ├── memory/
│   │   │   └── context.json
│   │   ├── README.md
│   │   ├── src/
│   │   └── tests/
│   ├── ai-helpers-v2-test/
│   │   ├── context.json
│   │   └── README.md
│   ├── integrated-demo/
│   │   ├── file_directory.md
│   │   └── memory/
│   │       └── context.json
│   ├── test-project-1/
│   │   ├── docs/
│   │   ├── file_directory.md
│   │   ├── memory/
│   │   │   └── context.json
│   │   ├── README.md
│   │   ├── src/
│   │   ├── test_helpers.md
│   │   └── tests/
│   ├── test-project-2/
│   │   ├── docs/
│   │   ├── file_directory.md
│   │   ├── memory/
│   │   │   └── context.json
│   │   ├── README.md
│   │   ├── src/
│   │   └── tests/
│   └── test-v2-project/
│       ├── context.json
│       ├── file_directory.md
│       └── README.md
├── pyproject.toml
├── python/
│   ├── __init__.py
│   ├── ai_helpers_v2/
│   │   ├── __init__.py
│   │   ├── code_ops.py
│   │   ├── core.py
│   │   ├── ez_code.py
│   │   ├── file_ops.py
│   │   ├── git_ops.py
│   │   ├── llm_ops.py
│   │   ├── project_ops.py
│   │   └── search_ops.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── backup_old_web_automation/
│   │   │   ├── web_automation.py
│   │   │   ├── web_automation_async.py
│   │   │   └── web_automation_extended.py
│   │   ├── image_generator.py
│   │   ├── web_automation_helpers.py
│   │   ├── web_automation_recorder.py
│   │   └── web_automation_repl.py
│   ├── essential_helpers.py
│   ├── info_ops.py
│   ├── json_repl_session.py
│   ├── json_repl_session.py.backup_context
│   ├── npm_builder.py
│   ├── npm_helpers.py
│   ├── persistent_history.py
│   ├── q_tools.py
│   ├── q_tools_refactored.py
│   ├── safe_exec_helpers.py
│   ├── safe_execution_v2.py
│   ├── safe_helpers.py
│   ├── safe_wrapper.py
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── dispatcher.py
│   │   ├── improved_manager.py
│   │   ├── messaging/
│   │   │   ├── __init__.py
│   │   │   └── message_controller.py
│   │   ├── models.py
│   │   ├── README.md
│   │   └── workflow_helper.py
│   ├── workflow_extension.py
│   └── workflow_helper.py
├── q_tools_guide_v2.md
├── README.md
├── recommended_helpers.md
├── session_state.json
├── src/
│   ├── core/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── file.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── project.ts
│   │   │   ├── index.ts
│   │   │   └── repositories/
│   │   │       ├── file-repository.ts
│   │   │       ├── index.ts
│   │   │       └── project-repository.ts
│   │   ├── index.ts
│   │   └── infrastructure/
│   │       ├── filesystem/
│   │       │   ├── fs-file-repository.ts
│   │       │   ├── fs-project-repository.ts
│   │       │   ├── index.ts
│   │       │   └── repository-factory.ts
│   │       └── index.ts
│   ├── handlers/
│   │   └── execute-code-handler.ts
│   ├── index.ts
│   ├── index.ts.backup
│   ├── services/
│   │   └── logger.ts
│   ├── tools/
│   │   ├── descriptions/
│   │   │   ├── execute-code.md
│   │   │   └── restart-repl.md
│   │   ├── schemas/
│   │   │   ├── execute-code.ts
│   │   │   └── restart-repl.ts
│   │   ├── tool-definitions.ts
│   │   ├── tool-definitions.ts.backup
│   │   ├── tool-definitions.ts.backup_20250715_144256
│   │   ├── tool-definitions.ts.backup_20250715_222152
│   │   ├── tool-definitions.ts.backup_20250716_201635
│   │   └── tool-definitions_backup.ts
│   ├── types/
│   │   └── tool-interfaces.ts
│   └── utils/
│       ├── helpers_integration.ts
│       ├── hybrid-helper-system.ts
│       ├── improved_helpers.py
│       ├── indent-helper.ts
│       ├── logger.ts
│       └── python-path.ts
├── startup_script.py
├── test_ai_helpers_v2.md
├── test_code.py
├── test_code.py.backup
├── test_git_helpers/
│   ├── test_file_0.txt
│   ├── test_file_1.txt
│   └── test_file_2.txt
├── test_helpers/
│   ├── subdir/
│   │   └── sub_file.txt
│   ├── test.json
│   ├── test1.txt
│   ├── test2.txt
│   ├── test_code.py
│   └── test_code.py.backup
├── test_helpers.json
├── test_helpers.txt
├── test_json_repl.py
├── test_q_functions.py
├── test_replace.py.backup
├── test_results/
│   └── unified_test.txt
├── test_search.py
├── test_search_sample.py
├── test_special_names.py
├── test_temp.txt
├── tests/
│   ├── test_safe_execution_v2.py
│   └── workflow/
│       └── test_event_publishing.py
├── threaded_test.png
├── tmpwo0ybiyt
├── tsconfig.json
├── workflow.json
└── workflow_history.json
```

*(자동 생성: /a 명령)*