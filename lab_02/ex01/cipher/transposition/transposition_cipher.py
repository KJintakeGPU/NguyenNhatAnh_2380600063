class TranspositionCipher:
    def __init__(self, key):
        self.key = key
        self.num_columns = len(str(key))

    def encrypt(self, plaintext):
        ciphertext = [''] * self.num_columns
        for col in range(self.num_columns):
            pointer = col
            while pointer < len(plaintext):
                ciphertext[col] += plaintext[pointer]
                pointer += self.num_columns
        return ''.join(ciphertext)

    def decrypt(self, ciphertext):
        num_rows = (len(ciphertext) + self.num_columns - 1) // self.num_columns
        num_shaded = (self.num_columns * num_rows) - len(ciphertext)
        
        plaintext = [''] * num_rows
        col = 0
        row = 0
        
        for symbol in ciphertext:
            plaintext[row] += symbol
            col += 1
            
            if col == self.num_columns or (col == self.num_columns - 1 and row >= num_rows - num_shaded):
                col = 0
                row += 1
        
        return ''.join(plaintext)