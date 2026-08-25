import * as assert from 'assert';
import * as vscode from 'vscode';

suite('AgentDocx SpecKit - Tests', () => {
    vscode.window.showInformationMessage('Démarrage des tests...');

    const expectedCommands = [
        'agentdocx-speckit.start_server',
        'agentdocx-speckit.stopServer',
        'agentdocx-speckit.startWatcher',
        'agentdocx-speckit.stopWatcher',
        'agentdocx-speckit.triggerPipeline'
    ];

    test('Commandes enregistrées', async () => {
        const allCommands = await vscode.commands.getCommands(true);
        for (const cmd of expectedCommands) {
            assert.ok(allCommands.includes(cmd), `Commande manquante: ${cmd}`);
        }
    });

    test('Cycle serveur', async () => {
        await vscode.commands.executeCommand('agentdocx-speckit.start_server');
        await new Promise(r => setTimeout(r, 3000));
        await vscode.commands.executeCommand('agentdocx-speckit.stopServer');
        assert.ok(true);
    });

    test('Cycle watcher', async () => {
        await vscode.commands.executeCommand('agentdocx-speckit.startWatcher');
        await new Promise(r => setTimeout(r, 2000));
        await vscode.commands.executeCommand('agentdocx-speckit.stopWatcher');
        assert.ok(true);
    });

    test('Health endpoint', async () => {
        await vscode.commands.executeCommand('agentdocx-speckit.start_server');
        await new Promise(r => setTimeout(r, 3000));
        
        const http = require('http');
        const healthy = await new Promise<boolean>((resolve, reject) => {
            const req = http.request({
                hostname: '127.0.0.1', port: 8000, path: '/health', method: 'GET'
            }, (res: any) => {
                let data = '';
                res.on('data', (c: any) => data += c);
                res.on('end', () => {
                    try { resolve(res.statusCode === 200 && JSON.parse(data).status === 'ok'); }
                    catch { resolve(false); }
                });
            });
            req.on('error', reject);
            req.end();
        });
        assert.ok(await healthy);
        await vscode.commands.executeCommand('agentdocx-speckit.stopServer');
    });
});