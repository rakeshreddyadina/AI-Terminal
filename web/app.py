"""
Flask Web Application Blueprint for AI Terminal
===============================================

This file defines the web application's structure but does not run it.
It provides the `create_app` factory function, which main.py uses to build
and configure the Flask app and its routes.
"""

import os
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

from logs.logger import setup_logger

logger = setup_logger(__name__)

# Create the SocketIO instance at the module level, unattached to an app.
# The @socketio decorators will attach to this instance.
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

# Module-level placeholders for the core components.
# These will be assigned by the create_app factory.
terminal = None
model_manager = None
system_monitor = None

def create_app(terminal_instance, system_monitor_instance, model_manager_instance):
    """
    Creates and configures the Flask application instance (Application Factory).
    """
    global terminal, system_monitor, model_manager

    # Assign the pre-initialized instances passed from main.py
    terminal = terminal_instance
    system_monitor = system_monitor_instance
    model_manager = model_manager_instance

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'web', 'templates')
    static_dir = os.path.join(project_root, 'web', 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    app.config['SECRET_KEY'] = 'ai-terminal-secret-key-2025'

    # --- Register HTTP Routes ---
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/model-status')
    def get_model_status():
        if model_manager:
            return jsonify({'ready': model_manager.is_model_ready()})
        return jsonify({'ready': False})

    # Link the app instance with SocketIO
    socketio.init_app(app)

    # Start background tasks that need the socketio context
    start_background_tasks()

    logger.info("Flask app created and configured successfully.")
    return app

# --- WebSocket Event Handlers ---
# These are defined outside the factory, but use the module-level components.

@socketio.on('connect')
def handle_connect():
    """Handles new client connections."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'Successfully connected to AI Terminal backend.'})
    if system_monitor:
        emit('system_info', system_monitor.get_system_info())

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('execute_command')
def handle_execute_command(data):
    """Executes a standard terminal command."""
    command = data.get('command', '').strip()
    if terminal and command:
        result = terminal.execute_command(command)
        emit('command_result', result)

@socketio.on('natural_language_command')
def handle_natural_language_command(data):
    """Translates a natural language query into a shell command."""
    nl_query = data.get('query', '').strip()
    if model_manager and model_manager.is_model_ready() and nl_query:
        context = {
            'current_dir': terminal.get_current_directory() if terminal else '~',
            'dir_contents': terminal.get_directory_contents() if terminal else []
        }
        # This line contains the fix for the previous AttributeError
        translated_command = model_manager.translate_command(nl_query, context)
        emit('nl_result', {'command': translated_command})
    else:
        emit('nl_result', {'error': 'AI model is not ready yet. Please wait.'})

@socketio.on('get_suggestions')
def handle_get_suggestions(data):
    """Provides command and file suggestions for autocompletion."""
    partial = data.get('partial', '')
    if terminal:
        suggestions = terminal.get_command_suggestions(partial)
        emit('suggestions', {'suggestions': suggestions})

@socketio.on('get_history')
def handle_get_history():
    """Retrieves the command history for the client."""
    if terminal:
        history = terminal.get_command_history()
        emit('history', {'history': history})

# --- Background Tasks ---
def start_background_tasks():
    """Initializes and starts background threads."""
    if not getattr(start_background_tasks, "has_started", False):
        start_background_tasks.has_started = True

        def system_monitor_task():
            """Periodically sends system stats to all connected clients."""
            while True:
                if system_monitor:
                    socketio.emit('system_info', system_monitor.get_system_info())
                socketio.sleep(5)

        threading.Thread(target=system_monitor_task, daemon=True).start()
        logger.info("Background system monitoring task started.")