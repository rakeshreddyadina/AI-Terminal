"""
Core Terminal Functionality
===========================
"""

import os
import json
import shlex
import subprocess
import platform
from pathlib import Path
from datetime import datetime

from core.file_manager import FileManager
from core.command_executor import CommandExecutor
from logs.logger import setup_logger

logger = setup_logger(__name__)


class Terminal:
    """Main terminal class handling command execution and state"""

    def __init__(self):
        self.current_directory = os.getcwd()
        self.command_history = self._load_history()
        self.file_manager = FileManager()
        self.command_executor = CommandExecutor()

        # Built-in commands
        self.builtin_commands = {
            'cd': self._cmd_cd,
            'pwd': self._cmd_pwd,
            'ls': self._cmd_ls,
            'dir': self._cmd_ls,  # Windows alias
            'mkdir': self._cmd_mkdir,
            'rmdir': self._cmd_rmdir,
            'rm': self._cmd_rm,
            'cp': self._cmd_cp,
            'mv': self._cmd_mv,
            'cat': self._cmd_cat,
            'echo': self._cmd_echo,
            'clear': self._cmd_clear,
            'history': self._cmd_history,
            'whoami': self._cmd_whoami,
            'uname': self._cmd_uname,
            'date': self._cmd_date,
            'help': self._cmd_help,
            'exit': self._cmd_exit,
            'ps': self._cmd_ps,
            'kill': self._cmd_kill,
            'df': self._cmd_df,
            'du': self._cmd_du,
            'find': self._cmd_find,
            'grep': self._cmd_grep,
            'touch': self._cmd_touch,
            'head': self._cmd_head,
            'tail': self._cmd_tail,
        }

    def execute_command(self, command_line):
        """Execute a command and return result"""
        try:
            command_line = command_line.strip()
            if not command_line:
                return {'output': '', 'error': '', 'cwd': self.current_directory}

            # Add to history
            self._add_to_history(command_line)

            # Parse command
            parts = shlex.split(command_line)
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            # Execute built-in command
            if command in self.builtin_commands:
                result = self.builtin_commands[command](args)
            else:
                # Execute system command
                result = self._execute_system_command(command_line)

            # Update current directory in result
            result['cwd'] = self.current_directory
            return result

        except Exception as e:
            logger.error(f"Error executing command '{command_line}': {e}")
            return {
                'output': '',
                'error': f"Error: {str(e)}",
                'cwd': self.current_directory
            }

    def _execute_system_command(self, command_line):
        """Execute system command"""
        try:
            # Use command executor for system commands
            result = self.command_executor.execute(command_line, self.current_directory)
            return result
        except Exception as e:
            return {
                'output': '',
                'error': f"Command not found or failed: {str(e)}",
                'cwd': self.current_directory
            }

    # Built-in command implementations
    def _cmd_cd(self, args):
        """Change directory command"""
        try:
            if not args:
                # Go to home directory
                new_dir = os.path.expanduser('~')
            elif args[0] == '..':
                new_dir = os.path.dirname(self.current_directory)
            elif args[0] == '-':
                # Go to previous directory (simplified)
                new_dir = os.path.expanduser('~')
            else:
                new_dir = args[0]
                if not os.path.isabs(new_dir):
                    new_dir = os.path.join(self.current_directory, new_dir)

            new_dir = os.path.abspath(new_dir)

            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.current_directory = new_dir
                return {'output': f"Changed to {new_dir}", 'error': ''}
            else:
                return {'output': '', 'error': f"Directory not found: {new_dir}"}
        except Exception as e:
            return {'output': '', 'error': f"cd: {str(e)}"}

    def _cmd_pwd(self, args):
        """Print working directory"""
        return {'output': self.current_directory, 'error': ''}

    def _cmd_ls(self, args):
        """List directory contents"""
        try:
            target_dir = self.current_directory
            show_hidden = '-a' in args or '--all' in args
            long_format = '-l' in args or '--long' in args

            # Get target directory from args (if not a flag)
            for arg in args:
                if not arg.startswith('-') and os.path.exists(arg):
                    if not os.path.isabs(arg):
                        target_dir = os.path.join(self.current_directory, arg)
                    else:
                        target_dir = arg
                    break

            return self.file_manager.list_directory(target_dir, show_hidden, long_format)
        except Exception as e:
            return {'output': '', 'error': f"ls: {str(e)}"}

    def _cmd_mkdir(self, args):
        """Create directory"""
        if not args:
            return {'output': '', 'error': 'mkdir: missing directory name'}

        results = []
        for dir_name in args:
            if not os.path.isabs(dir_name):
                dir_path = os.path.join(self.current_directory, dir_name)
            else:
                dir_path = dir_name

            result = self.file_manager.create_directory(dir_path)
            if result['error']:
                return result
            results.append(result['output'])

        return {'output': '\n'.join(results), 'error': ''}

    def _cmd_rmdir(self, args):
        """Remove empty directory"""
        if not args:
            return {'output': '', 'error': 'rmdir: missing directory name'}

        for dir_name in args:
            if not os.path.isabs(dir_name):
                dir_path = os.path.join(self.current_directory, dir_name)
            else:
                dir_path = dir_name

            result = self.file_manager.remove_directory(dir_path)
            if result['error']:
                return result

        return {'output': 'Directory removed', 'error': ''}

    def _cmd_rm(self, args):
        """Remove files or directories"""
        if not args:
            return {'output': '', 'error': 'rm: missing file name'}

        recursive = '-r' in args or '-rf' in args or '--recursive' in args
        force = '-f' in args or '-rf' in args or '--force' in args

        # Filter out flags to get file names
        files = [arg for arg in args if not arg.startswith('-')]

        for file_name in files:
            if not os.path.isabs(file_name):
                file_path = os.path.join(self.current_directory, file_name)
            else:
                file_path = file_name

            result = self.file_manager.remove_file(file_path, recursive, force)
            if result['error'] and not force:
                return result

        return {'output': 'Files removed', 'error': ''}

    def _cmd_cp(self, args):
        """Copy files"""
        if len(args) < 2:
            return {'output': '', 'error': 'cp: missing source or destination'}

        source = args[0]
        destination = args[1]

        if not os.path.isabs(source):
            source = os.path.join(self.current_directory, source)
        if not os.path.isabs(destination):
            destination = os.path.join(self.current_directory, destination)

        return self.file_manager.copy_file(source, destination)

    def _cmd_mv(self, args):
        """Move/rename files"""
        if len(args) < 2:
            return {'output': '', 'error': 'mv: missing source or destination'}

        source = args[0]
        destination = args[1]

        if not os.path.isabs(source):
            source = os.path.join(self.current_directory, source)
        if not os.path.isabs(destination):
            destination = os.path.join(self.current_directory, destination)

        return self.file_manager.move_file(source, destination)

    def _cmd_cat(self, args):
        """Display file contents"""
        if not args:
            return {'output': '', 'error': 'cat: missing file name'}

        file_name = args[0]
        if not os.path.isabs(file_name):
            file_path = os.path.join(self.current_directory, file_name)
        else:
            file_path = file_name

        return self.file_manager.read_file(file_path)

    def _cmd_echo(self, args):
        """Echo text"""
        return {'output': ' '.join(args), 'error': ''}

    def _cmd_clear(self, args):
        """Clear terminal (returns special flag)"""
        return {'output': '', 'error': '', 'clear': True}

    def _cmd_history(self, args):
        """Show command history"""
        history_text = []
        for i, cmd in enumerate(self.command_history[-50:], 1):  # Last 50 commands
            history_text.append(f"{i:4d}  {cmd}")
        return {'output': '\n'.join(history_text), 'error': ''}

    def _cmd_whoami(self, args):
        """Show current user"""
        import getpass
        return {'output': getpass.getuser(), 'error': ''}

    def _cmd_uname(self, args):
        """Show system information"""
        return {'output': f"{platform.system()} {platform.release()}", 'error': ''}

    def _cmd_date(self, args):
        """Show current date and time"""
        return {'output': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'error': ''}

    def _cmd_help(self, args):
        """Show help information"""
        help_text = """
Available commands:
  cd [dir]      - Change directory
  pwd           - Print working directory
  ls [-al] [dir] - List directory contents
  mkdir <dir>   - Create directory
  rm [-rf] <file> - Remove files/directories
  cp <src> <dst> - Copy files
  mv <src> <dst> - Move/rename files
  cat <file>    - Display file contents
  echo <text>   - Echo text
  clear         - Clear terminal
  history       - Show command history
  whoami        - Show current user
  uname         - Show system info
  date          - Show date/time
  ps            - Show processes
  kill <pid>    - Kill process
  df            - Show disk space
  du [dir]      - Show directory usage
  find <pattern> - Find files
  grep <pattern> <file> - Search in file
  touch <file>  - Create empty file
  head <file>   - Show first lines
  tail <file>   - Show last lines
  help          - Show this help
  exit          - Exit terminal
        """
        return {'output': help_text.strip(), 'error': ''}

    def _cmd_exit(self, args):
        """Exit terminal"""
        return {'output': 'Goodbye!', 'error': '', 'exit': True}

    def _cmd_ps(self, args):
        """Show processes"""
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = proc.info
                    processes.append(f"{info['pid']:6d} {info['name'][:30]:30s} {info['cpu_percent']:6.1f}%")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            output = "  PID COMMAND                        CPU%\n"
            output += "\n".join(processes[:20])  # Show first 20 processes
            return {'output': output, 'error': ''}
        except ImportError:
            return {'output': '', 'error': 'psutil not available'}

    def _cmd_kill(self, args):
        """Kill process"""
        if not args:
            return {'output': '', 'error': 'kill: missing process ID'}

        try:
            import psutil
            pid = int(args[0])
            process = psutil.Process(pid)
            process.terminate()
            return {'output': f'Process {pid} terminated', 'error': ''}
        except (ValueError, psutil.NoSuchProcess, ImportError) as e:
            return {'output': '', 'error': f'kill: {str(e)}'}

    def _cmd_df(self, args):
        """Show disk space"""
        try:
            import psutil
            disk_info = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append(
                        f"{partition.device:15s} {usage.total // 1024 // 1024:8d}M "
                        f"{usage.used // 1024 // 1024:8d}M {usage.free // 1024 // 1024:8d}M "
                        f"{partition.mountpoint}"
                    )
                except PermissionError:
                    pass

            output = "Filesystem         Total    Used    Free Mounted on\n"
            output += "\n".join(disk_info)
            return {'output': output, 'error': ''}
        except ImportError:
            return {'output': '', 'error': 'psutil not available'}

    def _cmd_du(self, args):
        """Show directory usage"""
        target_dir = args[0] if args else self.current_directory
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(self.current_directory, target_dir)

        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(target_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass

            return {'output': f"{total_size // 1024}K {target_dir}", 'error': ''}
        except Exception as e:
            return {'output': '', 'error': f'du: {str(e)}'}

    def _cmd_find(self, args):
        """Find files"""
        if not args:
            return {'output': '', 'error': 'find: missing pattern'}

        pattern = args[0]
        results = []

        try:
            for root, dirs, files in os.walk(self.current_directory):
                for file in files:
                    if pattern.lower() in file.lower():
                        results.append(os.path.join(root, file))
                if len(results) > 100:  # Limit results
                    break

            return {'output': '\n'.join(results), 'error': ''}
        except Exception as e:
            return {'output': '', 'error': f'find: {str(e)}'}

    def _cmd_grep(self, args):
        """Search in file"""
        if len(args) < 2:
            return {'output': '', 'error': 'grep: missing pattern or file'}

        pattern = args[0]
        filename = args[1]

        if not os.path.isabs(filename):
            filepath = os.path.join(self.current_directory, filename)
        else:
            filepath = filename

        try:
            results = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if pattern.lower() in line.lower():
                        results.append(f"{line_num}: {line.strip()}")

            return {'output': '\n'.join(results), 'error': ''}
        except Exception as e:
            return {'output': '', 'error': f'grep: {str(e)}'}

    def _cmd_touch(self, args):
        """Create empty file"""
        if not args:
            return {'output': '', 'error': 'touch: missing file name'}

        filename = args[0]
        if not os.path.isabs(filename):
            filepath = os.path.join(self.current_directory, filename)
        else:
            filepath = filename

        try:
            Path(filepath).touch()
            return {'output': f'Created {filename}', 'error': ''}
        except Exception as e:
            return {'output': '', 'error': f'touch: {str(e)}'}

    def _cmd_head(self, args):
        """Show first lines of file"""
        if not args:
            return {'output': '', 'error': 'head: missing file name'}

        filename = args[0]
        lines = 10  # default

        if len(args) > 2 and args[1] == '-n':
            try:
                lines = int(args[2])
            except ValueError:
                pass

        if not os.path.isabs(filename):
            filepath = os.path.join(self.current_directory, filename)
        else:
            filepath = filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = []
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    content.append(line.rstrip())

            return {'output': '\n'.join(content), 'error': ''}
        except Exception as e:
            return {'output': '', 'error': f'head: {str(e)}'}

    def _cmd_tail(self, args):
        """Show last lines of file"""
        if not args:
            return {'output': '', 'error': 'tail: missing file name'}

        filename = args[0]
        lines = 10  # default

        if len(args) > 2 and args[1] == '-n':
            try:
                lines = int(args[2])
            except ValueError:
                pass

        if not os.path.isabs(filename):
            filepath = os.path.join(self.current_directory, filename)
        else:
            filepath = filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                content = [line.rstrip() for line in all_lines[-lines:]]

            return {'output': '\n'.join(content), 'error': ''}
        except Exception as e:
            return {'output': '', 'error': f'tail: {str(e)}'}

    # Helper methods
    def get_current_directory(self):
        """Get current working directory"""
        return self.current_directory

    def get_directory_contents(self):
        """Get contents of current directory"""
        try:
            return os.listdir(self.current_directory)
        except Exception:
            return []

    def get_command_suggestions(self, partial_command):
        """Get command suggestions for autocomplete"""
        suggestions = []

        # Built-in command suggestions
        for cmd in self.builtin_commands.keys():
            if cmd.startswith(partial_command.lower()):
                suggestions.append(cmd)

        # File/directory suggestions if command contains space
        if ' ' in partial_command:
            parts = partial_command.split()
            if len(parts) >= 2:
                file_prefix = parts[-1]
                try:
                    for item in os.listdir(self.current_directory):
                        if item.startswith(file_prefix):
                            suggestions.append(' '.join(parts[:-1]) + ' ' + item)
                except Exception:
                    pass

        return suggestions[:10]  # Limit to 10 suggestions

    def get_command_history(self):
        """Get command history"""
        return self.command_history

    def _add_to_history(self, command):
        """Add command to history"""
        if command and command != self.command_history[-1:]:
            self.command_history.append(command)
            # Keep only last 1000 commands
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]
            self._save_history()

    def _load_history(self):
        """Load command history from file"""
        history_file = Path('logs/command_history.json')
        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
        return []

    def _save_history(self):
        """Save command history to file"""
        history_file = Path('logs/command_history.json')
        try:
            history_file.parent.mkdir(exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(self.command_history, f)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")