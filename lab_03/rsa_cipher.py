import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui.rsa import Ui_MainWindow
import requests

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Các biến cờ theo dõi trạng thái thay đổi Key
        self.key_changed_for_decrypt = False
        self.key_changed_for_verify = False
        
        # Kết nối Event từ file XML
        self.ui.btn_generate.clicked.connect(self.call_api_gen_keys)
        self.ui.btn_encrypt.clicked.connect(self.call_api_encrypt)
        self.ui.btn_decrypt.clicked.connect(self.call_api_decrypt)
        self.ui.btn_sign.clicked.connect(self.call_api_sign)
        self.ui.btn_verify.clicked.connect(self.call_api_verify)

    def call_api_gen_keys(self):
        url = "http://127.0.0.1:5000/api/rsa/generate_keys"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Bật cờ cảnh báo: Key đã đổi, dữ liệu cũ (nếu có) sẽ không còn khớp
                self.key_changed_for_decrypt = True
                self.key_changed_for_verify = True
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText(data["message"])
                msg.setInformativeText("Lưu ý: Cặp khóa mới đã được tạo. Các chuỗi Ciphertext hoặc Signature cũ trên giao diện sẽ không thể giải mã/xác thực thành công nữa!")
                msg.exec_()
            else:
                print("Error while calling API")
        except requests.exceptions.RequestException as e:
            print("Error: %s" % e.message)

    def call_api_encrypt(self):
        url = "http://127.0.0.1:5000/api/rsa/encrypt"
        payload = {
            "message": self.ui.txt_plaintext.toPlainText(),
            "key_type": "public"
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.ui.txt_ciphertext.setText(data["encrypted_message"])
                
                # Đã tạo Ciphertext mới theo Key mới -> tắt cờ cảnh báo Decrypt
                self.key_changed_for_decrypt = False
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Encrypted Successfully")
                msg.exec_()
            else:
                print("Error while calling API")
        except requests.exceptions.RequestException as e:
            print("Error: %s" % e.message)

    def call_api_decrypt(self):
        # Kiểm tra nếu chưa cập nhật Ciphertext sau khi đổi Key
        if self.key_changed_for_decrypt:
            msg_warn = QMessageBox()
            msg_warn.setIcon(QMessageBox.Warning)
            msg_warn.setWindowTitle("Cảnh báo")
            msg_warn.setText("Bạn vừa tạo Key mới!")
            msg_warn.setInformativeText("Chuỗi Cipher text hiện tại có thể là dữ liệu cũ của Key trước đó. Bạn có chắc chắn muốn tiếp tục giải mã?")
            msg_warn.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_warn.setDefaultButton(QMessageBox.No)
            
            if msg_warn.exec_() == QMessageBox.No:
                return # Dừng hàm, không gọi API nữa

        url = "http://127.0.0.1:5000/api/rsa/decrypt"
        payload = {
            "ciphertext": self.ui.txt_ciphertext.toPlainText(),
            "key_type": "private"
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.ui.txt_plaintext.setText(data["decrypted_message"])
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Decrypted Successfully")
                msg.exec_()
            else:
                # Thông báo khi giải mã thất bại (thường do lệch Key)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Decrypted Fail")
                msg.setInformativeText("Không thể giải mã dữ liệu. Vui lòng kiểm tra lại chuỗi Cipher text hoặc cặp Key.")
                msg.exec_()
        except requests.exceptions.RequestException as e:
            print("Error: %s" % e.message)

    def call_api_sign(self):
        url = "http://127.0.0.1:5000/api/rsa/sign"
        payload = {
            "message": self.ui.txt_info.toPlainText(),
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.ui.txt_signature.setText(data["signature"])
                
                # Đã ký mới theo Key mới -> tắt cờ cảnh báo Verify
                self.key_changed_for_verify = False
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Signed Successfully")
                msg.exec_()
            else:
                print("Error while calling API")
        except requests.exceptions.RequestException as e:
            print("Error: %s" % e.message)

    def call_api_verify(self):
        # Kiểm tra nếu chưa cập nhật Signature sau khi đổi Key
        if self.key_changed_for_verify:
            msg_warn = QMessageBox()
            msg_warn.setIcon(QMessageBox.Warning)
            msg_warn.setWindowTitle("Cảnh báo")
            msg_warn.setText("Bạn vừa tạo Key mới!")
            msg_warn.setInformativeText("Chuỗi Signature hiện tại có thể được tạo từ Key cũ. Bạn có muốn tiếp tục xác thực?")
            msg_warn.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_warn.setDefaultButton(QMessageBox.No)
            
            if msg_warn.exec_() == QMessageBox.No:
                return # Dừng hàm, không gọi API nữa

        url = "http://127.0.0.1:5000/api/rsa/verify"
        payload = {
            "message": self.ui.txt_info.toPlainText(),
            "signature": self.ui.txt_signature.toPlainText()
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if (data["is_verified"]):
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Verified Successfully")
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Critical) # Đổi thành Critical (X đỏ) cho rõ ràng lỗi
                    msg.setText("Verified Fail")
                    msg.setInformativeText("Chữ ký không hợp lệ với nội dung hoặc Key hiện tại.")
                    msg.exec_()
            else:
                print("Error while calling API")
        except requests.exceptions.RequestException as e:
            print("Error: %s" % e.message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())