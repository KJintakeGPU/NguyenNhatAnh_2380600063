from flask import Flask, request, jsonify
from cipher.caesar import CaesarCipher
from cipher.vigenere import VigenereCipher
app = Flask(__name__)
vigenere_Cipher = VigenereCipher()

caesar_cipher = CaesarCipher()
@app.route("/api/caesar/encrypt", methods=["POST"])
def caesar_encrypt():
    data = request.json
    plain_text = data['plain_text']
    key = int(data['key'])
    encrypt_text = caesar_cipher.encrypt(plain_text, key)
    return jsonify({"encrypted_message": encrypt_text})

@app.route("/api/caesar/decrypt", methods=["POST"])
def caesar_decrypt():
    data = request.json
    encrypt_text = data['encrypt_text']
    key = int(data['key'])
    decrypt_text = caesar_cipher.decrypt_text(encrypt_text, key)
    return jsonify({"decrypted_message": decrypt_text})

@app.route("/api/vigenere/encrypt", methods=["POST"])
def vigenere_encrypt():
    data = request.json
    plain_text = data['plain_text']
    key = data['key']
    encrypt_text = vigenere_Cipher.encrypt(plain_text, key)
    return jsonify({"encrypted_message": encrypt_text})

@app.route("/api/vigenere/decrypt", methods=["POST"])
def vigenere_decrypt():
    data = request.json
    encrypt_text = data['encrypt_text']
    key = data['key']
    decrypt_text = vigenere_Cipher.decrypt(encrypt_text, key)
    return jsonify({"decrypted_message": decrypt_text}) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)