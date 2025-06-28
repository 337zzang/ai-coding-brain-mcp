"use strict";
/**
 * Gitignore 관련 핸들러
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
exports.handleGitignoreAnalyze = handleGitignoreAnalyze;
exports.handleGitignoreUpdate = handleGitignoreUpdate;
exports.handleGitignoreCreate = handleGitignoreCreate;
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
/**
 * 프로젝트 분석하여 .gitignore 제안
 */
async function handleGitignoreAnalyze() {
    try {
        const projectRoot = process.cwd();
        const scriptPath = path.join(projectRoot, 'python', 'gitignore_manager.py');
        if (!fs.existsSync(scriptPath)) {
            throw new Error('gitignore_manager.py를 찾을 수 없습니다.');
        }
        const pythonCode = `
import json
from gitignore_manager import get_gitignore_manager

manager = get_gitignore_manager()
suggestions = manager.analyze_project()

# 결과 포맷팅
result = {
    "found": bool(suggestions),
    "categories": {}
}

for category, patterns in suggestions.items():
    result["categories"][category] = patterns

print(json.dumps(result, ensure_ascii=False))
`;
        const output = (0, child_process_1.execSync)(`python -c "${pythonCode.replace(/"/g, '\\"')}"`, {
            encoding: 'utf8',
            cwd: projectRoot
        });
        const result = JSON.parse(output.trim());
        if (!result.found) {
            return {
                content: [{
                        type: 'text',
                        text: '프로젝트에서 .gitignore에 추가할 만한 파일/폴더를 찾지 못했습니다.'
                    }]
            };
        }
        let text = '🔍 프로젝트 분석 결과\n\n';
        text += '.gitignore에 추가하면 좋을 패턴들:\n\n';
        for (const [category, patterns] of Object.entries(result.categories)) {
            text += `**${category}**\n`;
            for (const pattern of patterns) {
                text += `- ${pattern}\n`;
            }
            text += '\n';
        }
        return {
            content: [{
                    type: 'text',
                    text: text
                }]
        };
    }
    catch (error) {
        return {
            content: [{
                    type: 'text',
                    text: `오류 발생: ${error.message}`
                }]
        };
    }
}
/**
 * .gitignore 파일 업데이트
 */
async function handleGitignoreUpdate(args) {
    try {
        const projectRoot = process.cwd();
        const patterns = JSON.stringify(args.patterns);
        const category = args.category ? `"${args.category}"` : 'None';
        const pythonCode = `
import json
from gitignore_manager import get_gitignore_manager

manager = get_gitignore_manager()
result = manager.update_gitignore(${patterns}, ${category})

print(json.dumps(result, ensure_ascii=False))
`;
        const output = (0, child_process_1.execSync)(`python -c "${pythonCode.replace(/"/g, '\\"')}"`, {
            encoding: 'utf8',
            cwd: projectRoot
        });
        const result = JSON.parse(output.trim());
        let text = result.message + '\n\n';
        if (result.added && result.added.length > 0) {
            text += '✅ 추가된 패턴:\n';
            for (const pattern of result.added) {
                text += `- ${pattern}\n`;
            }
        }
        if (result.existing && result.existing.length > 0) {
            text += '\n⚠️ 이미 존재하는 패턴:\n';
            for (const pattern of result.existing) {
                text += `- ${pattern}\n`;
            }
        }
        return {
            content: [{
                    type: 'text',
                    text: text
                }]
        };
    }
    catch (error) {
        return {
            content: [{
                    type: 'text',
                    text: `오류 발생: ${error.message}`
                }]
        };
    }
}
/**
 * 새로운 .gitignore 파일 생성
 */
async function handleGitignoreCreate(args) {
    try {
        const projectRoot = process.cwd();
        const categories = args.categories ? JSON.stringify(args.categories) : 'None';
        const pythonCode = `
import json
from gitignore_manager import get_gitignore_manager

manager = get_gitignore_manager()
result = manager.create_gitignore(${categories})

print(json.dumps(result, ensure_ascii=False))
`;
        const output = (0, child_process_1.execSync)(`python -c "${pythonCode.replace(/"/g, '\\"')}"`, {
            encoding: 'utf8',
            cwd: projectRoot
        });
        const result = JSON.parse(output.trim());
        if (!result.success) {
            return {
                content: [{
                        type: 'text',
                        text: result.message
                    }]
            };
        }
        let text = result.message + '\n\n';
        text += '📝 포함된 카테고리:\n';
        for (const category of result.categories) {
            text += `- ${category}\n`;
        }
        return {
            content: [{
                    type: 'text',
                    text: text
                }]
        };
    }
    catch (error) {
        return {
            content: [{
                    type: 'text',
                    text: `오류 발생: ${error.message}`
                }]
        };
    }
}
//# sourceMappingURL=gitignore-handlers.js.map