/**
 * Project Context Handlers
 */

import { logger } from '../utils/logger';
import { JSONRPCExecutor } from '../json-rpc-executor';

const jsonRPCExecutor = new JSONRPCExecutor();

/**
 * Build project context handler
 */
export async function handleBuildProjectContext(args: {
  update_readme?: boolean;
  update_context?: boolean;
  include_stats?: boolean;
  include_file_directory?: boolean;
}): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const {
      update_readme = true,
      update_context = true,
      include_stats = true,
      include_file_directory = false
    } = args;
    
    const pythonCode = `
# 프로젝트 컨텍스트 문서 생성
from project_analyzer import ProjectAnalyzer
import os

analyzer = ProjectAnalyzer()
project_name = os.path.basename(os.getcwd())

results = []

# README.md 업데이트
if ${update_readme ? 'True' : 'False'}:
    readme_path = analyzer.update_readme(project_name)
    if readme_path:
        results.append(f"✅ README.md 업데이트 완료: {readme_path}")
    else:
        results.append("❌ README.md 업데이트 실패")

# PROJECT_CONTEXT.md 업데이트
if ${update_context ? 'True' : 'False'}:
    context_path = analyzer.update_project_context(
        project_name,
        include_stats=${include_stats ? 'True' : 'False'}
    )
    if context_path:
        results.append(f"✅ PROJECT_CONTEXT.md 업데이트 완료: {context_path}")
    else:
        results.append("❌ PROJECT_CONTEXT.md 업데이트 실패")

# file_directory.md 생성
if ${include_file_directory ? 'True' : 'False'}:
    directory_path = analyzer.create_file_directory(project_name)
    if directory_path:
        results.append(f"✅ file_directory.md 생성 완료: {directory_path}")
    else:
        results.append("❌ file_directory.md 생성 실패")

for result in results:
    print(result)
`;

    const executeResult = await jsonRPCExecutor.execute({
      code: pythonCode,
      language: 'python'
    });

    if (!executeResult.success) {
      throw new Error(executeResult.stderr || 'Build context failed');
    }

    return {
      content: [
        { type: 'text', text: '📋 Project Context Build Complete\n\n' },
        { type: 'text', text: executeResult.stdout }
      ]
    };
  } catch (error) {
    logger.error('Build project context error:', error);
    return {
      content: [
        { type: 'text', text: `❌ Build failed: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}
