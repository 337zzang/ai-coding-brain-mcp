"""
헬퍼 함수 사용법 가이드
"""

HELPER_USAGE_GUIDE = {
    "파일 작업": {
        "read_file": {
            "설명": "파일 내용 읽기",
            "사용법": "content = helpers.read_file('path/to/file.txt')",
            "매개변수": {
                "path": "읽을 파일 경로",
                "offset": "시작 줄 번호 (선택)",
                "length": "읽을 줄 수 (선택)"
            },
            "예시": [
                "helpers.read_file('README.md')",
                "helpers.read_file('large.txt', offset=100, length=50)"
            ]
        },
        "create_file": {
            "설명": "새 파일 생성 또는 덮어쓰기",
            "사용법": "helpers.create_file('path/to/file.txt', 'content')",
            "예시": "helpers.create_file('output.txt', 'Hello World')"
        },
        "write_file": {
            "설명": "파일에 내용 쓰기 (추가 가능)",
            "사용법": "helpers.write_file('path', 'content', mode='append')",
            "매개변수": {
                "mode": "'rewrite' 또는 'append'"
            }
        }
    },

    "Git 작업": {
        "git_status": {
            "설명": "Git 저장소 상태 확인",
            "사용법": "status = helpers.git_status()",
            "반환값": "수정된 파일, 추적되지 않은 파일 목록"
        },
        "git_diff": {
            "설명": "Git 변경사항 확인",
            "사용법": "diff = helpers.git_diff(file_path)",
            "예시": "helpers.git_diff('src/main.py')"
        },
        "git_add": {
            "설명": "파일을 스테이징",
            "사용법": "helpers.git_add(file_path)"
        }
    },

    "검색 작업": {
        "search_files": {
            "설명": "파일명으로 검색",
            "사용법": "files = helpers.search_files('path', 'pattern')",
            "예시": "helpers.search_files('.', '*.py')"
        },
        "search_in_files": {
            "설명": "파일 내용 검색",
            "사용법": "results = helpers.search_in_files('path', 'text')",
            "예시": "helpers.search_in_files('src', 'TODO')"
        }
    },

    "워크플로우": {
        "show_workflow_status": {
            "설명": "현재 워크플로우 상태 표시",
            "사용법": "helpers.show_workflow_status()"
        },
        "update_task_status": {
            "설명": "현재 태스크 상태 업데이트",
            "사용법": "helpers.update_task_status('completed', '작업 완료')",
            "매개변수": {
                "status": "'in_progress', 'completed', 'failed'",
                "note": "상태 변경 이유 (선택)"
            }
        }
    }
}

def show_helper_guide(category: str = None, function: str = None):
    """헬퍼 함수 사용법 가이드 표시"""
    print("\n📚 헬퍼 함수 사용법 가이드")
    print("=" * 50)

    if function:
        # 특정 함수 검색
        for cat, funcs in HELPER_USAGE_GUIDE.items():
            if function in funcs:
                print(f"\n카테고리: {cat}")
                func_info = funcs[function]
                print(f"함수: {function}")
                print(f"설명: {func_info['설명']}")
                print(f"사용법: {func_info['사용법']}")

                if '매개변수' in func_info:
                    print("\n매개변수:")
                    for param, desc in func_info['매개변수'].items():
                        print(f"  - {param}: {desc}")

                if '예시' in func_info:
                    print("\n예시:")
                    examples = func_info['예시']
                    if isinstance(examples, list):
                        for ex in examples:
                            print(f"  {ex}")
                    else:
                        print(f"  {examples}")
                return

        print(f"❌ '{function}' 함수를 찾을 수 없습니다.")

    elif category:
        # 카테고리별 표시
        if category in HELPER_USAGE_GUIDE:
            print(f"\n카테고리: {category}")
            for func_name, info in HELPER_USAGE_GUIDE[category].items():
                print(f"\n• {func_name}: {info['설명']}")
                print(f"  사용법: {info['사용법']}")
        else:
            print(f"❌ '{category}' 카테고리를 찾을 수 없습니다.")

    else:
        # 전체 카테고리 표시
        print("\n사용 가능한 카테고리:")
        for cat in HELPER_USAGE_GUIDE.keys():
            funcs = list(HELPER_USAGE_GUIDE[cat].keys())
            print(f"\n• {cat}")
            for func in funcs[:3]:
                print(f"  - {func}")
            if len(funcs) > 3:
                print(f"  ... 외 {len(funcs)-3}개")

        print("\n💡 사용법:")
        print("  - 카테고리별: show_helper_guide('파일 작업')")
        print("  - 특정 함수: show_helper_guide(function='read_file')")
