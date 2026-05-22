class VigenereCipher:
    def __init__(self, key):
        self

    def encrypt(self, plain_text, key):
        encrypt_text = ""
        key_index = 0
        for char in plain_text:
            if char.isalpha():
                shift = ord(key[key_index % len(key)].upper()) - ord('A')
                if char.isupper():
                    encrypt_text += chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
                else
                    encrypt_text += chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
                key_index += 1
            else:
                encrypt_text += char
        return encrypt_text
    
    def decrypt(self, encrypt_text, key):
        decrypt_text = ""
        key_index = 0
        for char in encrypt_text:
            if char.isalpha():
                shift = ord(key[key_index % len(key)].upper()) - ord('A')
                if char.isupper():
                    decrypt_text += chr((ord(char) - ord('A') - shift) % 26 + ord('A'))
                else:
                    decrypt_text += chr((ord(char) - ord('a') - shift) % 26 + ord('a'))
                key_index += 1
            else:
                decrypt_text += char
        return decrypt_text
                    