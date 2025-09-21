"""
File Manager - Handles file and directory operations
===================================================
"""

import os
import shutil
import stat
from pathlib import Path
from datetime import datetime
from logs.logger import setup_logger

logger = setup_logger(__name__)


class FileManager:
    """Handles file and directory operations"""

    def __init__(self):
        pass

    def list_directory(self, directory, show_hidden=False, long_format=False):
        """List directory contents"""
        try:
            if not os.path.exists(directory):
                return {'output': '', 'error': f"Directory not found: {directory}"}

            if not os.path.isdir(directory):
                return {'output': '', 'error': f"Not a directory: {directory}"}

            items = []
            try:
                dir_items = os.listdir(directory)
            except PermissionError:
                return {'output': '', 'error': f"Permission denied: {directory}"}

            # Filter hidden files if not requested
            if not show_hidden:
                dir_items = [item for item in dir_items if not item.startswith('.')]

            # Sort items
            dir_items.sort()

            if long_format:
                # Long format listing
                for item in dir_items:
                    item_path = os.path.join(directory, item)
                    try:
                        stat_info = os.stat(item_path)

                        # File type and permissions
                        mode = stat_info.st_mode
                        if os.path.isdir(item_path):
                            file_type = 'd'
                        elif os.path.islink(item_path):
                            file_type = 'l'
                        else:
                            file_type = '-'

                        # Permissions
                        perms = self._format_permissions(mode)

                        # Size
                        size = stat_info.st_size
                        size_str = self._format_size(size)

                        # Modified time
                        mtime = datetime.fromtimestamp(stat_info.st_mtime)
                        time_str = mtime.strftime('%b %d %H:%M')

                        # Format line
                        line = f"{file_type}{perms} {size_str:>8s} {time_str} {item}"
                        items.append(line)

                    except (OSError, PermissionError):
                        items.append(f"?????????? ? ? ? {item}")
            else:
                # Simple listing
                for item in dir_items:
                    item_path = os.path.join(directory, item)
                    if os.path.isdir(item_path):
                        items.append(f"{item}/")
                    else:
                        items.append(item)

            # Format output
            if long_format:
                output = '\n'.join(items)
            else:
                # Multi-column output
                if len(items) <= 10:
                    output = '  '.join(items)
                else:
                    # Split into columns
                    cols = 4
                    rows = (len(items) + cols - 1) // cols
                    formatted_items = []

                    for row in range(rows):
                        row_items = []
                        for col in range(cols):
                            idx = col * rows + row
                            if idx < len(items):
                                row_items.append(f"{items[idx]:<20s}")
                        formatted_items.append(''.join(row_items).rstrip())

                    output = '\n'.join(formatted_items)

            return {'output': output, 'error': ''}

        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return {'output': '', 'error': f"ls: {str(e)}"}

    def create_directory(self, directory_path):
        """Create a directory"""
        try:
            os.makedirs(directory_path, exist_ok=True)
            return {'output': f"Directory created: {directory_path}", 'error': ''}
        except PermissionError:
            return {'output': '', 'error': f"Permission denied: {directory_path}"}
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return {'output': '', 'error': f"mkdir: {str(e)}"}

    def remove_directory(self, directory_path):
        """Remove an empty directory"""
        try:
            if not os.path.exists(directory_path):
                return {'output': '', 'error': f"Directory not found: {directory_path}"}

            if not os.path.isdir(directory_path):
                return {'output': '', 'error': f"Not a directory: {directory_path}"}

            os.rmdir(directory_path)
            return {'output': f"Directory removed: {directory_path}", 'error': ''}

        except OSError as e:
            if e.errno == 39:  # Directory not empty
                return {'output': '', 'error': f"Directory not empty: {directory_path}"}
            else:
                return {'output': '', 'error': f"rmdir: {str(e)}"}
        except Exception as e:
            logger.error(f"Error removing directory {directory_path}: {e}")
            return {'output': '', 'error': f"rmdir: {str(e)}"}

    def remove_file(self, file_path, recursive=False, force=False):
        """Remove a file or directory"""
        try:
            if not os.path.exists(file_path):
                if force:
                    return {'output': '', 'error': ''}
                return {'output': '', 'error': f"File not found: {file_path}"}

            if os.path.isdir(file_path):
                if recursive:
                    shutil.rmtree(file_path)
                else:
                    return {'output': '', 'error': f"Is a directory: {file_path} (use -r for recursive)"}
            else:
                os.remove(file_path)

            return {'output': f"Removed: {file_path}", 'error': ''}

        except PermissionError:
            if force:
                return {'output': '', 'error': ''}
            return {'output': '', 'error': f"Permission denied: {file_path}"}
        except Exception as e:
            if force:
                return {'output': '', 'error': ''}
            logger.error(f"Error removing {file_path}: {e}")
            return {'output': '', 'error': f"rm: {str(e)}"}

    def copy_file(self, source, destination):
        """Copy a file or directory"""
        try:
            if not os.path.exists(source):
                return {'output': '', 'error': f"Source not found: {source}"}

            if os.path.isdir(source):
                if os.path.exists(destination):
                    if os.path.isdir(destination):
                        destination = os.path.join(destination, os.path.basename(source))
                    else:
                        return {'output': '', 'error': f"Destination exists and is not a directory: {destination}"}
                shutil.copytree(source, destination)
            else:
                if os.path.isdir(destination):
                    destination = os.path.join(destination, os.path.basename(source))
                shutil.copy2(source, destination)

            return {'output': f"Copied: {source} -> {destination}", 'error': ''}

        except PermissionError:
            return {'output': '', 'error': f"Permission denied"}
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return {'output': '', 'error': f"cp: {str(e)}"}

    def move_file(self, source, destination):
        """Move/rename a file or directory"""
        try:
            if not os.path.exists(source):
                return {'output': '', 'error': f"Source not found: {source}"}

            if os.path.isdir(destination) and not os.path.samefile(source, destination):
                destination = os.path.join(destination, os.path.basename(source))

            shutil.move(source, destination)
            return {'output': f"Moved: {source} -> {destination}", 'error': ''}

        except PermissionError:
            return {'output': '', 'error': f"Permission denied"}
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return {'output': '', 'error': f"mv: {str(e)}"}

    def read_file(self, file_path, max_size=1024 * 1024):  # 1MB limit
        """Read and display file contents"""
        try:
            if not os.path.exists(file_path):
                return {'output': '', 'error': f"File not found: {file_path}"}

            if os.path.isdir(file_path):
                return {'output': '', 'error': f"Is a directory: {file_path}"}

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return {'output': '', 'error': f"File too large: {file_size} bytes (max: {max_size})"}

            # Try to read as text
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return {'output': '', 'error': f"Cannot read file (binary or unknown encoding): {file_path}"}

            return {'output': content, 'error': ''}

        except PermissionError:
            return {'output': '', 'error': f"Permission denied: {file_path}"}
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {'output': '', 'error': f"cat: {str(e)}"}

    def write_file(self, file_path, content, append=False):
        """Write content to a file"""
        try:
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)

            action = "Appended to" if append else "Written to"
            return {'output': f"{action}: {file_path}", 'error': ''}

        except PermissionError:
            return {'output': '', 'error': f"Permission denied: {file_path}"}
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            return {'output': '', 'error': f"write: {str(e)}"}

    def get_file_info(self, file_path):
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return {'output': '', 'error': f"File not found: {file_path}"}

            stat_info = os.stat(file_path)

            info = {
                'path': file_path,
                'size': stat_info.st_size,
                'mode': oct(stat_info.st_mode)[-3:],
                'uid': stat_info.st_uid,
                'gid': stat_info.st_gid,
                'atime': datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                'mtime': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'ctime': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'is_dir': os.path.isdir(file_path),
                'is_file': os.path.isfile(file_path),
                'is_link': os.path.islink(file_path)
            }

            return {'output': info, 'error': ''}

        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {'output': '', 'error': f"stat: {str(e)}"}

    def _format_permissions(self, mode):
        """Format file permissions"""
        perms = ""

        # Owner permissions
        perms += 'r' if mode & stat.S_IRUSR else '-'
        perms += 'w' if mode & stat.S_IWUSR else '-'
        perms += 'x' if mode & stat.S_IXUSR else '-'

        # Group permissions
        perms += 'r' if mode & stat.S_IRGRP else '-'
        perms += 'w' if mode & stat.S_IWGRP else '-'
        perms += 'x' if mode & stat.S_IXGRP else '-'

        # Other permissions
        perms += 'r' if mode & stat.S_IROTH else '-'
        perms += 'w' if mode & stat.S_IWOTH else '-'
        perms += 'x' if mode & stat.S_IXOTH else '-'

        return perms

    def _format_size(self, size):
        """Format file size in human-readable format"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}K"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}M"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f}G"