import { ExecuteCodeHandler } from './execute-code-handler.js';

// 타입 정의
interface ToolResponse {
    content: Array<{
        type: string;
        text: string;
    }>;
}

// 전역 변수 키
const GLOBAL_VARS_KEY = 'workflow_global_vars';

/**
 * 변수 로드 코드 생성
 */
function generateLoadVars(): string {
    return `
# 이전 변수 복원
_saved_vars = helpers.get_value('${GLOBAL_VARS_KEY}', {})
if _saved_vars:
    for k, v in _saved_vars.items():
        globals()[k] = v
    print(f"♻️ {len(_saved_vars)}개 변수 복원됨")
`;
}

/**
 * 변수 저장 코드 생성
 */
function generateSaveVars(): string {
    return `
# 현재 세션의 변수들을 저장
_vars_to_save = {}
_exclude = {'__builtins__', '__name__', '__doc__', '__package__', '__loader__', '__spec__', '__file__', '__cached__', '_saved_vars', '_vars_to_save', '_exclude'}
for k, v in list(globals().items()):
    if not k.startswith('_') and k not in _exclude:
        try:
            import json
            json.dumps(v)  # JSON 직렬화 가능한지 테스트
            _vars_to_save[k] = v
        except:
            pass  # 직렬화 불가능한 객체는 제외

if _vars_to_save:
    helpers.update_cache('${GLOBAL_VARS_KEY}', _vars_to_save)
    print(f"💾 {len(_vars_to_save)}개 변수 저장됨")
`;
}

/**
 * 파일 분석 핸들러
 * ProjectAnalyzer를 사용하여 파일을 분석합니다.
 */
export async function handleFileAnalyze(params: { 
    file_path: string; 
    update_manifest?: boolean 
}): Promise<ToolResponse> {
    const updateManifest = params.update_manifest !== undefined ? params.update_manifest : true;
    
    const code = `
${generateLoadVars()}

# 필요한 모듈 import
from commands.file_analyze import analyze_file
from smart_print import smart_print

# 파일 분석 실행
result = analyze_file("${params.file_path}", update_manifest=${updateManifest ? 'True' : 'False'})

# 결과 출력
if result.get('success'):
    # 파일 정보 헤더
    smart_print(f"📄 파일 분석: {result['file_path']}")
    smart_print("=" * 60)
    
    # 기본 정보
    info = result['info']
    smart_print(f"**언어**: {info.get('language', 'unknown')}")
    smart_print(f"**크기**: {info.get('size', 0):,} bytes")
    smart_print(f"**최종 수정**: {info.get('last_modified', 'unknown')}")
    smart_print(f"**요약**: {info.get('summary', 'No summary')}")
    
    # 구조 정보
    smart_print("\\n### 📊 구조")
    smart_print(f"- 클래스: {len(info.get('classes', []))}개")
    smart_print(f"- 함수: {len(info.get('functions', []))}개")
    
    # 주요 함수/클래스 목록
    if info.get('classes'):
        smart_print("\\n**클래스 목록**:")
        for cls in info['classes'][:5]:
            smart_print(f"  - {cls['name']} ({len(cls.get('methods', []))}개 메서드)")
    
    if info.get('functions'):
        smart_print("\\n**주요 함수**:")
        for func in info['functions'][:10]:
            smart_print(f"  - {func['name']}({', '.join(func.get('params', []))})")
    
    # 의존성 정보
    imports = info.get('imports', {})
    if imports.get('internal') or imports.get('external'):
        smart_print("\\n### 🔗 의존성")
        if imports.get('internal'):
            smart_print(f"**내부 모듈**: {', '.join(imports['internal'][:5])}")
        if imports.get('external'):
            smart_print(f"**외부 라이브러리**: {', '.join(imports['external'][:5])}")
    
    # Wisdom 인사이트
    wisdom = info.get('wisdom_insights', {})
    if wisdom.get('potential_issues') or wisdom.get('improvement_suggestions'):
        smart_print("\\n### 💡 Wisdom 인사이트")
        for issue in wisdom.get('potential_issues', [])[:3]:
            smart_print(f"  ⚠️ {issue}")
        for suggestion in wisdom.get('improvement_suggestions', [])[:3]:
            smart_print(f"  💡 {suggestion}")
    
    # 컨텍스트 정보
    if result.get('context'):
        smart_print("\\n### 📝 파일 컨텍스트")
        smart_print(result['context'][:500] + "..." if len(result['context']) > 500 else result['context'])
else:
    smart_print(f"❌ 파일 분석 실패: {result.get('error', 'Unknown error')}")

${generateSaveVars()}
`;
    
    return ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
}
