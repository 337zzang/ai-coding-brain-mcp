#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JSON 관련 유틸리티 함수들
"""

from pathlib import Path

def safe_json_write(file_path, data, encoding='utf-8'):

    """원자적 JSON 파일 저장 - 파일 손상 방지"""

    import json

    import os

    import tempfile



    file_path = Path(file_path)



    # 임시 파일을 같은 디렉토리에 생성 (원자적 교체를 위해)

    with tempfile.NamedTemporaryFile('w', 

                                   delete=False, 

                                   dir=file_path.parent,

                                   prefix='.tmp_',

                                   suffix='.json',

                                   encoding=encoding) as tmp_file:

        json.dump(data, tmp_file, indent=2, ensure_ascii=False)

        tmp_file.flush()

        os.fsync(tmp_file.fileno())  # 디스크에 완전히 쓰기

        tmp_name = tmp_file.name



    # 원자적 교체 (POSIX에서는 원자적, Windows에서는 덮어쓰기)

    try:

        os.replace(tmp_name, str(file_path))

    except OSError:

        # Windows에서 대상 파일이 있으면 실패할 수 있음

        if os.path.exists(str(file_path)):

            os.remove(str(file_path))

        os.rename(tmp_name, str(file_path))



    def __init__(self):

        """AI Helpers v2 메서드들을 통합"""

        if not AI_HELPERS_V2_LOADED:

            print("⚠️ AI Helpers v2가 로드되지 않았습니다. 기능이 제한될 수 있습니다.")

            return

        

        # 영속적 히스토리 매니저 추가

        self._history_manager = None

            

        # File operations

        self.read_file = read_file

        self.write_file = write_file

        self.create_file = create_file

        self.file_exists = file_exists

        self.exists = file_exists  # 별칭

        self.append_to_file = append_to_file

        self.read_json = read_json

        self.write_json = write_json

        

        # Search operations

        self.search_code = search_code

        self.search_files = search_files

        self.search_in_files = search_code  # 별칭

        self.grep = grep

        self.find_function = find_function

        self.find_class = find_class

        

        # Code operations

        self.parse_with_snippets = parse_with_snippets

        self.insert_block = insert_block

        self.replace_block = replace_block

        

        # Git operations

        self.git_status = git_status

        self.git_add = git_add

        self.git_commit = git_commit

        self.git_branch = git_branch

        self.git_push = git_push

        self.git_pull = git_pull

        

        # Project operations

        self.get_current_project = get_current_project

        self.scan_directory_dict = scan_directory_dict

        self.create_project_structure = create_project_structure

        

        # Core operations

        self.get_metrics = get_metrics

        self.clear_cache = clear_cache

        self.get_execution_history = get_execution_history

        

        # flow_project 구현

        self.flow_project = self._flow_project

        self.cmd_flow_with_context = self._flow_project  # 별칭

        

        # Workflow 시스템 통합

        self.execute_workflow_command = self._execute_workflow_command

        self.get_workflow_status = self._get_workflow_status



        # workflow 메서드 별칭 추가

        def workflow(command=None, *args, **kwargs):

            if command:

                return self._execute_workflow_command(command, *args, **kwargs)

            else:

                return self._get_workflow_status()

        self.workflow = workflow

        self.update_file_directory = self._update_file_directory

        





        # LLM operations (llm_ops)
        try:
            from llm_ops import ask_o3
            self.ask_o3 = ask_o3
        except ImportError:
            pass

