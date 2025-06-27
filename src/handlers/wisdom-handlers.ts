/**
 * Wisdom System Handlers
 */

import { logger } from '../utils/logger';
import { JSONRPCExecutor } from '../json-rpc-executor';

const jsonRPCExecutor = new JSONRPCExecutor();

/**
 * Wisdom analyze handler - 코드 분석
 */
export async function handleWisdomAnalyze(args: {
  code: string;
  filename?: string;
  auto_fix?: boolean;
}): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const { code, filename = 'temp.py', auto_fix = false } = args;
    
    const pythonCode = `
from core.wisdom_integration import wisdom_integration

# 코드 분석
code = """${code.replace(/"""/g, '\"\"\""')}"""
filename = "${filename}"
auto_fix = ${auto_fix ? 'True' : 'False'}

# 분석 실행
should_proceed, modified_code, analysis_result = wisdom_integration.pre_execute_check(
    code, 
    language="${filename.endsWith('.py') ? 'python' : filename.endsWith('.ts') ? 'typescript' : 'javascript'}"
)

# 결과 생성
result = {
    "should_proceed": should_proceed,
    "modified_code": modified_code if modified_code != code else None,
    "analysis": analysis_result,
    "detections_count": analysis_result.get("total_issues", 0)
}

import json
print(json.dumps(result, indent=2, ensure_ascii=False))
`;

    const executeResult = await jsonRPCExecutor.execute({
      code: pythonCode,
      language: 'python'
    });

    if (!executeResult.success) {
      throw new Error(executeResult.stderr || 'Analysis failed');
    }

    // 결과 파싱
    const result = JSON.parse(executeResult.stdout);
    
    return {
      content: [
        { type: 'text', text: `🧠 Wisdom Analysis Complete\n\n` },
        { type: 'text', text: `📊 Total Issues: ${result.detections_count}\n` },
        { type: 'text', text: `Status: ${result.analysis.status}\n\n` },
        { type: 'text', text: JSON.stringify(result.analysis, null, 2) }
      ]
    };
  } catch (error) {
    logger.error('Wisdom analyze error:', error);
    return {
      content: [
        { type: 'text', text: `❌ Analysis failed: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}

/**
 * Wisdom analyze file handler - 파일 분석
 */
export async function handleWisdomAnalyzeFile(args: {
  filepath: string;
}): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const { filepath } = args;
    
    const pythonCode = `
from core.wisdom_integration import wisdom_integration

# 파일 분석
result = wisdom_integration.analyze_file("${filepath}")

import json
print(json.dumps(result, indent=2, ensure_ascii=False))
`;

    const executeResult = await jsonRPCExecutor.execute({
      code: pythonCode,
      language: 'python'
    });

    if (!executeResult.success) {
      throw new Error(executeResult.stderr || 'File analysis failed');
    }

    const result = JSON.parse(executeResult.stdout);
    
    return {
      content: [
        { type: 'text', text: `🧠 File Analysis: ${filepath}\n\n` },
        { type: 'text', text: JSON.stringify(result, null, 2) }
      ]
    };
  } catch (error) {
    logger.error('Wisdom analyze file error:', error);
    return {
      content: [
        { type: 'text', text: `❌ File analysis failed: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}

/**
 * Wisdom report handler - 리포트 생성
 */
export async function handleWisdomReport(args: {
  output_file?: string;
}): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const { output_file } = args;
    
    const pythonCode = `
from core.wisdom_integration import wisdom_integration

# 리포트 생성
report = wisdom_integration.generate_wisdom_report(${output_file ? `"${output_file}"` : 'None'})
print(report)
`;

    const executeResult = await jsonRPCExecutor.execute({
      code: pythonCode,
      language: 'python'
    });

    if (!executeResult.success) {
      throw new Error(executeResult.stderr || 'Report generation failed');
    }

    return {
      content: [
        { type: 'text', text: executeResult.stdout }
      ]
    };
  } catch (error) {
    logger.error('Wisdom report error:', error);
    return {
      content: [
        { type: 'text', text: `❌ Report generation failed: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}
