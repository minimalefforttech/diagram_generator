#!/usr/bin/env node

import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Enable debug mode for verbose output
const DEBUG = true;

function log(message) {
    if (DEBUG) {
        console.log(`[Setup] ${message}`);
    }
}

function run() {
    log('Starting PlantUML setup...');
    log(`Current directory: ${process.cwd()}`);
    log(`Script directory: ${__dirname}`);
    log(`Node version: ${process.version}`);
    log(`Platform: ${os.platform()}`);

    try {
        const isWindows = os.platform() === 'win32';
        const scriptPath = join(__dirname, isWindows ? 'compile-plantuml.ps1' : 'compile-plantuml.sh');
        
        log(`Using script: ${scriptPath}`);
        
        if (!fs.existsSync(scriptPath)) {
            throw new Error(`Setup script not found: ${scriptPath}`);
        }

        log(`Script exists: ${fs.existsSync(scriptPath)}`);

        if (isWindows) {
            log('Running PowerShell script...');
            execSync(`powershell -ExecutionPolicy Bypass -File "${scriptPath}"`, {
                stdio: 'inherit',
                windowsHide: true
            });
        } else {
            log('Running shell script...');
            // Make script executable
            fs.chmodSync(scriptPath, '755');
            execSync(scriptPath, {
                stdio: 'inherit',
                shell: '/bin/bash'
            });
        }

        log('Setup completed successfully!');
    } catch (error) {
        console.error('Failed to setup PlantUML:', error.message);
        if (error.stdout) console.log('Output:', error.stdout.toString());
        if (error.stderr) console.log('Error:', error.stderr.toString());
        process.exit(1);
    }
}

run();
