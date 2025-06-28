import * as path from 'path';
import * as fs from 'fs';
import { spawnSync } from 'child_process';

export function getPythonPath(): string {
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
            const result = spawnSync(cmd, ['--version'], { encoding: 'utf8' });
            if (result.status === 0) {
                console.log(`Found Python in PATH: ${cmd}`);
                return cmd;
            }
        } catch (e) {
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
        'C:os.path.join(os.path.join(", "))Python312os.path.join(os.path.join(", "))python.exe',
        'C:os.path.join(", ")Python311os.path.join(", ")python.exe',
        'C:\\Python310\\python.exe',
    ];

    if (process.platform !== 'win32') {
        possiblePaths.push(
            '/usr/bin/python3',
            '/usr/bin/python',
            '/usr/local/bin/python3',
            '/usr/local/bin/python'
        );
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

export function validatePythonPath(pythonPath: string): boolean {
    try {
        const result = spawnSync(pythonPath, ['--version'], { encoding: 'utf8' });
        return result.status === 0;
    } catch (e) {
        return false;
    }
}
