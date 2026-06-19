import sys
import socket
import hashlib
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QThread, pyqtSignal

# Gọi giao diện UI
from chat_form_dh import Ui_MainWindow

# --- THƯ VIỆN AES TỪ LAB TRƯỚC ---
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# --- THƯ VIỆN DIFFIE-HELLMAN CỦA BẠN ---
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# --- CÁC HÀM MÃ HÓA AES ---
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

# --- THREAD NHẬN TIN NHẮN ---
class ReceiveThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, client_socket, aes_key):
        super().__init__()
        self.client_socket = client_socket
        self.aes_key = aes_key
        self.running = True

    def run(self):
        while self.running:
            try:
                encrypted_message = self.client_socket.recv(2048)
                if not encrypted_message: break
                decrypted_message = decrypt_message(self.aes_key, encrypted_message)
                self.message_received.emit(f"Partner: {decrypted_message}")
            except Exception as e:
                self.message_received.emit("Mất kết nối với server.")
                break

    def stop(self):
        self.running = False
        self.quit()

# --- MAIN CONTROLLER CHO DH-AES ---
class ChatApp_DH_AES(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_thread = None
        self.aes_key = None

        # Gắn sự kiện nút bấm
        self.ui.btn_connect.clicked.connect(self.connect_to_server)
        self.ui.btn_send.clicked.connect(self.send_message)
        self.ui.txt_message.returnPressed.connect(self.send_message)

    def connect_to_server(self):
        try:
            # LƯU Ý: Sửa port này cho khớp với Server của bài Diffie-Hellman
            self.client_socket.connect(('localhost', 12345)) 
            self.ui.lbl_status.setText('Đang bắt tay Diffie-Hellman...')
            QtWidgets.QApplication.processEvents()

            # 1. Nhận Server Public Key (PEM) từ Server
            server_pub_key_bytes = self.client_socket.recv(2048)
            server_public_key = serialization.load_pem_public_key(
                server_pub_key_bytes, backend=default_backend()
            )

            # 2. Rút xuất tham số (p, g) từ Public Key của Server
            parameters = server_public_key.parameters()

            # 3. Sinh khóa Private & Public của Client dựa trên tham số đó
            client_private_key = parameters.generate_private_key()
            client_public_key = client_private_key.public_key()

            # 4. Gửi Client Public Key (PEM) lại cho Server
            client_pub_bytes = client_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            self.client_socket.send(client_pub_bytes)

            # 5. Cùng tính toán Shared Secret
            shared_secret = client_private_key.exchange(server_public_key)

            # 6. Băm Shared Secret ra thành khóa AES 16-byte (Giống ý tưởng Lab 4)
            self.aes_key = hashlib.md5(shared_secret).digest()

            # Khởi động luồng nhận tin nhắn
            self.receive_thread = ReceiveThread(self.client_socket, self.aes_key)
            self.receive_thread.message_received.connect(self.update_chat)
            self.receive_thread.start()

            self.ui.lbl_status.setText('Trạng thái: Kết nối an toàn (DH-AES)')
            self.ui.btn_connect.setEnabled(False)
            self.ui.btn_send.setEnabled(True)
            self.ui.txt_chat_history.append("<i>Đã thống nhất khóa bằng Diffie-Hellman. Bắt đầu chat!</i>")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Kết nối thất bại: {str(e)}")

    def send_message(self):
        message = self.ui.txt_message.text()
        if message and self.aes_key:
            self.update_chat(f"You: {message}")
            try:
                encrypted = encrypt_message(self.aes_key, message)
                self.client_socket.send(encrypted)
                self.ui.txt_message.clear()
            except Exception as e:
                self.update_chat(f"Lỗi gửi: {e}")

    def update_chat(self, msg):
        self.ui.txt_chat_history.append(msg)

    def closeEvent(self, event):
        if self.receive_thread: self.receive_thread.stop()
        self.client_socket.close()
        event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ChatApp_DH_AES()
    window.show()
    sys.exit(app.exec_())