import * as vscode from 'vscode';
import * as path from 'path';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('dia');
    const apiUrl = config.get<string>('apiUrl', 'http://localhost:8080');
    const repoId = config.get<string>('repoId', 'default');

    console.log('DIA Extension Activated');

    // 1. File Watcher for Delta Indexing
    const watcher = vscode.workspace.createFileSystemWatcher('**/*.{ts,py,js,go,rs,java}');
    
    watcher.onDidChange(async (uri) => {
        await indexFile(uri, apiUrl, repoId);
    });

    watcher.onDidCreate(async (uri) => {
        await indexFile(uri, apiUrl, repoId);
    });

    // 2. Command for manual analysis
    let disposable = vscode.commands.registerCommand('dia.analyzeSymbol', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const symbol = editor.document.getText(editor.selection);
        if (!symbol) {
            vscode.window.showErrorMessage('Please select a symbol to analyze');
            return;
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Analyzing impact of ${symbol}...`,
            cancellable: false
        }, async (progress) => {
            try {
                // Placeholder for analysis call
                const response = await axios.post(`${apiUrl}/api/v1/analyze/symbol`, {
                    repo_id: repoId,
                    symbol_name: symbol
                });
                vscode.window.showInformationMessage(`Analysis complete. Risk score: ${response.data.risk_score}`);
            } catch (err) {
                vscode.window.showErrorMessage(`Analysis failed: ${err}`);
            }
        });
    });

    context.subscriptions.push(disposable, watcher);
}

async function indexFile(uri: vscode.Uri, apiUrl: string, repoId: string) {
    try {
        const document = await vscode.workspace.openTextDocument(uri);
        const content = document.getText();
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
        
        if (!workspaceFolder) return;

        const relativePath = path.relative(workspaceFolder.uri.fsPath, uri.fsPath);
        
        await axios.post(`${apiUrl}/index/delta`, {
            repo_id: repoId,
            repo_root: workspaceFolder.uri.fsPath,
            file_path: relativePath,
            content: content
        });

        vscode.window.setStatusBarMessage(`⚡ DIA: Index updated (${relativePath})`, 3000);
    } catch (err) {
        console.error('Delta indexing failed:', err);
    }
}

export function deactivate() {}
