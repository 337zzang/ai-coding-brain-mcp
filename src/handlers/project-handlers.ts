/**
 * Project Context Handlers
 */

import { logger } from '../utils/logger';
import { execFile } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execFileAsync = promisify(execFile);

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
    
    const pythonPath = getPythonPath();
    const projectRoot = getProjectRoot();
    
    // Python 스크립트 내용
    const scriptContent = `
import sys
import os
sys.path.insert(0, r'${projectRoot.replace(/\\/g, '\\\\')}\\python')
os.chdir(r'${projectRoot.replace(/\\/g, '\\\\')}')

# 프로젝트 컨텍스트 문서 생성
from project_analyzer import ProjectAnalyzer

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

# 결과 출력
for result in results:
    print(result)

if not results:
    print("⚠️ 처리할 작업이 없습니다.")
`;

    const { stdout, stderr } = await execFileAsync(pythonPath, ['-c', scriptContent], {
      env: getPythonEnv(),
      cwd: projectRoot,
      windowsHide: true
    });
    
    if (stderr) {
      logger.warn(`Python stderr: ${stderr}`);
    }
    
    return {
      content: [{
        type: 'text',
        text: stdout.trim() || '✅ 프로젝트 컨텍스트 빌드 완료'
      }]
    };
  } catch (error: any) {
    logger.error('Build project context failed:', error);
    return {
      content: [{
        type: 'text',
        text: `❌ Build failed: ${error.message}`
      }]
    };
  }
}
