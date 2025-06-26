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
        const { execSync } = require('child_process');
        const pythonCode = `
from mcp_git_tools import git_status
result = git_status()
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
        
        const gitResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: gitResult.message || 'Git 상태 확인 완료'
            }]
        };
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
        const { execSync } = require('child_process');
        const message = args.message ? `"${args.message}"` : 'None';
        const autoAdd = args.auto_add !== false;
        
        const pythonCode = `
from mcp_git_tools import git_commit_smart
result = git_commit_smart(${message}, ${autoAdd})
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
        
        const commitResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: commitResult.message || 'Git 커밋 완료'
            }]
        };
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
        const { execSync } = require('child_process');
        const branchName = args.branch_name ? `"${args.branch_name}"` : 'None';
        const baseBranch = args.base_branch || 'main';
        
        const pythonCode = `
from mcp_git_tools import git_branch_smart
result = git_branch_smart(${branchName}, "${baseBranch}")
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
        
        const branchResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: branchResult.message || 'Git 브랜치 생성 완료'
            }]
        };
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
