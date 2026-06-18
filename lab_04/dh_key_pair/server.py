import socket
import threading
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_dh_parameters():
    parameters = dh.generate_parameters(generator=2, key_size=2048)
    return parameters

def generate_server_key_pair(parameters):
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key()
    return private_key, public_key
# -------------------------------

dh_parameters = generate_dh_parameters()
server_private_key, server_public_key = generate_server_key_pair(dh_parameters)

server_public_pem = server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))
server_socket.listen(5)

clients = []

def encrypt_message(key, message):
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(message.encode(), AES.block_size))
    return cipher.iv + ciphertext

def decrypt_message(key, encrypted_message):
    iv = encrypted_message[:AES.block_size]
    ciphertext = encrypted_message[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_message = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return decrypted_message.decode()

def handle_client(client_socket, client_address):
    print(f"Connected with {client_address}")

    try:
        client_socket.send(server_public_pem)

        client_pub_bytes = client_socket.recv(2048)
        client_public_key = serialization.load_pem_public_key(
            client_pub_bytes, backend=default_backend()
        )

        shared_secret = server_private_key.exchange(client_public_key)
        aes_key = hashlib.md5(shared_secret).digest()

        clients.append((client_socket, aes_key))

        while True:
            encrypted_message = client_socket.recv(2048)
            if not encrypted_message:
                break
            
            decrypted_message = decrypt_message(aes_key, encrypted_message)
            print(f"Received from {client_address}: {decrypted_message}")

            # Chuyển tiếp cho các client khác
            for client, key in clients:
                if client != client_socket:
                    encrypted = encrypt_message(key, decrypted_message)
                    client.send(encrypted)

            if decrypted_message.lower() == "exit":
                break

    except Exception as e:
        print(f"Lỗi với {client_address}: {e}")
    finally:
        # Dọn dẹp khi Client ngắt kết nối
        clients[:] = [(c, k) for c, k in clients if c != client_socket]
        client_socket.close()
        print(f"Connection with {client_address} closed")

while True:
    client_socket, client_address = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()