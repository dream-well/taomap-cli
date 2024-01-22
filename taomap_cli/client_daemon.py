import socket
import multiprocessing
import threading
import sys
import select
import json
import subprocess
import argparse

def convert_speed_unit(size, decimal_places=2):
    for unit in ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']:
        if size < 1000.0:
            break
        size /= 1000.0
    return f"{size:.{decimal_places}f} {unit}"

class SocketIO:
    def __init__(self, socket):
        self.socket = socket

    def write(self, text):
        # Send each line of output to the server immediately
        self.socket.sendall(text.encode())

    def flush(self):
        # This method might be called by print function, so it's necessary to have it.
        pass

def execute_code(code, s, completion_flag):
    # Use our custom SocketIO for stdout
    old_stdout = sys.stdout
    sys.stdout = SocketIO(s)

    # Execute the received code and capture any exceptions
    try:
        exec(code)
    except Exception as e:
        print(f"Error executing received code: {e}")
    finally:
        completion_flag.set()  # Set the flag to indicate completion

    # Restore original stdout
    sys.stdout = old_stdout

def receive_and_run_code(s, process, completion_flag):
    while True:
        # Non-blocking check for new data from server
        ready = select.select([s], [], [], 0.1)  # 0.1 seconds timeout
        if ready[0]:
            data = s.recv(1024).decode()
            if not data:
                continue

            if data[:8] == "!#SPD#!:" or data[:8] == "!#SPA#!:":
                try:
                    print('Speed testing...')
                    # Running the command and capturing the output
                    result = subprocess.run(['speedtest', '-f', 'json'], capture_output=True, text=True, check=True)

                    # The stdout attribute contains the output of the command
                    output = result.stdout

                    # Assuming the output is JSON formatted, parse it
                    speedtest_result = json.loads(output)
                    speed_text = f"{convert_speed_unit(speedtest_result['download']['bandwidth'])} / {convert_speed_unit(speedtest_result['upload']['bandwidth'])}"
                    s.sendall(str(f'!#SPD#!:{speed_text}').encode())
                    print(f'Speed test Result: {speed_text}')

                except subprocess.CalledProcessError as e:
                    # This will catch errors like command not found, or if the command returns a non-zero exit status
                    print(f"An error occurred: {e}")                    
                continue
    
            elif data[:8] == "!#STO#!:":
                if process and process.is_alive():
                    print('Stoping the executing process...')
                    process.terminate()
                    process.join()
                    print('Stopped.')
                    process = None  # Reset the process variable
                continue

            if process and process.is_alive():
                # A previous process is still running, handle according to your needs
                pass

            print("Running the following code...")
            print(data)
            completion_flag.clear()

            # Start a new process to execute the received code
            process = multiprocessing.Process(target=execute_code, args=(data,s, completion_flag))
            process.start()

        if process and not process.is_alive():
            # if completion_flag.is_set():
            s.sendall(str("!#END#!:").encode())  # Send "END" message to the server
            process = None  # Reset the process variable
    

def start_client(host='24.144.70.199', port=65432, user=''):
    process = None
    completion_flag = threading.Event()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))        
        s.sendall(user.encode())
        print(f'Connected to server({host}:{port}) with user id: {user}')

        receive_and_run_code(s, process, completion_flag)



def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Client for executing remote code.")
    
    # Add arguments to 'connect' command
    parser.add_argument("user", type=str, help="User identifier")
    parser.add_argument("--host", default='24.144.70.199', type=str, help="Host address")
    parser.add_argument("--port", default=65432, type=int, help="Port number")

    # Parse the arguments
    args = parser.parse_args()

    start_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()