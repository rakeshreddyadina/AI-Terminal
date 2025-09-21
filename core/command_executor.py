"""
Command Executor - Handles execution of system commands
======================================================
"""

import os
import subprocess
import shlex
import threading
import signal
import platform
from typing import Dict, Any
from logs.logger import setup_logger

logger = setup_logger(__name__)


class CommandExecutor:
    """Executes system commands safely"""

    def __init__(self):
        self.running_processes = {}
        self.process_lock = threading.Lock()

        # Command timeouts (in seconds)
        self.default_timeout = 30
        self.command_timeouts = {
            'ping': 10,
            'wget': 60,
            'curl': 60,
            'find': 60,
            'grep': 30,
            'tar': 120,
            'zip': 120,
            'unzip': 120
        }

    def execute(self, command: str, working_directory: str = None) -> Dict[str, Any]:
        """Execute a system command"""
        try:
            # Parse command
            if isinstance(command, str):
                cmd_parts = shlex.split(command)
            else:
                cmd_parts = command

            if not cmd_parts:
                return {'output': '', 'error': 'Empty command', 'returncode': 1}

            command_name = cmd_parts[0].lower()

            # Security check
            if not self._is_command_allowed(command_name):
                return {
                    'output': '',
                    'error': f'Command not allowed: {command_name}',
                    'returncode': 1
                }

            # Determine timeout
            timeout = self.command_timeouts.get(command_name, self.default_timeout)

            # Set working directory
            if working_directory and os.path.exists(working_directory):
                cwd = working_directory
            else:
                cwd = os.getcwd()

            # Execute command
            result = self._run_command(cmd_parts, cwd, timeout)
            return result

        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'returncode': 1
            }

    def _run_command(self, cmd_parts: list, cwd: str, timeout: int) -> Dict[str, Any]:
        """Run the actual command"""
        try:
            # Create process
            process = subprocess.Popen(
                cmd_parts,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                shell=False,  # Never use shell=True for security
                preexec_fn=None if platform.system() == "Windows" else os.setsid
            )

            # Store process for potential termination
            process_id = id(process)
            with self.process_lock:
                self.running_processes[process_id] = process

            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode

                # Clean up
                with self.process_lock:
                    self.running_processes.pop(process_id, None)

                # Process output
                output = self._process_output(stdout)
                error = self._process_output(stderr)

                return {
                    'output': output,
                    'error': error,
                    'returncode': returncode
                }

            except subprocess.TimeoutExpired:
                # Kill the process and its children
                self._kill_process_group(process)

                with self.process_lock:
                    self.running_processes.pop(process_id, None)

                return {
                    'output': '',
                    'error': f'Command timed out after {timeout} seconds',
                    'returncode': 124  # Standard timeout exit code
                }

        except FileNotFoundError:
            return {
                'output': '',
                'error': f'Command not found: {cmd_parts[0]}',
                'returncode': 127
            }
        except PermissionError:
            return {
                'output': '',
                'error': f'Permission denied: {cmd_parts[0]}',
                'returncode': 126
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution failed: {str(e)}',
                'returncode': 1
            }

    def _kill_process_group(self, process):
        """Kill a process and its children"""
        try:
            if platform.system() == "Windows":
                # Windows process termination
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            else:
                # Unix process group termination
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)

                # Give it a moment to terminate gracefully
                import time
                time.sleep(0.5)

                try:
                    # Force kill if still running
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already terminated
        except Exception as e:
            logger.error(f"Error killing process: {e}")

    def _process_output(self, output: str) -> str:
        """Process command output"""
        if not output:
            return ''

        # Remove excessive whitespace
        output = output.strip()

        # Limit output length to prevent overwhelming the terminal
        max_length = 10000  # 10KB
        if len(output) > max_length:
            output = output[:max_length] + '\n... [output truncated]'

        return output

    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to run"""
        # Allowed commands - whitelist approach for security
        allowed_commands = {
            # File operations
            'ls', 'dir', 'cat', 'head', 'tail', 'less', 'more', 'file',
            'find', 'locate', 'which', 'whereis', 'type',

            # Text processing
            'grep', 'egrep', 'fgrep', 'awk', 'sed', 'sort', 'uniq', 'cut',
            'tr', 'wc', 'diff', 'cmp',

            # Archive operations
            'tar', 'gzip', 'gunzip', 'zip', 'unzip', '7z',

            # System info
            'ps', 'top', 'htop', 'free', 'df', 'du', 'lsof', 'netstat',
            'uname', 'whoami', 'id', 'groups', 'uptime', 'date', 'cal',
            'env', 'printenv', 'history',

            # Network tools
            'ping', 'wget', 'curl', 'nslookup', 'dig', 'host',

            # Development tools
            'git', 'python', 'python3', 'node', 'npm', 'pip', 'pip3',
            'java', 'javac', 'gcc', 'g++', 'make', 'cmake',

            # Text editors (view mode)
            'vim', 'vi', 'nano', 'emacs',

            # Package managers (read-only operations)
            'apt', 'yum', 'dnf', 'pacman', 'brew',
        }

        # Commands that are explicitly blocked
        blocked_commands = {
            # System modification
            'rm', 'rmdir', 'del', 'erase', 'format', 'mkfs',
            'fdisk', 'parted', 'gparted',

            # System control
            'sudo', 'su', 'login', 'logout', 'exit', 'shutdown', 'reboot',
            'halt', 'poweroff', 'init', 'systemctl', 'service',

            # Network services
            'ssh', 'scp', 'rsync', 'ftp', 'sftp', 'telnet',

            # Process control
            'kill', 'killall', 'pkill', 'nohup', 'screen', 'tmux',

            # File permissions
            'chmod', 'chown', 'chgrp', 'umask',

            # Mount operations
            'mount', 'umount', 'swapon', 'swapoff',

            # Dangerous tools
            'dd', 'shred', 'wipe',
        }

        base_command = command.split('/')[-1]  # Handle full paths

        if base_command in blocked_commands:
            return False

        if base_command in allowed_commands:
            return True

        # Check if it's a built-in shell command that should be handled
        # by the terminal itself
        shell_builtins = {'cd', 'pwd', 'echo', 'help', 'clear', 'history'}
        if base_command in shell_builtins:
            return False  # Let the terminal handle these

        # For security, default to not allowing unknown commands
        logger.warning(f"Unknown command blocked: {command}")
        return False

    def terminate_all_processes(self):
        """Terminate all running processes"""
        with self.process_lock:
            for process_id, process in list(self.running_processes.items()):
                try:
                    self._kill_process_group(process)
                except Exception as e:
                    logger.error(f"Error terminating process {process_id}: {e}")

            self.running_processes.clear()

    def get_running_processes(self):
        """Get list of currently running processes managed by this executor"""
        with self.process_lock:
            return list(self.running_processes.keys())

    def terminate_process(self, process_id):
        """Terminate a specific process"""
        with self.process_lock:
            process = self.running_processes.get(process_id)
            if process:
                try:
                    self._kill_process_group(process)
                    self.running_processes.pop(process_id, None)
                    return True
                except Exception as e:
                    logger.error(f"Error terminating process {process_id}: {e}")
                    return False
            return False