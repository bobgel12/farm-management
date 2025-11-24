#!/usr/bin/env python3
"""
Simple script to view Django application logs
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / 'logs'

def view_logs(log_file='django.log', lines=50, follow=False):
    """View log file contents"""
    log_path = LOGS_DIR / log_file
    
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        return
    
    try:
        if follow:
            # Follow mode (like tail -f)
            import time
            with open(log_path, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                print(f"📋 Following {log_file} (Ctrl+C to stop)...")
                print("-" * 80)
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)
        else:
            # Show last N lines
            with open(log_path, 'r') as f:
                all_lines = f.readlines()
                total_lines = len(all_lines)
                start_line = max(0, total_lines - lines)
                
                print(f"📋 Showing last {min(lines, total_lines)} lines of {log_file} (total: {total_lines} lines)")
                print("-" * 80)
                for line in all_lines[start_line:]:
                    print(line.rstrip())
    except KeyboardInterrupt:
        print("\n\n👋 Stopped following logs")
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def list_logs():
    """List all available log files"""
    if not LOGS_DIR.exists():
        print(f"❌ Logs directory not found: {LOGS_DIR}")
        return
    
    log_files = list(LOGS_DIR.glob('*.log'))
    
    if not log_files:
        print(f"📋 No log files found in {LOGS_DIR}")
        return
    
    print(f"📋 Available log files in {LOGS_DIR}:")
    print("-" * 80)
    for log_file in sorted(log_files):
        size = log_file.stat().st_size
        size_mb = size / (1024 * 1024)
        print(f"  • {log_file.name} ({size_mb:.2f} MB)")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='View Django application logs')
    parser.add_argument('file', nargs='?', default='django.log', help='Log file to view (default: django.log)')
    parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to show (default: 50)')
    parser.add_argument('-f', '--follow', action='store_true', help='Follow log file (like tail -f)')
    parser.add_argument('-l', '--list', action='store_true', help='List all available log files')
    
    args = parser.parse_args()
    
    if args.list:
        list_logs()
    else:
        view_logs(args.file, args.lines, args.follow)

if __name__ == '__main__':
    main()


