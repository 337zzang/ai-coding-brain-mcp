const { spawn, execSync } = require('child_process');
const path = require('path');

console.log('🔍 Python 경로 문제 진단');
console.log('=' * 50);

// 1. 현재 환경 확인
console.log('\n1️⃣ Node.js 환경');
console.log('  - Node 버전:', process.version);
console.log('  - 플랫폼:', process.platform);
console.log('  - 현재 디렉토리:', process.cwd());

// 2. Python 실행 파일 찾기
console.log('\n2️⃣ Python 실행 파일 위치');
const pythonPaths = [
    'python',
    'python.exe',
    'C:\\Users\\Administrator\\miniconda3\\python.exe',
    'C:\\Users\\Administrator\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe',
    path.join(process.env.USERPROFILE, 'miniconda3', 'python.exe')
];

for (const pythonPath of pythonPaths) {
    try {
        const version = execSync(`"${pythonPath}" --version`, { encoding: 'utf8' });
        console.log(`  ✅ ${pythonPath}: ${version.trim()}`);
    } catch (error) {
        console.log(`  ❌ ${pythonPath}: 실행 불가`);
    }
}

// 3. 환경 변수 확인
console.log('\n3️⃣ 환경 변수');
console.log('  - PATH에 Python 포함:', process.env.PATH.includes('python') ? '예' : '아니오');
console.log('  - PYTHONPATH:', process.env.PYTHONPATH || '설정되지 않음');
console.log('  - PYTHONIOENCODING:', process.env.PYTHONIOENCODING || '설정되지 않음');

// 4. Python 스크립트 실행 테스트
console.log('\n4️⃣ Python 스크립트 실행 테스트');
const testCode = 'import sys; print(f"Python {sys.version.split()[0]} 작동중")';

// 각 Python 경로로 시도
const workingPython = 'C:\\Users\\Administrator\\miniconda3\\python.exe';
try {
    const result = execSync(`"${workingPython}" -c "${testCode}"`, { encoding: 'utf8' });
    console.log(`  ✅ 실행 성공: ${result.trim()}`);
} catch (error) {
    console.log(`  ❌ 실행 실패:`, error.message);
}

// 5. MCP 서버 설정 제안
console.log('\n5️⃣ 해결 방법');
console.log('  1. package.json의 scripts에 Python 경로 추가:');
console.log('     "start": "set PYTHON=C:\\\\Users\\\\Administrator\\\\miniconda3\\\\python.exe && node dist/index.js"');
console.log('  2. 또는 시스템 PATH에 Python 추가');
console.log('  3. 또는 코드에서 직접 전체 경로 사용');
