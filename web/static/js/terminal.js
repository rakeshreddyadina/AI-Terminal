/**
 * AI-Powered Terminal Frontend Logic (Unified Interface Version)
 * =============================================================
 */

class Terminal {
    constructor() {
        this.currentDirectory = '~';
        this.commandHistory = [];
        this.historyIndex = -1;
        this.suggestionIndex = -1;
        this.suggestions = [];

        this.initializeElements();
        this.bindEvents();
        this.focusInput();
    }

    initializeElements() {
        // Terminal elements
        this.terminalOutput = document.getElementById('terminal-output');
        this.commandInput = document.getElementById('command-input');
        this.terminalPrompt = document.getElementById('terminal-prompt');
        this.currentDirSpan = document.getElementById('current-directory');
        this.inputModeIcon = document.getElementById('input-mode-icon');

        // System elements in header
        this.cpuUsage = document.getElementById('cpu-usage');
        this.memoryUsage = document.getElementById('memory-usage');
        this.connectionStatus = document.getElementById('connection-status');
        this.connectionText = document.getElementById('connection-text');
        this.aiStatus = document.getElementById('ai-status');

        // Suggestions
        this.suggestionsDiv = document.getElementById('suggestions');
        this.suggestionsList = document.getElementById('suggestions-list');
    }

    bindEvents() {
        // Command input events
        this.commandInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.commandInput.addEventListener('input', (e) => this.handleInput(e));
        this.commandInput.addEventListener('blur', () => this.hideSuggestions());

        // Keep input focused
        this.terminalOutput.parentElement.addEventListener('click', (e) => {
            if (!window.getSelection().toString()) {
                this.focusInput();
            }
        });
    }

    handleKeyDown(e) {
        switch (e.key) {
            case 'Enter':
                e.preventDefault();
                this.routeCommand();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateHistory(-1);
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.navigateHistory(1);
                break;
            case 'Tab':
                e.preventDefault();
                this.handleTabCompletion();
                break;
            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }

    handleInput(e) {
        const value = e.target.value;
        this.updateInputMode(value);
        if (value.length > 0) {
            this.requestSuggestions(value);
        } else {
            this.hideSuggestions();
        }
        this.suggestionIndex = -1;
    }

    routeCommand() {
        const command = this.commandInput.value.trim();
        if (!command) return;

        this.addToHistory(command);
        this.displayCommand(command);
        this.commandInput.value = '';
        this.updateInputMode(''); // Reset icon
        this.hideSuggestions();

        const isLikelyCmd = this.isLikelyStandardCommand(command);

        if (isLikelyCmd) {
            if (this.isDestructiveCommand(command)) {
                if (confirm(`⚠️ DESTRUCTIVE COMMAND ⚠️\n\nAre you sure you want to execute:\n${command}`)) {
                    window.socket.emit('execute_command', { command });
                } else {
                    this.displayError("Command cancelled by user.");
                    this.scrollToBottom();
                }
            } else {
                window.socket.emit('execute_command', { command });
            }
        } else {
            this.displayOutput('→ Sending to AI for translation...', 'info');
            window.socket.emit('natural_language_command', { query: command });
        }
    }

    isLikelyStandardCommand(input) {
        const parts = input.trim().split(' ');
        const firstWord = parts[0].toLowerCase();
        const commonCommands = ['ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'echo', 'git', 'docker', 'npm', 'pip', 'python', 'node', 'grep', 'find', 'clear', 'history', 'help', 'exit'];

        if (commonCommands.includes(firstWord)) return true;
        if (parts.length === 1 && (input.includes('/') || input.includes('./') || input.includes('../'))) return true;
        if (input.length < 10 && parts.length < 3) return true;

        return false;
    }

    isDestructiveCommand(command) {
        return command.trim().startsWith('rm ') && (command.includes(' -r') || command.includes(' -f'));
    }

    updateInputMode(value) {
        if (!value) {
            this.inputModeIcon.className = 'fas fa-terminal';
            this.inputModeIcon.title = 'Command Mode';
            return;
        }
        if (this.isLikelyStandardCommand(value)) {
            this.inputModeIcon.className = 'fas fa-terminal';
            this.inputModeIcon.title = 'Command Mode';
        } else {
            this.inputModeIcon.className = 'fas fa-brain ai-mode';
            this.inputModeIcon.title = 'AI Mode (Natural Language)';
        }
    }

    displayCommand(command) {
        const commandDiv = document.createElement('div');
        commandDiv.className = 'command-line';
        commandDiv.innerHTML = `
            <span class="terminal-prompt">${this.terminalPrompt.textContent}</span>
            <span class="command">${this.escapeHtml(command)}</span>
        `;
        this.terminalOutput.appendChild(commandDiv);
    }

    displayOutput(output, type = 'output') {
        if (!output) return;
        const outputDiv = document.createElement('div');
        outputDiv.className = `command-line ${type}`;
        outputDiv.innerHTML = `<pre>${this.escapeHtml(output)}</pre>`;
        this.terminalOutput.appendChild(outputDiv);
        this.scrollToBottom();
    }

    displayError(error) {
        this.displayOutput(error, 'error');
    }

    updatePrompt(cwd) {
        this.currentDirectory = cwd;
        // Simple tilde replacement for display
        const homePath = this.currentDirectory.split(/\/|\\/).slice(0, 3).join('/');
        const shortPath = cwd.startsWith(homePath) ? '~' + cwd.substring(homePath.length) : cwd;
        this.terminalPrompt.textContent = `user@ai-terminal:${shortPath}$ `;
        this.currentDirSpan.textContent = shortPath;
    }

    clearTerminal() {
        // Keep the welcome message
        const welcomeMessage = this.terminalOutput.querySelector('.welcome-message');
        this.terminalOutput.innerHTML = '';
        if (welcomeMessage) {
            this.terminalOutput.appendChild(welcomeMessage);
        }
    }

    // --- History, Suggestions, and Utility Methods ---

    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;
        if (this.historyIndex === -1) {
            this.historyIndex = this.commandHistory.length;
        }
        this.historyIndex += direction;

        if (this.historyIndex < 0) this.historyIndex = 0;
        if (this.historyIndex >= this.commandHistory.length) {
            this.historyIndex = this.commandHistory.length;
            this.commandInput.value = '';
            return;
        }
        this.commandInput.value = this.commandHistory[this.historyIndex] || '';
    }

    handleTabCompletion() {
        if (this.suggestions.length > 0) {
            this.commandInput.value = this.suggestions[0];
            this.hideSuggestions();
        }
    }

    addToHistory(command) {
        if (command && command !== this.commandHistory[this.commandHistory.length - 1]) {
            this.commandHistory.push(command);
        }
        this.historyIndex = -1;
    }

    requestSuggestions(partial) {
        if (window.socket) {
            window.socket.emit('get_suggestions', { partial });
        }
    }

    showSuggestions(suggestions) {
        this.suggestions = suggestions;
        if (suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        this.suggestionsList.innerHTML = suggestions.map(s => `<div class="suggestion-item">${s}</div>`).join('');
        this.suggestionsDiv.style.display = 'block';
    }

    hideSuggestions() {
        this.suggestionsDiv.style.display = 'none';
        this.suggestions = [];
    }

    // --- Status Updates ---

    updateSystemStats(stats) {
        if (stats.cpu_percent !== undefined) this.cpuUsage.textContent = `${Math.round(stats.cpu_percent)}%`;
        if (stats.memory_percent !== undefined) this.memoryUsage.textContent = `${Math.round(stats.memory_percent)}%`;
    }

    updateAIStatus(status, isReady) {
        this.aiStatus.textContent = status;
        this.aiStatus.parentElement.className = `stat-item ai-status ${isReady ? 'ready' : 'loading'}`;
    }

    updateConnectionStatus(connected) {
        this.connectionStatus.className = `status-indicator ${connected ? 'connected' : ''}`;
        this.connectionText.textContent = connected ? 'Connected' : 'Disconnected';
    }

    // --- Helpers ---

    focusInput() {
        this.commandInput.focus();
    }

    scrollToBottom() {
        this.terminalOutput.scrollTop = this.terminalOutput.scrollHeight;
    }

    escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize terminal when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.terminal = new Terminal();
    if (typeof io !== 'undefined') {
        initializeWebSocket();
    } else {
        console.error('Socket.IO library not found.');
        window.terminal.displayError('Error: Could not connect to the backend server.');
    }
});