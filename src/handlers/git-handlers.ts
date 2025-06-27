/**
 * Git Handlers - AI Coding Brain MCP
 * Git 관련 MCP 도구 핸들러
 */

import { createLogger } from '../services/logger';

const logger = createLogger('git-handlers');

/**
 * Git 상태 확인
 */
export async function handleGitStatus(_args: any): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { spawn } = require('child_process');
        const path = require('path');
        const fs = require('fs');
        
        // 프로젝트 루트 찾기
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
        
        // Python 스크립트 경로 설정
        const scriptPath = path.join(projectRoot, 'python', 'mcp_git_wrapper.py');
        
        if (!fs.existsSync(scriptPath)) {
            throw new Error(`Python script not found at ${scriptPath}`);
        }
        
        // 설정 파일에서 Python 경로 읽기
        const configPath = path.join(projectRoot, '.ai-brain.config.json');
        let pythonPath = 'python';
        
        if (fs.existsSync(configPath)) {
            try {
                const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                pythonPath = config.python?.path || 'python';
            } catch (e) {
                logger.warn('Failed to read config, using default python path');
            }
        }
        
        return new Promise((resolve, reject) => {
            const pythonProcess = spawn(pythonPath, [scriptPath, 'status'], {
                cwd: projectRoot,  // 프로젝트 루트를 작업 디렉토리로 설정
                env: { ...process.env },
                windowsHide: true
            });
            
            let output = '';
            let errorOutput = '';
            
            pythonProcess.stdout.on('data', (data: Buffer) => {
                output += data.toString('utf8');
            });
            
            pythonProcess.stderr.on('data', (data: Buffer) => {
                errorOutput += data.toString('utf8');
            });
            
            pythonProcess.on('close', (code: number | null) => {
                if (code !== 0) {
                    reject(new Error(`Process exited with code ${code}: ${errorOutput}`));
                    return;
                }
                
                try {
                    const gitResult = JSON.parse(output.trim());
                    
                    if (gitResult.success) {
                        resolve({
                            content: [{
                                type: 'text',
                                text: gitResult.message
                            }]
                        });
                    } else {
                        resolve({
                            content: [{
                                type: 'text',
                                text: `Git 상태 확인 실패: ${gitResult.message}`
                            }]
                        });
                    }
                } catch (parseError) {
                    reject(new Error(`Failed to parse output: ${output}`));
                }
            });
            
            pythonProcess.on('error', (error: Error) => {
                reject(error);
            });
        });
    } catch (error) {
        logger.error('Git status failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 상태 확인 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 스마트 커밋
 */
export async function handleGitCommitSmart(args: { message?: string; auto_add?: boolean }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { spawn } = require('child_process');
        const path = require('path');
        const fs = require('fs');
        
        // 프로젝트 루트 찾기
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
        
        // Python 스크립트 경로 설정
        const scriptPath = path.join(projectRoot, 'python', 'mcp_git_wrapper.py');
        
        if (!fs.existsSync(scriptPath)) {
            throw new Error(`Python script not found at ${scriptPath}`);
        }
        
        // 설정 파일에서 Python 경로 읽기
        const configPath = path.join(projectRoot, '.ai-brain.config.json');
        let pythonPath = 'python';
        
        if (fs.existsSync(configPath)) {
            try {
                const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                pythonPath = config.python?.path || 'python';
            } catch (e) {
                logger.warn('Failed to read config, using default python path');
            }
        }
        
        // 인자 준비
        const cmdArgs = ['commit'];
        if (args.message) {
            cmdArgs.push(args.message);
        } else {
            cmdArgs.push('');  // 빈 메시지
        }
        cmdArgs.push(args.auto_add !== false ? 'true' : 'false');
        
        return new Promise((resolve, reject) => {
            const pythonProcess = spawn(pythonPath, [scriptPath, ...cmdArgs], {
                cwd: projectRoot,  // 프로젝트 루트를 작업 디렉토리로 설정
                env: { ...process.env },
                windowsHide: true
            });
            
            let output = '';
            let errorOutput = '';
            
            pythonProcess.stdout.on('data', (data: Buffer) => {
                output += data.toString('utf8');
            });
            
            pythonProcess.stderr.on('data', (data: Buffer) => {
                errorOutput += data.toString('utf8');
            });
            
            pythonProcess.on('close', (code: number | null) => {
                if (code !== 0) {
                    reject(new Error(`Process exited with code ${code}: ${errorOutput}`));
                    return;
                }
                
                try {
                    const commitResult = JSON.parse(output.trim());
                    
                    resolve({
                        content: [{
                            type: 'text',
                            text: commitResult.message || 'Git 커밋 완료'
                        }]
                    });
                } catch (parseError) {
                    reject(new Error(`Failed to parse output: ${output}`));
                }
            });
            
            pythonProcess.on('error', (error: Error) => {
                reject(error);
            });
        });
    } catch (error) {
        logger.error('Git commit failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 커밋 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 스마트 브랜치
 */
export async function handleGitBranchSmart(args: { branch_name?: string; base_branch?: string }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { spawn } = require('child_process');
        const path = require('path');
        const fs = require('fs');
        
        // 프로젝트 루트 찾기 (handleGitStatus와 동일한 로직)
        let projectRoot = process.cwd();
        
        if (!projectRoot.includes('ai-coding-brain-mcp')) {
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
        
        // Python 스크립트 경로
        const scriptPath = path.join(projectRoot, 'python', 'mcp_git_wrapper.py');
        
        if (!fs.existsSync(scriptPath)) {
            throw new Error(`Python script not found at ${scriptPath}`);
        }
        
        // 설정 파일에서 Python 경로 읽기
        const configPath = path.join(projectRoot, '.ai-brain.config.json');
        let pythonPath = 'python';
        
        if (fs.existsSync(configPath)) {
            try {
                const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                pythonPath = config.python?.path || 'python';
            } catch (e) {
                logger.warn('Failed to read config, using default python path');
            }
        }
        
        // 인자 준비
        const pythonArgs = [scriptPath, 'branch-smart'];
        if (args.branch_name) {
            pythonArgs.push(args.branch_name);
        }
        if (args.base_branch) {
            pythonArgs.push('--base', args.base_branch);
        }
        
        return new Promise((resolve, reject) => {
            const pythonProcess = spawn(pythonPath, pythonArgs, {
                cwd: projectRoot,
                env: { ...process.env },
                windowsHide: true
            });
            
            let output = '';
            let errorOutput = '';
            
            pythonProcess.stdout.on('data', (data: Buffer) => {
                output += data.toString();
            });
            
            pythonProcess.stderr.on('data', (data: Buffer) => {
                errorOutput += data.toString();
            });
            
            pythonProcess.on('close', (code: number) => {
                if (code !== 0) {
                    reject(new Error(`Process exited with code ${code}: ${errorOutput}`));
                    return;
                }
                
                try {
                    const result = JSON.parse(output.trim());
                    resolve({
                        content: [{
                            type: 'text',
                            text: result.message || 'Git 브랜치 생성 완료'
                        }]
                    });
                } catch (parseError) {
                    // JSON 파싱 실패 시 출력 그대로 반환
                    resolve({
                        content: [{
                            type: 'text',
                            text: output.trim() || 'Git 브랜치 생성 완료'
                        }]
                    });
                }
            });
            
            pythonProcess.on('error', (error: Error) => {
                reject(error);
            });
        });
    } catch (error) {
        logger.error('Git branch failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 브랜치 생성 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 스마트 롤백
 */
export async function handleGitRollbackSmart(args: { target?: string; safe_mode?: boolean }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const target = args.target ? `"${args.target}"` : 'None';
        const safeMode = args.safe_mode !== false;
        
        const pythonCode = `
from mcp_git_tools import git_rollback_smart
result = git_rollback_smart(${target}, ${safeMode})
print(json.dumps(result, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "import json; ${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true  // Windows 호환성을 위해 추가
            }
        );
        
        const rollbackResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: rollbackResult.message || 'Git 롤백 완료'
            }]
        };
    } catch (error) {
        logger.error('Git rollback failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 롤백 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 푸시
 */
export async function handleGitPush(args: { remote?: string; branch?: string }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const remote = args.remote || 'origin';
        const branch = args.branch ? `"${args.branch}"` : 'None';
        
        const pythonCode = `
from mcp_git_tools import git_push
result = git_push("${remote}", ${branch})
print(json.dumps(result, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "import json; ${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true  // Windows 호환성을 위해 추가
            }
        );
        
        const pushResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: pushResult.message || 'Git 푸시 완료'
            }]
        };
    } catch (error) {
        logger.error('Git push failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 푸시 실패: ${error}`
            }]
        };
    }
}
