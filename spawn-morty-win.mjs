#!/usr/bin/env node
import { spawn } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';

const Style = {
    RED: '\x1b[31m',
    GREEN: '\x1b[32m',
    YELLOW: '\x1b[33m',
    CYAN: '\x1b[36m',
    DIM: '\x1b[2m',
    RESET: '\x1b[0m',
};

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
}

function printMinimalPanel(title, data, color, icon) {
    console.log(`\n${Style[color]}${icon} ${title}${Style.RESET}`);
    for (const [k, v] of Object.entries(data)) {
        console.log(`  ${Style.DIM}${k}:${Style.RESET} ${v}`);
    }
    console.log('');
}

async function main() {
    const args = process.argv.slice(2);
    let ticketId, ticketPath, ticketFile, timeoutSeconds = 1200, task;
    
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--ticket-id') ticketId = args[++i];
        else if (args[i] === '--ticket-path') ticketPath = args[++i];
        else if (args[i] === '--ticket-file') ticketFile = args[++i];
        else if (args[i] === '--timeout') timeoutSeconds = parseInt(args[++i]);
        else task = args[i];
    }

    const resolvedTicketPath = path.resolve(ticketPath);
    fs.mkdirSync(resolvedTicketPath, { recursive: true });
    
    const extensionRoot = "C:\\Users\\THIAGO\\.gemini\\extensions\\pickle-rick";
    const sessionLog = path.join(resolvedTicketPath, `worker_session_${process.pid}.log`);

    printMinimalPanel('Spawning Morty Worker (Windows Fix V4 - No Sandbox)', {
        Request: task,
        Ticket: ticketId,
        Timeout: `${timeoutSeconds}s`,
        PID: process.pid,
    }, 'CYAN', '🥒');

    const includes = [extensionRoot, path.join(extensionRoot, 'skills'), resolvedTicketPath];
    // REMOVED -s (sandbox) because it fails on windows without docker
    const cmdArgs = ['-y']; 
    for (const include of includes) {
        if (fs.existsSync(include)) {
            cmdArgs.push('--include-directories', `"${include}"`);
        }
    }

    let workerPrompt = `# **TASK REQUEST**\n${task}\n\nYou are a Morty Worker. Implement the request above.`;
    if (ticketFile && fs.existsSync(ticketFile)) {
        workerPrompt += `\n\n# TARGET TICKET CONTENT\n${fs.readFileSync(ticketFile, 'utf8')}`;
    }
    workerPrompt += `\n\n# EXECUTION CONTEXT\n- SESSION_ROOT: ${path.dirname(resolvedTicketPath)}\n- TICKET_ID: ${ticketId}\n- TICKET_DIR: ${resolvedTicketPath}`;
    workerPrompt += '\n\n**IMPORTANT**: You are a localized worker. You are FORBIDDEN from working on ANY other tickets. Once you output `<promise>I AM DONE</promise>`, you MUST STOP and let the manager take over.\n\n1. Activate persona: \`activate_skill("load-pickle-persona")\`.\n2. Follow the Rick Loop lifecycle.\n3. Output: <promise>I AM DONE</promise>';

    const escapedPrompt = workerPrompt.replace(/"/g, '\\"');
    cmdArgs.push('-p', `"${escapedPrompt}"`);

    const logStream = fs.createWriteStream(sessionLog, { flags: 'w' });
    
    const proc = spawn('gemini', cmdArgs, {
        cwd: process.cwd(),
        env: { ...process.env, PICKLE_ROLE: 'worker' },
        stdio: ['inherit', 'pipe', 'pipe'],
        shell: true 
    });

    proc.stdout?.pipe(logStream);
    proc.stderr?.pipe(logStream);

    const spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    const startTime = Date.now();
    let spinnerIdx = 0;
    const spinnerTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        process.stdout.write(`\r   ${Style.CYAN}${spinner[spinnerIdx++ % spinner.length]}${Style.RESET} Worker Active... ${Style.DIM}[${formatTime(elapsed)}]${Style.RESET}\x1b[K`);
    }, 100);

    proc.on('close', (code) => {
        clearInterval(spinnerTimer);
        process.stdout.write('\r\x1b[K');
        logStream.end();
        const hasDone = fs.existsSync(sessionLog) && fs.readFileSync(sessionLog, 'utf8').includes('<promise>I AM DONE</promise>');
        printMinimalPanel('Worker Report', { status: `exit:${code}`, validation: hasDone ? 'successful' : 'failed' }, hasDone ? 'GREEN' : 'RED', '🥒');
        process.exit(hasDone ? 0 : 1);
    });
}
main();
