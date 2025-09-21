"""
Configuration settings for AI Terminal
=====================================
"""

import os
from pathlib import Path

# --- NEW: Add your Google API Key here ---
# Get your key from https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# --- MODIFIED: Set the Gemini model name ---
AI_MODEL_NAME = "gemini-2.5-flash"

# Web server settings
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
DEBUG = False

# Terminal settings
MAX_HISTORY_SIZE = 1000
MAX_OUTPUT_SIZE = 10000  # 10KB
COMMAND_TIMEOUT = 30  # seconds

# Security settings
ALLOWED_COMMANDS = {
    'ls', 'cat', 'head', 'tail', 'grep', 'find', 'ps', 'df', 'du', 'free',
    'uname', 'whoami', 'date', 'ping', 'curl', 'wget', 'git', 'python',
    'python3', 'node', 'npm', 'pip', 'pip3'
}

BLOCKED_COMMANDS = {
    'rm', 'sudo', 'su', 'chmod', 'chown', 'kill', 'shutdown', 'reboot',
    'dd', 'mkfs', 'fdisk', 'mount', 'umount'
}

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# System monitoring settings
MONITOR_INTERVAL = 2  # seconds
ENABLE_SYSTEM_MONITORING = True

# AI settings
AI_MAX_TOKENS = 100
AI_TEMPERATURE = 0.7
AI_TIMEOUT = 30  # seconds