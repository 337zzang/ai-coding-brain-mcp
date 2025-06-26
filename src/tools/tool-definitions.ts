/**
 * AI Coding Brain MCP - Tool Definitions v8.0
 * 핵심 워크플로우 유지, 중복만 제거
 * 
 * 작성일: 2025-06-16
 */

// 도구 정의 타입
interface ToolDefinition {
    name: string;
    description: string;
    inputSchema: {
        type: string;
        properties: Record<string, any>;
        required?: string[];
    };
}

export const toolDefinitions: ToolDefinition[] = [
    {
        name: 'execute_code',
        description: `Python 코드 실행

JSON REPL 세션에서 Python 코드를 실행합니다.
세션 간 변수가 유지되며, 복잡한 작업 수행이 가능합니다.

주요 기능:
- 변수 영속성 (세션 유지)
- 파일 시스템 접근
- 데이터 처리 및 분석
- 프로젝트 관리 작업

사용 가능한 helpers 메서드:
- helpers.scan_directory_dict(path) - 디렉토리 스캔 (딕셔너리 반환)
- helpers.read_file(path) - 파일 읽기
- helpers.create_file(path, content) - 파일 생성/수정
- helpers.search_files_advanced(path, pattern) - 파일명 검색
  예: helpers.search_files_advanced(".", "*.py")
  반환: {'results': [파일정보 리스트]}
- helpers.search_code_content(path, pattern, file_pattern) - 코드 내용 검색
  예: helpers.search_code_content("python", "def", "*.py")
  반환: {'results': [파일별 매치 정보]}
- helpers.replace_block(file, target, new_code) - 코드 블록 교체
- helpers.cmd_flow_with_context(project) - 프로젝트 전환

사용 예:
\`\`\`python
# 디렉토리 구조 파악
files = helpers.scan_directory_dict(".")
print(f"파일: {len(files['files'])}개")
print(f"디렉토리: {len(files['directories'])}개")

# 파일 읽기/쓰기
content = helpers.read_file("config.json")
helpers.create_file("output.txt", content)

# 코드 수정
helpers.replace_block("app.py", "function_name", new_code)
\`\`\``,
        inputSchema: {
            type: 'object',
            properties: {
                code: {
                    type: 'string',
                    description: '실행할 Python 코드'
                },
                language: {
                    type: 'string',
                    description: '프로그래밍 언어',
                    enum: ['python'],
                    default: 'python'
                }
            },
            required: ['code']
        }
    },

    {
        name: 'restart_json_repl',
        description: `JSON REPL 세션 재시작

용도: 메모리 정리, 변수 초기화
기본값: helpers 유지하며 재시작

\`\`\`python
restart_json_repl()  # helpers 유지
restart_json_repl(keep_helpers=False)  # 완전 초기화
\`\`\``,
        inputSchema: {
            type: 'object',
            properties: {
                reason: {
                    type: 'string',
                    description: '재시작 이유',
                    default: '세션 새로고침'
                },
                keep_helpers: {
                    type: 'boolean',
                    description: 'helpers 객체 유지 여부',
                    default: true
                }
            },
            required: []
        }
    },

    

    

    

    {
        name: 'plan_project',
        description: `프로젝트 계획 수립

새로운 작업 계획을 수립합니다.
내부적으로 helpers.cmd_plan()을 실행합니다.

워크플로우:
1. 계획 분석 및 브리핑 제시
2. 사용자 승인 대기  
3. Phase별 작업 자동 생성`,
        inputSchema: {
            type: 'object',
            properties: {
                plan_name: {
                    type: 'string',
                    description: '계획 이름 (선택사항)'
                },
                description: {
                    type: 'string',
                    description: '계획 설명 (선택사항)'
                }
            },
            required: []
        }
    },

    {
        name: 'task_manage',
        description: `작업 관리

작업을 추가, 조회, 수정, 삭제합니다.
내부적으로 helpers.cmd_task()를 실행합니다.

사용 예:
- task_manage("add", "새로운 기능 구현")
- task_manage("list")
- task_manage("done", 1)`,
        inputSchema: {
            type: 'object',
            properties: {
                action: {
                    type: 'string',
                    description: '작업 액션 (add, list, done, remove)',
                    enum: ['add', 'list', 'done', 'remove']
                },
                args: {
                    type: 'array',
                    description: '액션에 따른 인자들',
                    items: {
                        type: 'string'
                    }
                }
            },
            required: ['action']
        }
    },

    {
        name: 'next_task',
        description: `다음 작업 진행,

현재 작업을 완료 처리하고 다음 작업으로 진행합니다.
내부적으로 helpers.cmd_next()를 실행합니다.

워크플로우:
1. 현재 작업 완료 처리
2. 다음 작업 로드
3. 작업 브리핑 제시`,
        inputSchema: {
            type: 'object',
            properties: {},
            required: []
        }
    },


    // ========== Wisdom 시스템 도구 ==========
    {
        name: 'wisdom_stats',
        description: `Wisdom 시스템 통계 조회
        
프로젝트의 축적된 지혜와 통계를 확인합니다.
- 오류 패턴 통계
- 자주 하는 실수들
- 베스트 프랙티스 목록

사용 예:
- wisdom_stats()`,
        inputSchema: {
            type: 'object',
            properties: {},
            required: []
        }
    },
    
    {
        name: 'track_mistake',
        description: `실수 추적 및 기록
        
프로젝트 작업 중 발생한 실수를 추적합니다.
실시간으로 경고 메시지를 표시하고 wisdom에 기록합니다.

사용 예:
- track_mistake("console_usage", "app.ts에서 console.log 사용")
- track_mistake("no_backup", "파일 수정 전 백업 안함")`,
        inputSchema: {
            type: 'object',
            properties: {
                mistake_type: {
                    type: 'string',
                    description: '실수 유형 (console_usage, no_backup, direct_flow 등)'
                },
                context: {
                    type: 'string',
                    description: '실수가 발생한 컨텍스트나 파일명',
                    default: ''
                }
            },
            required: ['mistake_type']
        }
    },
    
    {
        name: 'add_best_practice',
        description: `베스트 프랙티스 추가
        
프로젝트에서 발견한 좋은 방법이나 교훈을 기록합니다.

사용 예:
- add_best_practice("항상 PR 전에 로컬 테스트 실행", "workflow")
- add_best_practice("타입 체크를 먼저 하면 오류 50% 감소", "safety")`,
        inputSchema: {
            type: 'object',
            properties: {
                practice: {
                    type: 'string',
                    description: '베스트 프랙티스 내용'
                },
                category: {
                    type: 'string',
                    description: '카테고리 (general, workflow, safety, performance 등)',
                    default: 'general'
                }
            },
            required: ['practice']
        }
    },

    // ========== 파일 분석 도구 ==========
    {
        name: 'file_analyze',
        description: `파일 분석 도구

ProjectAnalyzer를 사용하여 특정 파일의 상세 정보를 분석합니다.
파일의 구조, 요약, 의존성, 복잡도 등의 정보를 제공합니다.

사용 예:
- file_analyze("python/commands/enhanced_flow.py")
- file_analyze("src/index.ts")

반환 정보:
- 파일 요약
- 클래스/함수 목록
- import 의존성
- 코드 복잡도
- Wisdom 인사이트`,
        inputSchema: {
            type: 'object',
            properties: {
                file_path: {
                    type: 'string',
                    description: '분석할 파일 경로 (프로젝트 루트 기준 상대 경로)'
                },
                update_manifest: {
                    type: 'boolean',
                    description: 'Manifest 업데이트 여부 (기본값: true)',
                    default: true
                }
            },
            required: ['file_path']
        }
    },

    // ========== Git 백업 도구 ==========
    {
        name: 'git_status',
        description: `Git 상태 확인

현재 브랜치와 변경된 파일 목록을 확인합니다.

반환 정보:
- 현재 브랜치
- 수정된 파일
- 추적되지 않는 파일
- 스테이징된 파일`,
        inputSchema: {
            type: 'object',
            properties: {},
            required: []
        }
    },

    {
        name: 'git_commit_smart',
        description: `스마트 Git 커밋 (백업)

변경 사항을 자동으로 커밋하여 백업합니다.
커밋 메시지가 없으면 현재 작업 컨텍스트를 기반으로 자동 생성합니다.

사용 예:
- git_commit_smart() - 자동 메시지
- git_commit_smart("기능 추가: 로그인 API")`,
        inputSchema: {
            type: 'object',
            properties: {
                message: {
                    type: 'string',
                    description: '커밋 메시지 (선택사항)'
                },
                auto_add: {
                    type: 'boolean',
                    description: '변경 사항 자동 스테이징',
                    default: true
                }
            },
            required: []
        }
    },

    {
        name: 'git_branch_smart',
        description: `스마트 브랜치 생성

현재 작업에 맞는 브랜치를 자동으로 생성합니다.
브랜치 이름이 없으면 작업 컨텍스트를 기반으로 자동 생성합니다.

예시:
- task/1-2_로그인구현_20250626
- work/20250626_1430`,
        inputSchema: {
            type: 'object',
            properties: {
                branch_name: {
                    type: 'string',
                    description: '브랜치 이름 (선택사항)'
                },
                base_branch: {
                    type: 'string',
                    description: '기반 브랜치',
                    default: 'main'
                }
            },
            required: []
        }
    },

    {
        name: 'git_rollback_smart',
        description: `안전한 Git 롤백 (복원)

특정 시점으로 코드를 되돌립니다.
롤백 전 현재 상태를 백업 브랜치로 자동 생성합니다.

사용 예:
- git_rollback_smart() - 이전 커밋으로
- git_rollback_smart("abc1234") - 특정 커밋으로`,
        inputSchema: {
            type: 'object',
            properties: {
                target: {
                    type: 'string',
                    description: '롤백 대상 커밋 (선택사항)'
                },
                safe_mode: {
                    type: 'boolean',
                    description: '백업 브랜치 생성 여부',
                    default: true
                }
            },
            required: []
        }
    },

    {
        name: 'git_push',
        description: `원격 저장소로 푸시

로컬 커밋을 GitHub 등 원격 저장소로 전송합니다.

사용 예:
- git_push() - origin으로 현재 브랜치 푸시
- git_push("origin", "main") - 특정 브랜치 푸시`,
        inputSchema: {
            type: 'object',
            properties: {
                remote: {
                    type: 'string',
                    description: '원격 저장소 이름',
                    default: 'origin'
                },
                branch: {
                    type: 'string',
                    description: '브랜치 이름 (선택사항)'
                }
            },
            required: []
        }
    },
    {
        name: 'gitignore_analyze',
        description: `프로젝트 분석 및 .gitignore 제안

프로젝트를 분석하여 .gitignore에 추가해야 할 파일/폴더를 제안합니다.
Python, Node.js, IDE, OS 등 카테고리별로 분류하여 제공합니다.`,
        inputSchema: {
            type: 'object',
            properties: {},
            required: []
        }
    },
    {
        name: 'gitignore_update',
        description: `.gitignore 파일 업데이트

기존 .gitignore 파일에 새로운 패턴을 추가합니다.
중복되는 패턴은 자동으로 제외됩니다.`,
        inputSchema: {
            type: 'object',
            properties: {
                patterns: {
                    type: 'array',
                    items: { type: 'string' },
                    description: '추가할 패턴 리스트 (예: ["*.log", "*.tmp", "cache/"])'
                },
                category: {
                    type: 'string',
                    description: '카테고리 이름 (주석으로 추가됨)'
                }
            },
            required: ['patterns']
        }
    },
    {
        name: 'gitignore_create',
        description: `새로운 .gitignore 파일 생성

프로젝트에 맞는 .gitignore 파일을 자동으로 생성합니다.
카테고리를 지정하거나, 지정하지 않으면 모든 일반적인 패턴을 포함합니다.`,
        inputSchema: {
            type: 'object',
            properties: {
                categories: {
                    type: 'array',
                    items: { type: 'string' },
                    description: '포함할 카테고리 (Python, Node.js, IDE, OS, 환경 설정, 로그 및 임시 파일, 백업 파일)'
                }
            },
            required: []
        }
    },
    {
        name: 'flow_project',
        description: `프로젝트 전환 및 컨텍스트 로드
        
지정된 프로젝트로 전환하고 전체 컨텍스트를 로드합니다.
내부적으로 helpers.cmd_flow_with_context()를 실행합니다.

주요 기능:
- 이전 프로젝트 컨텍스트 자동 백업
- 새 프로젝트로 전환
- 전체 컨텍스트 로드 (계획, 작업, 분석 정보 등)
- file_directory.md 자동 생성/업데이트
- Wisdom 시스템 활성화
- 프로젝트 브리핑 표시

사용 예:
- flow_project("my-project")
- flow_project("ai-coding-brain-mcp")`,
        inputSchema: {
            type: 'object',
            properties: {
                project_name: {
                    type: 'string',
                    description: '전환할 프로젝트 이름'
                }
            },
            required: ['project_name']
        }
    },
    
    // AI 이미지 생성 도구
      {
    name: 'toggle_api',
    description: 'API를 활성화하거나 비활성화합니다. 이미지 생성, 번역, 음성 합성 등 다양한 API를 on/off 할 수 있습니다.',
    inputSchema: {
      type: 'object',
      properties: {
        api_name: {
          type: 'string',
          description: 'API 이름 (예: image, translator, voice 등)'
        },
        enabled: {
          type: 'boolean',
          description: '활성화 여부 (기본값: true)',
          default: true
        }
      },
      required: ['api_name']
    },
    // Handler is defined in index.ts
  },
  {
    name: 'list_apis',
    description: '사용 가능한 API 목록과 활성화 상태를 조회합니다.',
    inputSchema: {
      type: 'object',
      properties: {}
    },
    // Handler is defined in index.ts
  },
];