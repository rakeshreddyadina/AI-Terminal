"""
AI-Powered Terminal - Main Entry Point
=====================================

This script initializes all the core components of the application
and starts the Flask web server. This is the only file you should run.
"""

import os
import sys
from pathlib import Path
import subprocess

# Add project root to path to ensure modules can be imported
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the factory function and socketio instance from the app blueprint
from web.app import create_app, socketio
# Import the component classes to be initialized
from core.terminal import Terminal
from core.system_monitor import SystemMonitor
from ai.model_manager import ModelManager
from logs.logger import setup_logger

logger = setup_logger(__name__)

def setup_environment():
    """Create directories and install required packages."""
    # Create directories
    dirs_to_create = [
        'logs', 'web/templates', 'web/static/css',
        'web/static/js', 'core', 'ai', 'config'
    ]
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        (Path(dir_path) / '__init__.py').touch(exist_ok=True)

    # Install requirements
    requirements_file = project_root / 'requirements.txt'
    try:
        logger.info("Checking and installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        logger.info("All packages are up to date.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        return False

def main():
    """Main application entry point."""
    print("Starting AI-Powered Terminal...")
    logger.info("Application starting up.")

    # --- Step 1: Setup Environment ---
    if not setup_environment():
        print("❌ Error: Failed to install required packages. Please see the log.")
        sys.exit(1)

    # --- Step 2: Initialize Core Components ---
    logger.info("Initializing core components...")
    terminal = Terminal()
    system_monitor = SystemMonitor()
    model_manager = ModelManager()

    # --- Step 3: Create the Web Application using the Factory ---
    # The components are passed into the factory to build the app
    app = create_app(
        terminal_instance=terminal,
        system_monitor_instance=system_monitor,
        model_manager_instance=model_manager
    )

    # --- Step 4: Run the Server ---
    logger.info("Starting web server on http://localhost:5000")
    print("\n" + "="*50)
    print("🚀 AI Terminal is ready!")
    print(f"🌍 Access the interface at: http://localhost:5000")
    print("="*50 + "\n")

    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.critical(f"Failed to start the web server: {e}", exc_info=True)
        print(f"❌ A critical error occurred: {e}")
        return 1

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Terminal. Goodbye!")
        sys.exit(0)