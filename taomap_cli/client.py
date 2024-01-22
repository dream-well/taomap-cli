import argparse
import subprocess
import os
import signal

# Constants
DAEMON_SCRIPT = 'taomap_cli/client_daemon.py'  # Path to your daemon script
LOG_FILE = 'daemon.log'
PID_FILE = 'daemon.pid'

def write_pid_file(pid):
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))

def read_pid_file():
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return None

def remove_pid_file():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def start_daemon(host, port, user):
    if read_pid_file():
        print("Daemon is already running.")
        return
    
    command = ['python', DAEMON_SCRIPT, user, '--host', host, '--port', str(port)]
    with open(LOG_FILE, 'a') as log_file:
        process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
    write_pid_file(process.pid)
    print(f"Daemon started with PID {process.pid}")

def stop_daemon():
    pid = read_pid_file()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            remove_pid_file()
            print("Daemon stopped.")
        except OSError:
            print("Error stopping daemon.")
            remove_pid_file()
    else:
        print("Daemon is not running.")

def restart_daemon():
    stop_daemon()
    start_daemon()

def check_status():
    pid = read_pid_file()
    if pid and os.path.exists(f'/proc/{pid}'):
        print(f"Daemon is running with PID {pid}.")
    else:
        print("Daemon is not running.")

def show_logs():
    with open(LOG_FILE, 'r') as log_file:
        print(log_file.read())

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Client for executing remote code.")

    subparsers = parser.add_subparsers(dest='command')
    connect_parser = subparsers.add_parser('connect', help='Connect to the server and start the daemon process')
    subparsers.add_parser('stop', help='Stop the daemon')
    subparsers.add_parser('restart', help='Restart the daemon')
    subparsers.add_parser('status', help='Show the status of the daemon')
    subparsers.add_parser('logs', help='Show the logs of the daemon')

    # Add arguments to 'connect' command
    connect_parser.add_argument("user", type=str, help="User identifier")
    connect_parser.add_argument("--host", default='24.144.70.199', type=str, help="Host address")
    connect_parser.add_argument("--port", default=65432, type=int, help="Port number")

    # Parse the arguments
    args = parser.parse_args()

    # Check if the 'connect' command is used
    if args.command == 'connect':
        start_daemon(args.host, args.port, args.user)
    elif args.command == 'stop':
        stop_daemon()
    elif args.command == 'restart':
        restart_daemon()
    elif args.command == 'status':
        check_status()
    elif args.command == 'logs':
        show_logs()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()