#!/usr/bin/env node

import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('Checking environment setup...\n');

// System information
console.log('System Information:');
console.log('-----------------');
console.log('Platform:', process.platform);
console.log('Architecture:', process.arch);
console.log('Node Version:', process.version);
console.log('Working Directory:', process.cwd());
console.log('Script Directory:', __dirname);

// Check Python availability
console.log('\nPython Check:');
console.log('-----------');
try {
    const pythonVersion = execSync('python --version 2>&1').toString().trim();
    console.log('Python Version:', pythonVersion);
} catch (err) {
    try {
        const python3Version = execSync('python3 --version 2>&1').toString().trim();
        console.log('Python3 Version:', python3Version);
    } catch (err) {
        console.error('❌ Python not found. Please install Python and add it to your PATH');
        process.exit(1);
    }
}

// Check PowerShell/Bash availability
console.log('\nShell Check:');
console.log('-----------');
if (process.platform === 'win32') {
    try {
        const psVersion = execSync('powershell $PSVersionTable.PSVersion.Major').toString().trim();
        console.log('PowerShell Version:', psVersion);
    } catch (err) {
        console.error('❌ PowerShell not found or not accessible');
        process.exit(1);
    }
} else {
    try {
        const bashVersion = execSync('bash --version').toString().split('\n')[0];
        console.log('Bash Version:', bashVersion);
    } catch (err) {
        console.error('❌ Bash not found or not accessible');
        process.exit(1);
    }
}

// Check file permissions
console.log('\nPermissions Check:');
console.log('-----------------');
try {
    const testDir = join(__dirname, '.test-permissions');
    fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(join(testDir, 'test.txt'), 'test');
    fs.unlinkSync(join(testDir, 'test.txt'));
    fs.rmdirSync(testDir);
    console.log('✅ Write permissions OK');
} catch (err) {
    console.error('❌ Write permissions missing:', err.message);
    process.exit(1);
}

// Check script files
console.log('\nScript Files Check:');
console.log('-----------------');
const isWindows = process.platform === 'win32';
const setupScript = join(__dirname, isWindows ? 'compile-plantuml.ps1' : 'compile-plantuml.sh');

if (fs.existsSync(setupScript)) {
    console.log(`✅ Setup script found: ${setupScript}`);
} else {
    console.error(`❌ Setup script missing: ${setupScript}`);
    process.exit(1);
}

console.log('\n✅ Environment check completed successfully!');
console.log('You can now run: npm run setup:plantuml');
