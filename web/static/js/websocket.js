/**
 * WebSocket Communication Handler (Unified Interface Version)
 * ==========================================================
 */

function initializeWebSocket() {
    // Initialize Socket.IO connection
    window.socket = io();

    // Connection events
    window.socket.on('connect', () => {
        console.log('Connected to AI Terminal server');
        window.terminal.updateConnectionStatus(true);
        window.terminal.updateAIStatus('AI Ready', true); // Assuming AI is ready on connect
    });

    window.socket.on('disconnect', () => {
        console.log('Disconnected from server');
        window.terminal.updateConnectionStatus(false);
        window.terminal.updateAIStatus('Disconnected', false);
    });

    window.socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        window.terminal.updateConnectionStatus(false);
        window.terminal.displayError('Connection error: ' + error.message);
    });

    // --- Main Event Handlers ---

    // Handles responses for standard commands (ls, cd, etc.)
    window.socket.on('command_result', (data) => {
        handleCommandResult(data);
    });

    // Handles responses for natural language queries
    window.socket.on('nl_result', (data) => {
        handleNLResult(data);
    });

    // Handles autocomplete suggestions
    window.socket.on('suggestions', (data) => {
        if (data.suggestions) {
            window.terminal.showSuggestions(data.suggestions);
        }
    });

    // Handles system information updates
    window.socket.on('system_info', (data) => {
        window.terminal.updateSystemStats(data);
    });

    // Initial connection confirmation
    window.socket.on('connected', (data) => {
        console.log('Server message:', data.status);
    });
}

/**
 * Processes the result from a standard command execution.
 * @param {object} data The data object from the server.
 */
function handleCommandResult(data) {
    // Handle special commands first
    if (data.clear) {
        window.terminal.clearTerminal();
        return;
    }

    if (data.exit) {
        window.terminal.displayOutput('Terminal session ended. Refresh to restart.');
        window.terminal.commandInput.disabled = true;
        return;
    }

    // Update the current working directory and prompt if it has changed
    if (data.cwd && data.cwd !== window.terminal.currentDirectory) {
        window.terminal.updatePrompt(data.cwd);
    }

    // Display standard output if it exists
    if (data.output) {
        window.terminal.displayOutput(data.output);
    }

    // Display error output if it exists
    if (data.error) {
        window.terminal.displayError(data.error);
    }
}

/**
 * Processes the result from a natural language translation.
 * @param {object} data The data object from the server.
 */
function handleNLResult(data) {
    if (data.error) {
        window.terminal.displayError(`AI Error: ${data.error}`);
    } else if (data.command) {
        // Auto-fill the command input with the AI's suggestion
        window.terminal.commandInput.value = data.command;
        window.terminal.focusInput();

        // Display the suggestion in the main terminal output for clarity
        const message = `AI Suggestion: \`${data.command}\`\n(Press Enter to run, or type a new command)`;
        window.terminal.displayOutput(message, 'ai-suggestion');
    }
}