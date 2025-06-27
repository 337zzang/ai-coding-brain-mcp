// API 토글 핸들러
import { createLogger } from '../utils/logger';
import * as path from 'path';
import * as fs from 'fs';
import { execFile } from 'child_process';
import { promisify } from 'util';

const logger = createLogger('api-toggle-handler');
const execFileAsync = promisify(execFile);

// ToolHandler 타입 정의
interface ToolHandler {
  name: string;
  execute: (args: any) => Promise<any>;
}

/**
 * Get Python path from config
 */
/**
 * Get project root directory
 */
function getProjectRoot(): string {
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

function getPythonPath(): string {
    const configPath = path.join(getProjectRoot(), '.ai-brain.config.json');
    
    if (fs.existsSync(configPath)) {
        try {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            return config.python?.path || 'python';
        } catch (e) {
            logger.warn('Failed to read config, using default python path');
        }
    }
    
    return 'python';
}

/**
 * Get Python environment
 */
function getPythonEnv(): NodeJS.ProcessEnv {
    const projectRoot = getProjectRoot();
    return {
        ...process.env,
        PYTHONPATH: path.join(projectRoot, 'python'),
        PYTHONIOENCODING: 'utf-8',
        PYTHONDONTWRITEBYTECODE: '1',
        PYTHONUNBUFFERED: '1'
    };
}

async function executePythonCode(code: string): Promise<any> {
    try {
        const pythonPath = getPythonPath();
        const projectRoot = getProjectRoot();
        
        // Add proper path setup
        const fullCode = `
import os
import sys
sys.path.insert(0, r'${projectRoot.replace(/\\/g, '\\\\')}\\python')
os.chdir(r'${projectRoot.replace(/\\/g, '\\\\')}')

# Initialize REPL environment
from json_repl_session import initialize_repl, repl_globals
initialize_repl()

${code}
`;
        
        const { stdout, stderr } = await execFileAsync(pythonPath, ['-c', fullCode], {
            env: getPythonEnv(),
            cwd: projectRoot,
            windowsHide: true
        });
        
        if (stderr) {
            logger.warn(`Python stderr: ${stderr}`);
        }
        
        try {
            return JSON.parse(stdout.trim());
        } catch (e) {
            return { success: true, output: stdout };
        }
    } catch (error: any) {
        logger.error('Python execution error:', error);
        throw new Error(`Python execution failed: ${error.message}`);
    }
}

export const apiToggleHandler: ToolHandler = {
  name: 'toggle_api',
  
  async execute(args: any) {
    const { api_name, enabled = true } = args;
    
    if (!api_name) {
      throw new Error('API 이름을 지정해주세요');
    }
    
    const code = `
import json
from api_manager import api_manager
result = api_manager.toggle_api("${api_name}", ${enabled})
print(json.dumps(result, ensure_ascii=False))
`;
    
    try {
      return await executePythonCode(code);
    } catch (error) {
      logger.error('API 토글 오류: ' + error);
      throw error;
    }
  }
};

export const listApisHandler: ToolHandler = {
  name: 'list_apis',
  
  async execute() {
    const code = `
import json
from api_manager import api_manager
apis = api_manager.list_apis()

# 결과 포맷팅
if apis:
    available = apis.get('available', [])
    enabled = apis.get('enabled', [])
    
    message = "🔌 **API 목록**\\n\\n"
    
    if available:
        message += f"**사용 가능한 API ({len(available)}개):**\\n"
        for api in available:
            status = "✅" if api in enabled else "❌"
            message += f"  • {api} {status}\\n"
    else:
        message += "사용 가능한 API가 없습니다.\\n"
    
    result = {
        "content": [{
            "type": "text",
            "text": message
        }]
    }
else:
    result = {
        "content": [{
            "type": "text",
            "text": "API 목록을 가져올 수 없습니다."
        }]
    }

print(json.dumps(result, ensure_ascii=False))
`;
    
    try {
      const result = await executePythonCode(code);
      // executePythonCode가 이미 JSON 파싱을 하므로, result를 그대로 반환
      if (result.content) {
        return result;
      } else {
        // 파싱 실패 시 기본 응답
        return {
          content: [{
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }]
        };
      }
    } catch (error) {
      logger.error('API 목록 조회 오류: ' + error);
      throw error;
    }
  }
};
