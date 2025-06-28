"use strict";
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
exports.getPythonPath = getPythonPath;
exports.validatePythonPath = validatePythonPath;
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const child_process_1 = require("child_process");
function getPythonPath() {
    // 1. 환경변수에서 PYTHON_PATH 확인
    if (process.env['PYTHON_PATH'] && fs.existsSync(process.env['PYTHON_PATH'])) {
        console.log(`Using PYTHON_PATH from environment: ${process.env['PYTHON_PATH']}`);
        return process.env['PYTHON_PATH'];
    }
    // 2. 시스템 PATH에서 python 찾기
    const pythonCommands = process.platform === 'win32'
        ? ['python.exe', 'python3.exe', 'py.exe']
        : ['python3', 'python'];
    for (const cmd of pythonCommands) {
        try {
            const result = (0, child_process_1.spawnSync)(cmd, ['--version'], { encoding: 'utf8' });
            if (result.status === 0) {
                console.log(`Found Python in PATH: ${cmd}`);
                return cmd;
            }
        }
        catch (e) {
            // Continue to next option
        }
    }
    // 3. 일반적인 Python 설치 경로 확인
    const possiblePaths = [
        // 현재 사용자의 Anaconda/Miniconda 경로
        path.join(process.env['USERPROFILE'] || '', 'anaconda3', 'python.exe'),
        path.join(process.env['USERPROFILE'] || '', 'miniconda3', 'python.exe'),
        path.join(process.env['LOCALAPPDATA'] || '', 'Programs', 'Python', 'Python312', 'python.exe'),
        path.join(process.env['LOCALAPPDATA'] || '', 'Programs', 'Python', 'Python311', 'python.exe'),
        path.join(process.env['LOCALAPPDATA'] || '', 'Programs', 'Python', 'Python310', 'python.exe'),
        'C:\\Python312\\python.exe',
        'C:\\Python311\\python.exe',
        'C:\\Python310\\python.exe',
    ];
    if (process.platform !== 'win32') {
        possiblePaths.push('/usr/bin/python3', '/usr/bin/python', '/usr/local/bin/python3', '/usr/local/bin/python');
    }
    for (const pythonPath of possiblePaths) {
        if (fs.existsSync(pythonPath)) {
            console.log(`Found Python at: ${pythonPath}`);
            return pythonPath;
        }
    }
    // 4. 기본값 반환
    console.warn('Could not find Python installation. Using default.');
    return process.platform === 'win32' ? 'python.exe' : 'python3';
}
function validatePythonPath(pythonPath) {
    try {
        const result = (0, child_process_1.spawnSync)(pythonPath, ['--version'], { encoding: 'utf8' });
        return result.status === 0;
    }
    catch (e) {
        return false;
    }
}
//# sourceMappingURL=python-path.js.map