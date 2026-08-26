import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as child_process from 'child_process';
import * as http from 'http';

let serverProcess: child_process.ChildProcess | undefined;
let watcherProcess: child_process.ChildProcess | undefined;
let frontendProcess: child_process.ChildProcess | undefined;

// 💡 Trois canaux de sortie distincts pour une traçabilité optimale
let serverOutputChannel: vscode.OutputChannel;
let watcherOutputChannel: vscode.OutputChannel;
let frontendOutputChannel: vscode.OutputChannel;

function getPythonExecutable(): string {
    return process.platform === 'win32' ? 'python' : 'python3';
}

// 🛠️ AUTO-INIT: Initialize .task_runtime and current-task.json for all projects in specs/
async function initTaskRuntimes(workspacePath: string, watcherChannel: vscode.OutputChannel) {
    const specsPath = path.join(workspacePath, 'specs');
    if (!fs.existsSync(specsPath)) return;

    try {
        const projectDirs = fs.readdirSync(specsPath);
        for (const projectDir of projectDirs) {
            const projectPath = path.join(specsPath, projectDir);
            if (!fs.statSync(projectPath).isDirectory()) continue;

            const runtimeDir = path.join(projectPath, '.task_runtime');
            const currentTaskFile = path.join(runtimeDir, 'current-task.json');

            if (!fs.existsSync(runtimeDir)) {
                fs.mkdirSync(runtimeDir, { recursive: true });
                watcherChannel.appendLine(`[INIT] Created runtime directory for ${projectDir}`);
            }

            // Problème 1 — ne jamais créer de tâches "done" avant que tasks.md n'existe
            // Si tasks.md n'existe pas, le runtime doit rester vide (tasks:{}) jusqu'à /speckit-tasks
            const tasksMdPath = path.join(projectPath, 'tasks.md');
            let expectedTasks: Record<string, string> | null = null;
            if (fs.existsSync(tasksMdPath)) {
                try {
                    const tasksContent = fs.readFileSync(tasksMdPath, 'utf8');
                    const matches = tasksContent.match(/\bT\d+\b/g);
                    if (matches) {
                        const unique = Array.from(new Set(matches)).sort();
                        expectedTasks = {};
                        for (const id of unique) {
                            // Seules les tâches du tasks.md réel sont valides — toutes en todo à l'initialisation
                            if (/^T\d+$/.test(id)) {
                                expectedTasks[id] = "todo";
                            }
                        }
                    }
                } catch {}
            }

            if (!fs.existsSync(currentTaskFile)) {
                const initialData: any = {
                    task_id: "",
                    file: "",
                    status: "todo",
                    project_name: projectDir,
                    updated_at: new Date().toISOString(),
                    tasks: expectedTasks && Object.keys(expectedTasks).length > 0 ? expectedTasks : {}
                };
                fs.writeFileSync(currentTaskFile, JSON.stringify(initialData, null, 2), 'utf8');
                watcherChannel.appendLine(`[INIT] Initialized current-task.json for ${projectDir} with ${Object.keys(initialData.tasks).length} tasks`);
            } else if (expectedTasks !== null) {
                // Si tasks.md existe mais current-task.json a un tasks incomplet (ex: 4 done sur spec.md), corriger en todo complet
                try {
                    const existing = JSON.parse(fs.readFileSync(currentTaskFile, 'utf8'));
                    const existingKeys = Object.keys(existing.tasks || {});
                    const expectedKeys = Object.keys(expectedTasks);
                    const isIncomplete = existingKeys.length !== expectedKeys.length || existingKeys.some(k => !(k in expectedTasks));
                    const hasPrematureDone = Object.values(existing.tasks || {}).some((v: any) => v === "done");
                    if ((isIncomplete || hasPrematureDone) && expectedKeys.length > 0) {
                        // Ne corriger que si le fichier semble avoir été généré prématurément (ex: T001 spec.md done)
                        const looksPremature = existing.file && existing.file.includes('spec.md');
                        if (looksPremature || isIncomplete) {
                            existing.tasks = expectedTasks;
                            existing.task_id = "";
                            existing.file = "";
                            existing.status = "todo";
                            existing.updated_at = new Date().toISOString();
                            fs.writeFileSync(currentTaskFile, JSON.stringify(existing, null, 2), 'utf8');
                            watcherChannel.appendLine(`[INIT] Corrected premature current-task.json for ${projectDir} → ${expectedKeys.length} todo`);
                        }
                    }
                } catch {}
            } else if (!fs.existsSync(tasksMdPath)) {
                // tasks.md n'existe pas encore — forcer un runtime vide même si un LLM l'a rempli prématurément
                try {
                    const existing = JSON.parse(fs.readFileSync(currentTaskFile, 'utf8'));
                    if (Object.keys(existing.tasks || {}).length > 0) {
                        existing.tasks = {};
                        existing.task_id = "";
                        existing.file = "";
                        existing.status = "todo";
                        existing.updated_at = new Date().toISOString();
                        fs.writeFileSync(currentTaskFile, JSON.stringify(existing, null, 2), 'utf8');
                        watcherChannel.appendLine(`[INIT] Reset premature tasks for ${projectDir} (tasks.md not yet generated)`);
                    }
                } catch {}
            }
        }
    } catch (err) {
        watcherChannel.appendLine(`[ERROR INIT] Failed to initialize task runtimes: ${err}`);
    }
}

export function activate(context: vscode.ExtensionContext) {
    // Initialisation des trois canaux d'affichage
    serverOutputChannel = vscode.window.createOutputChannel("AgentDocx Server");
    watcherOutputChannel = vscode.window.createOutputChannel("AgentDocx Watcher");
    frontendOutputChannel = vscode.window.createOutputChannel("AgentDocx Frontend");

    serverOutputChannel.appendLine("[INIT] Canal Serveur FastAPI prêt.");
    watcherOutputChannel.appendLine("[INIT] Canal Watcher Python prêt.");
    frontendOutputChannel.appendLine("[INIT] Canal Frontend React prêt.");

    // 🎯 Récupérer le dossier du workspace (projet ouvert)
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage("Aucun dossier de travail ouvert. Ouvrez un dossier contenant backend/ et specs/");
        return;
    }
    const workspacePath = workspaceFolder.uri.fsPath;

    // 🛠️ Auto-initialize .task_runtime folders and current-task.json files
    initTaskRuntimes(workspacePath, watcherOutputChannel);

    // 🎯 Chemins des scripts EMBARQUÉS dans l'extension (priorité) + fallback workspace
    const extensionScriptsPath = path.join(context.extensionPath, 'scripts', 'python');
    const workspaceScriptsPath = path.join(workspacePath, 'scripts', 'python');
    const scriptsPath = fs.existsSync(extensionScriptsPath) ? extensionScriptsPath : workspaceScriptsPath;
    
    // Détermination des chemins basés sur le workspace (projet ouvert)
    const backendPath = path.join(workspacePath, 'backend');
    const specsPath = path.join(workspacePath, 'specs');
    const frontendPath = path.join(workspacePath, 'frontend');
    
    // Vérifier que les dossiers requis existent
    if (!fs.existsSync(backendPath)) {
        vscode.window.showErrorMessage(`Dossier 'backend' introuvable dans le workspace : ${workspacePath}`);
        return;
    }
    if (!fs.existsSync(specsPath)) {
        vscode.window.showWarningMessage(`Dossier 'specs' introuvable dans le workspace : ${workspacePath}. Le watcher ne surveillera rien.`);
    }
    if (!fs.existsSync(frontendPath)) {
        vscode.window.showWarningMessage(`Dossier 'frontend' introuvable dans le workspace : ${workspacePath}. Le frontend ne sera pas lancé.`);
    }
    
    if (!fs.existsSync(scriptsPath)) {
        vscode.window.showErrorMessage(`Dossier 'scripts/python' introuvable ni dans l'extension ni dans le workspace`);
        return;
    }
    
    // Options pour child_process.spawn avec CWD et PYTHONPATH configurés sur le workspace
    const spawnOptions: child_process.SpawnOptions = {
        cwd: workspacePath,
        env: {
            ...process.env,
            PYTHONIOENCODING: 'utf-8',
            PYTHONPATH: workspacePath + path.delimiter + (process.env.PYTHONPATH || ''),
            // 🎯 Variables pour que les scripts Python trouvent le workspace
            SPECKIT_WORKSPACE: workspacePath,
            SPECKIT_SPECS_DIR: specsPath,
            SPECKIT_BACKEND_DIR: backendPath,
            SPECKIT_SCRIPTS_DIR: scriptsPath
        }
    };

    // =========================================================================
    // 1. Commande : Démarrer le Serveur FastAPI
    // =========================================================================
    const startServerCmd = vscode.commands.registerCommand('agentdocx-speckit.start_server', () => {
        serverOutputChannel.show(true);

        if (serverProcess) {
            serverOutputChannel.appendLine("[SERVEUR] Le serveur FastAPI est déjà en cours d'exécution.");
            return;
        }

        const scriptPath = path.join(scriptsPath, 'start_server.py');
        if (!fs.existsSync(scriptPath)) {
            vscode.window.showErrorMessage(`Script Python introuvable : ${scriptPath}`);
            serverOutputChannel.appendLine(`[ERREUR SERVEUR] Fichier non trouvé : ${scriptPath}`);
            return;
        }

        const pythonCmd = getPythonExecutable();
        serverOutputChannel.appendLine(`[SERVEUR] Démarrage de FastAPI (${pythonCmd} ${scriptPath})...`);

        serverProcess = child_process.spawn(pythonCmd, [scriptPath], spawnOptions);

        serverProcess.stdout?.on('data', (data) => {
            serverOutputChannel.appendLine(`[STDOUT] ${data.toString().trim()}`);
        });

        serverProcess.stderr?.on('data', (data) => {
            serverOutputChannel.appendLine(`[STDERR] ${data.toString().trim()}`);
        });

        serverProcess.on('close', (code) => {
            serverOutputChannel.appendLine(`[SERVEUR] Processus arrêté avec le code ${code}`);
            serverProcess = undefined;
        });

        serverProcess.on('error', (err) => {
            vscode.window.showErrorMessage(`Erreur lors du lancement de FastAPI : ${err.message}`);
            serverOutputChannel.appendLine(`[ERREUR] ${err.message}`);
            serverProcess = undefined;
        });
    });

    // =========================================================================
    // 2. Commande : Arrêter le Serveur FastAPI
    // =========================================================================
    const stopServerCmd = vscode.commands.registerCommand('agentdocx-speckit.stopServer', () => {
        serverOutputChannel.show(true);
        if (!serverProcess) {
            vscode.window.showInformationMessage("Aucun serveur FastAPI n'est en cours d'exécution.");
            return;
        }

        serverProcess.kill();
        serverProcess = undefined;
        serverOutputChannel.appendLine("[SERVEUR] Serveur FastAPI arrêté.");
        vscode.window.showInformationMessage("Serveur FastAPI arrêté.");
    });

    // =========================================================================
    // 3. Commande : Démarrer le Watcher Python
    // =========================================================================
    const startWatcherCmd = vscode.commands.registerCommand('agentdocx-speckit.startWatcher', () => {
        watcherOutputChannel.show(true);

        if (watcherProcess) {
            watcherOutputChannel.appendLine("[WATCHER] Le Watcher Python est déjà en cours d'exécution.");
            return;
        }

        const scriptPath = path.join(scriptsPath, 'spec_watcher.py');
        if (!fs.existsSync(scriptPath)) {
            vscode.window.showErrorMessage(`Script Watcher introuvable : ${scriptPath}`);
            watcherOutputChannel.appendLine(`[ERREUR WATCHER] Fichier non trouvé : ${scriptPath}`);
            return;
        }

        const pythonCmd = getPythonExecutable();
        watcherOutputChannel.appendLine(`[WATCHER] Démarrage du Watcher (${pythonCmd} ${scriptPath})...`);

        // Pass workspace path to watcher via environment variable
        const watcherEnv = {
            ...process.env,
            PYTHONIOENCODING: 'utf-8',
            PYTHONPATH: workspacePath + path.delimiter + (process.env.PYTHONPATH || ''),
            SPECKIT_WORKSPACE: workspacePath,
            SPECKIT_SPECS_DIR: specsPath,
            SPECKIT_BACKEND_DIR: backendPath,
            SPECKIT_SCRIPTS_DIR: scriptsPath
        };

        watcherProcess = child_process.spawn(pythonCmd, [scriptPath], {
            ...spawnOptions,
            env: watcherEnv
        });

        watcherProcess.stdout?.on('data', (data) => {
            watcherOutputChannel.appendLine(`[STDOUT] ${data.toString().trim()}`);
        });

        watcherProcess.stderr?.on('data', (data) => {
            watcherOutputChannel.appendLine(`[STDERR] ${data.toString().trim()}`);
        });

        watcherProcess.on('close', (code) => {
            watcherOutputChannel.appendLine(`[WATCHER] Processus Watcher arrêté avec le code ${code}`);
            watcherProcess = undefined;
        });

        watcherProcess.on('error', (err) => {
            vscode.window.showErrorMessage(`Erreur lors du lancement du Watcher : ${err.message}`);
            watcherOutputChannel.appendLine(`[ERREUR] ${err.message}`);
            watcherProcess = undefined;
        });
    });

    // =========================================================================
    // 4. Commande : Arrêter le Watcher Python
    // =========================================================================
    const stopWatcherCmd = vscode.commands.registerCommand('agentdocx-speckit.stopWatcher', () => {
        watcherOutputChannel.show(true);
        if (!watcherProcess) {
            vscode.window.showInformationMessage("Aucun Watcher Python n'est en cours d'exécution.");
            return;
        }

        watcherProcess.kill();
        watcherProcess = undefined;
        watcherOutputChannel.appendLine("[WATCHER] Watcher Python arrêté.");
        vscode.window.showInformationMessage("Watcher Python arrêté.");
    });

    // =========================================================================
    // 5. Commande : Déclencher la Régénération
    // =========================================================================
    const triggerPipelineCmd = vscode.commands.registerCommand('agentdocx-speckit.triggerPipeline', async () => {
        serverOutputChannel.show(true);
        serverOutputChannel.appendLine("[PIPELINE] Envoi de la demande de régénération à FastAPI...");

        if (!serverProcess) {
            serverOutputChannel.appendLine("[PIPELINE] Serveur éteint. Démarrage automatique...");
            await vscode.commands.executeCommand('agentdocx-speckit.start_server');
            await new Promise((resolve) => setTimeout(resolve, 2000));
        }

        const requestOptions: http.RequestOptions = {
            hostname: '127.0.0.1',
            port: 8000,
            path: '/health',
            method: 'GET'
        };

        const req = http.request(requestOptions, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                serverOutputChannel.appendLine(`[PIPELINE REPONSE ${res.statusCode}] : ${data}`);
                vscode.window.showInformationMessage("Pipeline contacté avec succès !");
            });
        });

        req.on('error', (err) => {
            serverOutputChannel.appendLine(`[PIPELINE ERREUR] ${err.message}`);
            vscode.window.showErrorMessage(`Erreur lors de l'appel au serveur FastAPI : ${err.message}`);
        });

        req.end();
    });

    // =========================================================================
    // 6. Commande : Démarrer le Frontend React
    // =========================================================================
    const startFrontendCmd = vscode.commands.registerCommand('agentdocx-speckit.start_frontend', () => {
        frontendOutputChannel.show(true);

        // Tuer tout processus existant sur le port 5000 avant de démarrer
        if (process.platform === 'win32') {
            const { exec } = require('child_process');
            exec('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :5000\') do taskkill /F /PID %a', (err: Error | null) => {
                if (!err) {
                    frontendOutputChannel.appendLine("[FRONTEND] Port 5000 libéré.");
                }
            });
        }

        if (frontendProcess) {
            frontendOutputChannel.appendLine("[FRONTEND] Le frontend React est déjà en cours d'exécution.");
            return;
        }

        if (!fs.existsSync(frontendPath)) {
            vscode.window.showErrorMessage(`Dossier 'frontend' introuvable : ${frontendPath}`);
            return;
        }

        const packageJsonPath = path.join(frontendPath, 'package.json');
        if (!fs.existsSync(packageJsonPath)) {
            vscode.window.showErrorMessage(`package.json introuvable dans : ${frontendPath}`);
            return;
        }

        const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
        frontendOutputChannel.appendLine(`[FRONTEND] Démarrage du frontend React (${npmCmd} start)...`);
        frontendOutputChannel.appendLine(`[FRONTEND] CWD: ${frontendPath}`);

        frontendProcess = child_process.spawn(npmCmd, ['start'], {
            cwd: frontendPath,
            shell: true,  // Important sur Windows pour npm.cmd
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8',
                PATH: process.env.PATH,
            }
        });

        frontendProcess.stdout?.on('data', (data) => {
            const output = data.toString();
            // Préserver les sauts de ligne pour lisibilité
            output.split('\n').forEach((line: string) => {
                const trimmed = line.trim();
                if (trimmed) {
                    frontendOutputChannel.appendLine(`[FRONTEND] ${trimmed}`);
                    // Détecter compilation réussie et afficher notification avec URL
                    if (trimmed.includes('Compiled successfully!') || trimmed.includes('webpack compiled successfully')) {
                        vscode.window.showInformationMessage('Frontend React compilé avec succès !', 'Ouvrir', 'Copier URL').then(selection => {
                            if (selection === 'Ouvrir') {
                                vscode.env.openExternal(vscode.Uri.parse('http://localhost:5000'));
                            } else if (selection === 'Copier URL') {
                                vscode.env.clipboard.writeText('http://localhost:5000');
                                vscode.window.showInformationMessage('URL copiée : http://localhost:5000');
                            }
                        });
                    }
                }
            });
        });

        frontendProcess.stderr?.on('data', (data) => {
            const output = data.toString();
            output.split('\n').forEach((line: string) => {
                if (line.trim()) {
                    frontendOutputChannel.appendLine(`[FRONTEND] ${line.trim()}`);
                }
            });
        });

        frontendProcess.on('close', (code) => {
            frontendOutputChannel.appendLine(`[FRONTEND] Processus arrêté avec le code ${code}`);
            frontendProcess = undefined;
        });

        frontendProcess.on('error', (err) => {
            vscode.window.showErrorMessage(`Erreur lors du lancement du frontend : ${err.message}`);
            frontendOutputChannel.appendLine(`[ERREUR] ${err.message}`);
            frontendProcess = undefined;
        });
    });

    // =========================================================================
    // 7. Commande : Arrêter le Frontend React
    // =========================================================================
    const stopFrontendCmd = vscode.commands.registerCommand('agentdocx-speckit.stop_frontend', () => {
        frontendOutputChannel.show(true);
        if (!frontendProcess) {
            vscode.window.showInformationMessage("Aucun frontend React n'est en cours d'exécution.");
            return;
        }

        frontendProcess.kill();
        frontendProcess = undefined;
        frontendOutputChannel.appendLine("[FRONTEND] Frontend React arrêté.");
        vscode.window.showInformationMessage("Frontend React arrêté.");
    });

    context.subscriptions.push(
        startServerCmd,
        stopServerCmd,
        startWatcherCmd,
        stopWatcherCmd,
        startFrontendCmd,
        stopFrontendCmd,
        triggerPipelineCmd,
        serverOutputChannel,
        watcherOutputChannel,
        frontendOutputChannel
    );

    // Démarrage automatique au chargement
    vscode.commands.executeCommand('agentdocx-speckit.start_server');
    vscode.commands.executeCommand('agentdocx-speckit.startWatcher');
    vscode.commands.executeCommand('agentdocx-speckit.start_frontend');
}

export function deactivate() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = undefined;
    }
    if (watcherProcess) {
        watcherProcess.kill();
        watcherProcess = undefined;
    }
    if (frontendProcess) {
        // Sur Windows, utiliser taskkill pour tuer l'arbre de processus complet
        if (process.platform === 'win32' && frontendProcess.pid) {
            const { exec } = require('child_process');
            exec(`taskkill /F /T /PID ${frontendProcess.pid}`, (err: Error | null) => {
                if (err) {
                    frontendOutputChannel.appendLine(`[FRONTEND] Erreur taskkill: ${err.message}`);
                }
            });
        } else {
            frontendProcess.kill();
        }
        frontendProcess = undefined;
    }
}
