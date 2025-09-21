"""
System Monitor - CPU, Memory, and System Information
===================================================
"""

import os
import platform
import threading
import time
from datetime import datetime
from logs.logger import setup_logger

logger = setup_logger(__name__)


class SystemMonitor:
    """Monitors system resources and provides system information"""

    def __init__(self):
        self._cpu_percent = 0.0
        self._memory_percent = 0.0
        self._disk_usage = {}
        self._system_info = {}
        self._lock = threading.Lock()

        # Initialize system info
        self._update_system_info()

        # Start monitoring thread
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                self._update_cpu_usage()
                self._update_memory_usage()
                self._update_disk_usage()
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _update_cpu_usage(self):
        """Update CPU usage"""
        try:
            # Try using psutil if available
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                with self._lock:
                    self._cpu_percent = cpu_percent
            except ImportError:
                # Fallback method for systems without psutil
                with self._lock:
                    self._cpu_percent = self._get_cpu_usage_fallback()
        except Exception as e:
            logger.error(f"Error updating CPU usage: {e}")

    def _update_memory_usage(self):
        """Update memory usage"""
        try:
            # Try using psutil if available
            try:
                import psutil
                memory = psutil.virtual_memory()
                with self._lock:
                    self._memory_percent = memory.percent
            except ImportError:
                # Fallback method
                with self._lock:
                    self._memory_percent = self._get_memory_usage_fallback()
        except Exception as e:
            logger.error(f"Error updating memory usage: {e}")

    def _update_disk_usage(self):
        """Update disk usage"""
        try:
            # Try using psutil if available
            try:
                import psutil
                disk_usage = {}
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_usage[partition.mountpoint] = {
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': (usage.used / usage.total) * 100
                        }
                    except PermissionError:
                        pass

                with self._lock:
                    self._disk_usage = disk_usage
            except ImportError:
                # Fallback method
                with self._lock:
                    self._disk_usage = self._get_disk_usage_fallback()
        except Exception as e:
            logger.error(f"Error updating disk usage: {e}")

    def _update_system_info(self):
        """Update system information"""
        try:
            system_info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'boot_time': self._get_boot_time(),
                'uptime': self._get_uptime()
            }

            # Add CPU info
            try:
                import psutil
                system_info['cpu_count'] = psutil.cpu_count()
                system_info['cpu_count_logical'] = psutil.cpu_count(logical=True)
            except ImportError:
                system_info['cpu_count'] = os.cpu_count() or 1
                system_info['cpu_count_logical'] = os.cpu_count() or 1

            # Add memory info
            try:
                import psutil
                memory = psutil.virtual_memory()
                system_info['total_memory'] = memory.total
                system_info['available_memory'] = memory.available
            except ImportError:
                system_info['total_memory'] = self._get_total_memory_fallback()
                system_info['available_memory'] = 0

            with self._lock:
                self._system_info = system_info

        except Exception as e:
            logger.error(f"Error updating system info: {e}")

    def _get_cpu_usage_fallback(self):
        """Fallback method to get CPU usage without psutil"""
        try:
            if platform.system() == "Linux":
                with open('/proc/loadavg', 'r') as f:
                    load_avg = float(f.read().split()[0])
                # Rough approximation: load average as percentage
                return min(load_avg * 100, 100.0)
            else:
                # For other systems, return a placeholder
                return 0.0
        except:
            return 0.0

    def _get_memory_usage_fallback(self):
        """Fallback method to get memory usage without psutil"""
        try:
            if platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        key, value = line.split(':')
                        meminfo[key.strip()] = int(value.split()[0]) * 1024  # Convert to bytes

                total = meminfo.get('MemTotal', 0)
                available = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))

                if total > 0:
                    used = total - available
                    return (used / total) * 100

            return 0.0
        except:
            return 0.0

    def _get_disk_usage_fallback(self):
        """Fallback method to get disk usage without psutil"""
        try:
            disk_usage = {}

            if platform.system() == "Windows":
                import shutil
                total, used, free = shutil.disk_usage("C:\\")
                disk_usage["C:\\"] = {
                    'total': total,
                    'used': used,
                    'free': free,
                    'percent': (used / total) * 100
                }
            else:
                import shutil
                total, used, free = shutil.disk_usage("/")
                disk_usage["/"] = {
                    'total': total,
                    'used': used,
                    'free': free,
                    'percent': (used / total) * 100
                }

            return disk_usage
        except:
            return {}

    def _get_total_memory_fallback(self):
        """Fallback method to get total memory without psutil"""
        try:
            if platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            return int(line.split()[1]) * 1024  # Convert to bytes
            return 0
        except:
            return 0

    def _get_boot_time(self):
        """Get system boot time"""
        try:
            import psutil
            return datetime.fromtimestamp(psutil.boot_time()).isoformat()
        except ImportError:
            return "Unknown"

    def _get_uptime(self):
        """Get system uptime"""
        try:
            import psutil
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time

            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)

            return f"{days}d {hours}h {minutes}m"
        except ImportError:
            return "Unknown"

    def get_system_info(self):
        """Get current system information"""
        with self._lock:
            return {
                'cpu_percent': round(self._cpu_percent, 1),
                'memory_percent': round(self._memory_percent, 1),
                'disk_usage': self._disk_usage,
                'system_info': self._system_info,
                'timestamp': datetime.now().isoformat()
            }

    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        with self._lock:
            return self._cpu_percent

    def get_memory_usage(self):
        """Get current memory usage percentage"""
        with self._lock:
            return self._memory_percent

    def get_disk_usage(self):
        """Get current disk usage information"""
        with self._lock:
            return self._disk_usage

    def get_process_list(self):
        """Get list of running processes"""
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return processes
        except ImportError:
            return []

    def kill_process(self, pid):
        """Kill a process by PID"""
        try:
            import psutil
            process = psutil.Process(pid)
            process.terminate()
            return True
        except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_network_info(self):
        """Get network interface information"""
        try:
            import psutil
            network_info = {}

            # Network interfaces
            interfaces = psutil.net_if_addrs()
            for interface_name, interface_addresses in interfaces.items():
                network_info[interface_name] = []
                for address in interface_addresses:
                    network_info[interface_name].append({
                        'family': str(address.family),
                        'address': address.address,
                        'netmask': address.netmask,
                        'broadcast': address.broadcast
                    })

            # Network statistics
            net_io = psutil.net_io_counters()
            network_info['io_counters'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }

            return network_info
        except ImportError:
            return {}

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self._monitoring = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_monitoring()