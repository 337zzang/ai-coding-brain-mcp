"use strict";
/**
 * Wisdom System Handlers
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleWisdomStats = handleWisdomStats;
exports.handleTrackMistake = handleTrackMistake;
exports.handleAddBestPractice = handleAddBestPractice;
exports.handleWisdomAnalyze = handleWisdomAnalyze;
exports.handleWisdomAnalyzeFile = handleWisdomAnalyzeFile;
exports.handleWisdomReport = handleWisdomReport;
const logger_1 = require("../utils/logger");
const child_process_1 = require("child_process");
const util_1 = require("util");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const execFileAsync = (0, util_1.promisify)(child_process_1.execFile);
/**
 * Get Python path from config
 */
function getPythonPath() {
    const projectRoot = getProjectRoot();
    const configPath = path.join(projectRoot, '.ai-brain.config.json');
    if (fs.existsSync(configPath)) {
        try {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            return config.python?.path || 'python';
        }
        catch (e) {
            logger_1.logger.warn('Failed to read config, using default python path');
        }
    }
    // Fallback to system python
    return 'python';
}
/**
 * Get project root directory
 */
function getProjectRoot() {
    let projectRoot = process.cwd();
    // ai-coding-brain-mcp 프로젝트 디렉토리 찾기
    if (!projectRoot.includes('ai-coding-brain-mcp')) {
        // 알려진 위치에서 찾기
        const possiblePaths = [
            'C:\\Users\\Administrator\\Desktop\\ai-coding-brain-mcp',
            path.join(process.env['USERPROFILE'] || '', 'Desktop', 'ai-coding-brain-mcp'),
            path.join(process.env['USERPROFILE'] || '', 'Documents', 'ai-coding-brain-mcp')
        ];
        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(path.join(possiblePath, '.ai-brain.config.json'))) {
                projectRoot = possiblePath;
                break;
            }
        }
    }
    return projectRoot;
}
/**
 * Get Python environment
 */
function getPythonEnv() {
    const projectRoot = getProjectRoot();
    return {
        ...process.env,
        PYTHONPATH: path.join(projectRoot, 'python'),
        PYTHONIOENCODING: 'utf-8',
        PYTHONDONTWRITEBYTECODE: '1',
        PYTHONUNBUFFERED: '1'
    };
}
/**
 * Execute Python code helper
 */
async function executePythonCode(code) {
    try {
        const pythonPath = getPythonPath();
        const projectRoot = getProjectRoot();
        // Add proper path setup to the code
        const fullCode = `
import sys
import os
sys.path.insert(0, r'${projectRoot.replace(/\\/g, '\\\\')}\\python')
os.chdir(r'${projectRoot.replace(/\\/g, '\\\\')}')

${code}
`;
        const { stdout, stderr } = await execFileAsync(pythonPath, ['-c', fullCode], {
            env: getPythonEnv(),
            cwd: projectRoot,
            windowsHide: true
        });
        if (stderr) {
            logger_1.logger.warn(`Python stderr: ${stderr}`);
        }
        return stdout;
    }
    catch (error) {
        logger_1.logger.error('Python execution error:', error);
        throw new Error(`Python execution failed: ${error.message}`);
    }
}
/**
 * Wisdom stats handler - 통계 정보
 */
async function handleWisdomStats() {
    try {
        const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
stats = wisdom.get_statistics()

import json
print(json.dumps(stats, indent=2, ensure_ascii=False))
`;
        const result = await executePythonCode(pythonCode);
        const stats = JSON.parse(result);
        let message = `🧠 **Wisdom 시스템 통계**\n\n`;
        message += `📊 **전체 현황**\n`;
        message += `• 총 실수: ${stats.total_mistakes || 0}\n`;
        message += `• 총 오류: ${stats.total_errors || 0}\n`;
        message += `• 베스트 프랙티스: ${stats.total_best_practices || 0}\n\n`;
        if (stats.mistake_types && Object.keys(stats.mistake_types).length > 0) {
            message += `❌ **자주 하는 실수**\n`;
            const sortedMistakes = Object.entries(stats.mistake_types)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5);
            for (const [type, count] of sortedMistakes) {
                message += `• ${type}: ${count}회\n`;
            }
        }
        return {
            content: [{
                    type: 'text',
                    text: message
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Failed to get wisdom stats:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ Failed to get statistics: ${error}`
                }]
        };
    }
}
/**
 * Track mistake handler
 */
async function handleTrackMistake(args) {
    try {
        const { mistake_type, context = '' } = args;
        const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.track_mistake('${mistake_type}', '${context.replace(/'/g, "\\'")}')
print("Success")
`;
        await executePythonCode(pythonCode);
        return {
            content: [{
                    type: 'text',
                    text: `✅ 실수가 기록되었습니다: ${mistake_type}`
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Failed to track mistake:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ Failed to track mistake: ${error}`
                }]
        };
    }
}
/**
 * Add best practice handler
 */
async function handleAddBestPractice(args) {
    try {
        const { practice, category = 'general' } = args;
        const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.add_best_practice('${practice.replace(/'/g, "\\'")}', '${category}')
print("Success")
`;
        await executePythonCode(pythonCode);
        return {
            content: [{
                    type: 'text',
                    text: `✅ 베스트 프랙티스가 추가되었습니다: ${practice}`
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Failed to add best practice:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ Failed to add best practice: ${error}`
                }]
        };
    }
}
/**
 * Wisdom analyze handler - 코드 분석
 */
async function handleWisdomAnalyze(args) {
    try {
        const { code, filename = 'temp.py' } = args;
        // Escape the code properly
        const escapedCode = code.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
        const pythonCode = `
from wisdom_hooks import get_wisdom_hooks
hooks = get_wisdom_hooks()

code = '''${escapedCode}'''
filename = '${filename}'

detected = hooks.check_code_patterns(code, filename)

import json
print(json.dumps({
    'detected': detected,
    'count': len(detected)
}, ensure_ascii=False))
`;
        const result = await executePythonCode(pythonCode);
        const analysis = JSON.parse(result);
        if (analysis.count === 0) {
            return {
                content: [{
                        type: 'text',
                        text: '✅ 코드 분석 완료: 문제점이 발견되지 않았습니다.'
                    }]
            };
        }
        let message = `🔍 **코드 분석 결과**\n\n`;
        message += `발견된 문제: ${analysis.count}개\n\n`;
        for (const detection of analysis.detected) {
            message += `⚠️ **${detection.pattern}**\n`;
            message += `• 위치: ${detection.location || '알 수 없음'}\n`;
            message += `• 설명: ${detection.message || ''}\n\n`;
        }
        return {
            content: [{
                    type: 'text',
                    text: message
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Failed to analyze code:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ Analysis failed: ${error}`
                }]
        };
    }
}
/**
 * Wisdom analyze file handler
 */
async function handleWisdomAnalyzeFile(args) {
    try {
        const { filepath } = args;
        const pythonCode = `
import os
from wisdom_hooks import get_wisdom_hooks

filepath = r'${filepath.replace(/\\/g, '\\\\')}'

if not os.path.exists(filepath):
    print(json.dumps({'error': 'File not found'}, ensure_ascii=False))
else:
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    
    hooks = get_wisdom_hooks()
    detected = hooks.check_code_patterns(code, filepath)
    
    import json
    print(json.dumps({
        'detected': detected,
        'count': len(detected),
        'filepath': filepath
    }, ensure_ascii=False))
`;
        const result = await executePythonCode(pythonCode);
        const analysis = JSON.parse(result);
        if (analysis.error) {
            return {
                content: [{
                        type: 'text',
                        text: `❌ 파일을 찾을 수 없습니다: ${filepath}`
                    }]
            };
        }
        if (analysis.count === 0) {
            return {
                content: [{
                        type: 'text',
                        text: `✅ 파일 분석 완료: ${filepath}\n문제점이 발견되지 않았습니다.`
                    }]
            };
        }
        let message = `🔍 **파일 분석 결과: ${filepath}**\n\n`;
        message += `발견된 문제: ${analysis.count}개\n\n`;
        for (const detection of analysis.detected) {
            message += `⚠️ **${detection.pattern}**\n`;
            message += `• 위치: ${detection.location || '알 수 없음'}\n`;
            message += `• 설명: ${detection.message || ''}\n\n`;
        }
        return {
            content: [{
                    type: 'text',
                    text: message
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Failed to analyze file:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ File analysis failed: ${error}`
                }]
        };
    }
}
/**
 * Wisdom report handler
 */
async function handleWisdomReport(args) {
    try {
        const { output_file } = args;
        const pythonCode = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()

# Generate report
report = wisdom.generate_report()

# Save if output file specified
output_file = ${output_file ? `'${output_file}'` : 'None'}
if output_file:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to: {output_file}")
else:
    print(report)
`;
        const result = await executePythonCode(pythonCode);
        return {
            content: [{
                    type: 'text',
                    text: result.trim()
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Failed to generate report:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ Report generation failed: ${error}`
                }]
        };
    }
}
//# sourceMappingURL=wisdom-handlers.js.map