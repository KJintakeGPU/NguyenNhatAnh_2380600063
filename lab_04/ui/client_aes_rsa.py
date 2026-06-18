import sys
import socket
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QThread, pyqtSignal

# Import giao diện đã được generate từ Qt Designer
from chat_form import Ui_MainWindow

# Import thư viện mã hóa của bạn
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

# --- CÁC HÀM MÃ HÓA NGUYÊN BẢN ---
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
                encrypted_message = self.client_socket.recv(1024)
                if not encrypted_message: break
                decrypted_message = decrypt_message(self.aes_key, encrypted_message)
                self.message_received.emit(f"Partner: {decrypted_message}")
            except:
                self.message_received.emit("Mất kết nối với server.")
                break

    def stop(self):
        self.running = False
        self.quit()

# --- MAIN CONTROLLER KHỞI TẠO TỪ GIAO DIỆN CHUẨN ---
class ChatApp_AES_RSA(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_thread = None
        self.aes_key = None

        # Kết nối sự kiện nút bấm vào hàm logic
        self.ui.btn_connect.clicked.connect(self.connect_to_server)
        self.ui.btn_send.clicked.connect(self.send_message)
        self.ui.txt_message.returnPressed.connect(self.send_message)

    def connect_to_server(self):
        try:
            self.client_socket.connect(('localhost', 23456)) # Chú ý port server của bạn
            self.ui.lbl_status.setText('Trạng thái: Đang trao đổi khóa RSA...')
            QtWidgets.QApplication.processEvents()

            # Handshake y hệt code gốc của bạn
            client_key = RSA.generate(2048)
            server_public_key = RSA.import_key(self.client_socket.recv(2048))
            self.client_socket.send(client_key.publickey().export_key(format='PEM'))
            
            encrypted_aes_key = self.client_socket.recv(2048)
            cipher_rsa = PKCS1_OAEP.new(client_key)
            self.aes_key = cipher_rsa.decrypt(encrypted_aes_key)

            # Khởi động Thread
            self.receive_thread = ReceiveThread(self.client_socket, self.aes_key)
            self.receive_thread.message_received.connect(self.update_chat)
            self.receive_thread.start()

            self.ui.lbl_status.setText('Trạng thái: Kết nối an toàn (AES-RSA)')
            self.ui.btn_connect.setEnabled(False)
            self.ui.btn_send.setEnabled(True)
            self.ui.txt_chat_history.append("<i>Đã nhận khóa AES. Bắt đầu chat!</i>")

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
    window = ChatApp_AES_RSA()
    window.show()
    sys.exit(app.exec_())