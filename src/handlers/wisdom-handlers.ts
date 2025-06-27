/**
 * Wisdom System Handlers
 */

import { logger } from '../utils/logger';
import { execFile } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import { getPythonPath, getPythonEnv } from '../utils/python-path';

const execFileAsync = promisify(execFile);

/**
 * Execute Python code helper
 */
async function executePythonCode(code: string): Promise<string> {
  try {
    const pythonPath = getPythonPath();
    const { stdout, stderr } = await execFileAsync(pythonPath, ['-c', code], {
      env: getPythonEnv(),
      cwd: path.join(process.cwd(), 'python')
    });
    
    if (stderr) {
      logger.warn(`Python stderr: ${stderr}`);
    }
    
    return stdout;
  } catch (error: any) {
    throw new Error(`Python execution failed: ${error.message}`);
  }
}

/**
 * Wisdom stats handler - 통계 정보
 */
export async function handleWisdomStats(): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
stats = wisdom.get_statistics()

import json
print(json.dumps(stats, indent=2, ensure_ascii=False))
`;

    const result = await executePythonCode(pythonCode);
    const stats = JSON.parse(result) as any;
    
    return {
      content: [
        { type: 'text', text: `🧠 Wisdom System Statistics\n\n` },
        { type: 'text', text: JSON.stringify(stats, null, 2) }
      ]
    };
  } catch (error) {
    logger.error('Wisdom stats error:', error);
    return {
      content: [
        { type: 'text', text: `❌ Failed to get statistics: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}

/**
 * Track mistake handler - 실수 추적
 */
export async function handleTrackMistake(args: {
  mistake_type: string;
  context?: string;
}): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const { mistake_type, context = '' } = args;
    
    const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.track_mistake("${mistake_type}", "${context}")
print(f"✅ Mistake tracked: {mistake_type}")
`;

    const result = await executePythonCode(pythonCode);
    
    return {
      content: [
        { type: 'text', text: result.trim() }
      ]
    };
  } catch (error) {
    logger.error('Track mistake error:', error);
    return {
      content: [
        { type: 'text', text: `❌ Failed to track mistake: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}

/**
 * Add best practice handler - 베스트 프랙티스 추가
 */
export async function handleAddBestPractice(args: {
  practice: string;
  category?: string;
}): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const { practice, category = 'general' } = args;
    
    const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.add_best_practice("${practice}", "${category}")
print(f"✅ Best practice added: {practice}")
`;

    const result = await executePythonCode(pythonCode);
    
    return {
      content: [
        { type: 'text', text: result.trim() }
      ]
    };
  } catch (error) {
    logger.error('Add best practice error:', error);
    return {
      content: [
        { type: 'text', text: `❌ Failed to add best practice: ${error instanceof Error ? error.message : String(error)}` }
      ]
    };
  }
}

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
code = """${code.replace(/"""/g, '\\"\\"\\"')}"""
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

    const result = await executePythonCode(pythonCode);
    const analysisResult = JSON.parse(result) as any;
    
    return {
      content: [
        { type: 'text', text: `🧠 Wisdom Analysis Complete\n\n` },
        { type: 'text', text: `📊 Total Issues: ${analysisResult.detections_count}\n` },
        { type: 'text', text: `Status: ${analysisResult.analysis.status}\n\n` },
        { type: 'text', text: JSON.stringify(analysisResult.analysis, null, 2) }
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

    const result = await executePythonCode(pythonCode);
    const analysisResult = JSON.parse(result) as any;
    
    return {
      content: [
        { type: 'text', text: `🧠 File Analysis: ${filepath}\n\n` },
        { type: 'text', text: JSON.stringify(analysisResult, null, 2) }
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

    const result = await executePythonCode(pythonCode);
    
    return {
      content: [
        { type: 'text', text: `🧠 Wisdom Report Generated\n\n` },
        { type: 'text', text: result }
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