#!/usr/bin/env python3
"""
IPFS Health Monitor
Comprehensive monitoring script for IPFS node health and performance
"""

import requests
import json
import subprocess
import sys
import os
import time
from pathlib import Path
from datetime import datetime
import argparse

# Try to import psutil, install if not available
try:
    import psutil
except ImportError:
    print("Installing required dependency: psutil")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

class IPFSHealthMonitor:
    def __init__(self, ipfs_api_url="http://127.0.0.1:5001"):
        self.ipfs_api_url = ipfs_api_url
        self.session = requests.Session()
        self.session.timeout = 10
        
    def check_daemon_status(self):
        """Check if IPFS daemon is running and accessible"""
        try:
            response = self.session.get(f'{self.ipfs_api_url}/api/v0/version')
            if response.status_code == 200:
                version_info = response.json()
                return {
                    'status': 'healthy',
                    'version': version_info.get('Version', 'Unknown'),
                    'commit': version_info.get('Commit', 'Unknown')
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
        
    def check_service_status(self):
        """Check systemd service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'ipfs'],
                capture_output=True, text=True
            )
            active = result.returncode == 0
            
            # Get service uptime
            result = subprocess.run(
                ['systemctl', 'show', 'ipfs', '--property=ActiveEnterTimestamp'],
                capture_output=True, text=True
            )
            
            uptime = "Unknown"
            if result.returncode == 0 and result.stdout:
                timestamp_line = result.stdout.strip()
                if '=' in timestamp_line:
                    timestamp_str = timestamp_line.split('=', 1)[1]
                    if timestamp_str and timestamp_str != "0":
                        try:
                            start_time = datetime.strptime(
                                timestamp_str.split('.')[0], 
                                "%a %Y-%m-%d %H:%M:%S %Z"
                            )
                            uptime_delta = datetime.now() - start_time
                            uptime = str(uptime_delta).split('.')[0]
                        except:
                            pass
            
            return {
                'active': active,
                'uptime': uptime
            }
        except Exception as e:
            return {
                'active': False,
                'error': str(e)
            }
    
    def get_repo_stats(self):
        """Get IPFS repository statistics"""
        try:
            response = self.session.get(f'{self.ipfs_api_url}/api/v0/stats/repo')
            if response.status_code == 200:
                stats = response.json()
                return {
                    'status': 'success',
                    'size_bytes': stats.get('RepoSize', 0),
                    'size_mb': round(stats.get('RepoSize', 0) / 1024 / 1024, 2),
                    'objects': stats.get('NumObjects', 0),
                    'version': stats.get('Version', 'Unknown')
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_swarm_stats(self):
        """Get swarm peer statistics"""
        try:
            response = self.session.get(f'{self.ipfs_api_url}/api/v0/swarm/peers')
            if response.status_code == 200:
                peers_data = response.json()
                peers = peers_data.get('Peers', [])
                return {
                    'status': 'success',
                    'peer_count': len(peers),
                    'peers': peers[:5]  # First 5 peers for sample
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_pin_stats(self):
        """Get pinning statistics"""
        try:
            # Get pinned objects count
            result = subprocess.run(
                ['sudo', '-u', 'ipfs', '/usr/local/bin/ipfs', 'pin', 'ls', '--type=recursive'],
                capture_output=True, text=True, env={'IPFS_PATH': '/mnt/ssd/ipfs'}
            )
            
            if result.returncode == 0:
                pin_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                return {
                    'status': 'success',
                    'pinned_objects': pin_count
                }
            else:
                return {
                    'status': 'error',
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_system_stats(self):
        """Get system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage for IPFS data directory
            disk_usage = psutil.disk_usage('/mnt/ssd')
            
            # Network IO
            net_io = psutil.net_io_counters()
            
            # IPFS process info
            ipfs_process = None
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'ipfs' in proc.info['name']:
                        ipfs_process = proc.info
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
                    'used_gb': round(memory.used / 1024 / 1024 / 1024, 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk_usage.total / 1024 / 1024 / 1024, 2),
                    'used_gb': round(disk_usage.used / 1024 / 1024 / 1024, 2),
                    'free_gb': round(disk_usage.free / 1024 / 1024 / 1024, 2),
                    'percent': round((disk_usage.used / disk_usage.total) * 100, 2)
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv
                },
                'ipfs_process': ipfs_process
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def check_nft_data(self):
        """Check NFT data directory statistics"""
        nft_data_dir = Path('/mnt/ssd/nft_data')
        
        if not nft_data_dir.exists():
            return {
                'status': 'not_found',
                'message': 'NFT data directory not found'
            }
        
        try:
            # Count NFT files
            summary_files = list(nft_data_dir.glob('*_summary.json'))
            metadata_files = list(nft_data_dir.glob('*_metadata.json'))
            image_files = list(nft_data_dir.glob('*_image.*'))
            
            # Calculate directory size
            total_size = 0
            for file_path in nft_data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return {
                'status': 'success',
                'nft_count': len(summary_files),
                'metadata_files': len(metadata_files),
                'image_files': len(image_files),
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_health_check(self, verbose=False):
        """Run comprehensive health check"""
        print("🏥 IPFS Node Health Check")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check daemon status
        print("🔍 IPFS Daemon Status")
        daemon_status = self.check_daemon_status()
        if daemon_status['status'] == 'healthy':
            print(f"  ✅ IPFS daemon is running")
            print(f"  📦 Version: {daemon_status['version']}")
            if verbose:
                print(f"  🔗 Commit: {daemon_status['commit']}")
        else:
            print(f"  ❌ IPFS daemon is not responding")
            print(f"  ⚠️  Error: {daemon_status.get('error', 'Unknown')}")
            return False
        
        print()
        
        # Check service status
        print("⚙️  Service Status")
        service_status = self.check_service_status()
        if service_status['active']:
            print(f"  ✅ IPFS service is active")
            print(f"  ⏱️  Uptime: {service_status['uptime']}")
        else:
            print(f"  ❌ IPFS service is not active")
            if 'error' in service_status:
                print(f"  ⚠️  Error: {service_status['error']}")
        
        print()
        
        # Repository stats
        print("📊 Repository Statistics")
        repo_stats = self.get_repo_stats()
        if repo_stats['status'] == 'success':
            print(f"  📁 Repository size: {repo_stats['size_mb']} MB")
            print(f"  🗂️  Objects: {repo_stats['objects']:,}")
            print(f"  📋 Version: {repo_stats['version']}")
        else:
            print(f"  ❌ Could not get repository stats")
            print(f"  ⚠️  Error: {repo_stats.get('error', 'Unknown')}")
        
        print()
        
        # Swarm stats
        print("🌐 Network Statistics")
        swarm_stats = self.get_swarm_stats()
        if swarm_stats['status'] == 'success':
            print(f"  🤝 Connected peers: {swarm_stats['peer_count']}")
            if verbose and swarm_stats['peers']:
                print("  📡 Sample peers:")
                for peer in swarm_stats['peers'][:3]:
                    addr = peer.get('Addr', 'Unknown')
                    print(f"    - {addr}")
        else:
            print(f"  ❌ Could not get swarm stats")
            print(f"  ⚠️  Error: {swarm_stats.get('error', 'Unknown')}")
        
        print()
        
        # Pin stats
        print("📌 Pinning Statistics")
        pin_stats = self.get_pin_stats()
        if pin_stats['status'] == 'success':
            print(f"  📍 Pinned objects: {pin_stats['pinned_objects']}")
        else:
            print(f"  ❌ Could not get pin stats")
            print(f"  ⚠️  Error: {pin_stats.get('error', 'Unknown')}")
        
        print()
        
        # System stats
        print("💻 System Resources")
        system_stats = self.get_system_stats()
        if 'error' not in system_stats:
            print(f"  🖥️  CPU usage: {system_stats['cpu_percent']}%")
            print(f"  🧠 Memory: {system_stats['memory']['used_gb']:.1f}GB / {system_stats['memory']['total_gb']:.1f}GB ({system_stats['memory']['percent']:.1f}%)")
            print(f"  💾 Disk: {system_stats['disk']['used_gb']:.1f}GB / {system_stats['disk']['total_gb']:.1f}GB ({system_stats['disk']['percent']:.1f}%)")
            
            if system_stats['ipfs_process']:
                print(f"  🔧 IPFS process: PID {system_stats['ipfs_process']['pid']}")
                if verbose:
                    print(f"    - CPU: {system_stats['ipfs_process']['cpu_percent']}%")
                    print(f"    - Memory: {system_stats['ipfs_process']['memory_percent']:.1f}%")
        else:
            print(f"  ❌ Could not get system stats")
            print(f"  ⚠️  Error: {system_stats['error']}")
        
        print()
        
        # NFT data stats
        print("🎨 NFT Data Statistics")
        nft_stats = self.check_nft_data()
        if nft_stats['status'] == 'success':
            print(f"  🖼️  NFT collections: {nft_stats['nft_count']}")
            print(f"  📄 Metadata files: {nft_stats['metadata_files']}")
            print(f"  🎭 Image files: {nft_stats['image_files']}")
            print(f"  📦 Total size: {nft_stats['total_size_mb']} MB")
        elif nft_stats['status'] == 'not_found':
            print(f"  ⚠️  {nft_stats['message']}")
        else:
            print(f"  ❌ Could not check NFT data")
            print(f"  ⚠️  Error: {nft_stats.get('error', 'Unknown')}")
        
        print()
        
        # Health summary
        print("🏥 Health Summary")
        warnings = []
        
        if daemon_status['status'] != 'healthy':
            warnings.append("IPFS daemon not responding")
        
        if not service_status['active']:
            warnings.append("IPFS service not active")
        
        if 'disk' in system_stats and system_stats['disk']['percent'] > 90:
            warnings.append("Disk usage high (>90%)")
        
        if 'memory' in system_stats and system_stats['memory']['percent'] > 90:
            warnings.append("Memory usage high (>90%)")
        
        if swarm_stats.get('peer_count', 0) < 5:
            warnings.append("Low peer count (<5)")
        
        if warnings:
            print("  ⚠️  Warnings:")
            for warning in warnings:
                print(f"    - {warning}")
        else:
            print("  ✅ All systems healthy!")
        
        print()
        print("🌐 Web Interfaces:")
        print("  - IPFS WebUI: http://127.0.0.1:5001/webui/")
        print("  - IPFS Gateway: http://127.0.0.1:8080/ipfs/")
        
        return len(warnings) == 0
    
    def monitor_continuous(self, interval=60):
        """Run continuous monitoring"""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_health_check()
                print(f"⏰ Next check in {interval} seconds...")
                print("-" * 50)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    
    def export_metrics(self, output_file):
        """Export metrics to JSON file"""
        print(f"📊 Exporting metrics to {output_file}...")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'daemon': self.check_daemon_status(),
            'service': self.check_service_status(),
            'repository': self.get_repo_stats(),
            'swarm': self.get_swarm_stats(),
            'pinning': self.get_pin_stats(),
            'system': self.get_system_stats(),
            'nft_data': self.check_nft_data()
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"✅ Metrics exported successfully")
        except Exception as e:
            print(f"❌ Failed to export metrics: {e}")
    
    def check_alerts(self):
        """Check for alert conditions"""
        alerts = []
        
        # Check daemon
        daemon_status = self.check_daemon_status()
        if daemon_status['status'] != 'healthy':
            alerts.append({
                'severity': 'critical',
                'message': 'IPFS daemon not responding',
                'details': daemon_status.get('error', 'Unknown error')
            })
        
        # Check service
        service_status = self.check_service_status()
        if not service_status['active']:
            alerts.append({
                'severity': 'critical',
                'message': 'IPFS service not active',
                'details': service_status.get('error', 'Service stopped')
            })
        
        # Check system resources
        system_stats = self.get_system_stats()
        if 'disk' in system_stats:
            if system_stats['disk']['percent'] > 95:
                alerts.append({
                    'severity': 'critical',
                    'message': f"Disk usage critical: {system_stats['disk']['percent']:.1f}%",
                    'details': f"Only {system_stats['disk']['free_gb']:.1f}GB free"
                })
            elif system_stats['disk']['percent'] > 85:
                alerts.append({
                    'severity': 'warning',
                    'message': f"Disk usage high: {system_stats['disk']['percent']:.1f}%",
                    'details': f"{system_stats['disk']['free_gb']:.1f}GB free"
                })
        
        if 'memory' in system_stats and system_stats['memory']['percent'] > 90:
            alerts.append({
                'severity': 'warning',
                'message': f"Memory usage high: {system_stats['memory']['percent']:.1f}%",
                'details': f"Using {system_stats['memory']['used_gb']:.1f}GB of {system_stats['memory']['total_gb']:.1f}GB"
            })
        
        # Check swarm peers
        swarm_stats = self.get_swarm_stats()
        if swarm_stats.get('peer_count', 0) < 3:
            alerts.append({
                'severity': 'warning',
                'message': f"Low peer count: {swarm_stats.get('peer_count', 0)}",
                'details': 'Consider checking network connectivity'
            })
        
        return alerts

def main():
    parser = argparse.ArgumentParser(description='IPFS Health Monitor')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--continuous', '-c', type=int, metavar='INTERVAL',
                       help='Run continuous monitoring with specified interval (seconds)')
    parser.add_argument('--export', '-e', metavar='FILE',
                       help='Export metrics to JSON file')
    parser.add_argument('--alerts', '-a', action='store_true',
                       help='Check for alert conditions only')
    parser.add_argument('--api-url', default='http://127.0.0.1:5001',
                       help='IPFS API URL (default: http://127.0.0.1:5001)')
    
    args = parser.parse_args()
    
    monitor = IPFSHealthMonitor(ipfs_api_url=args.api_url)
    
    if args.alerts:
        alerts = monitor.check_alerts()
        if alerts:
            print("🚨 Active Alerts:")
            for alert in alerts:
                severity_icon = "🔴" if alert['severity'] == 'critical' else "🟡"
                print(f"  {severity_icon} {alert['severity'].upper()}: {alert['message']}")
                print(f"    Details: {alert['details']}")
            sys.exit(1)
        else:
            print("✅ No alerts")
            sys.exit(0)
    
    elif args.export:
        monitor.export_metrics(args.export)
    
    elif args.continuous:
        monitor.monitor_continuous(args.continuous)
    
    else:
        healthy = monitor.run_health_check(verbose=args.verbose)
        sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()