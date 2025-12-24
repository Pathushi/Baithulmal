import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from django.conf import settings

def encrypt_payment(transaction_id: str, amount: str):
    # Create the plaintext string
    plaintext = f"{transaction_id}|{amount}"
    
    # DEBUG: Print what we are about to encrypt
    print(f"--- DEBUG: ENCRYPTION ---")
    print(f"PLAINTEXT: {plaintext}")
    
    # Locate the key file relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_file = os.path.join(current_dir, "crypto", "public_key.pem")

    if not os.path.exists(key_file):
        print(f"ERROR: Key file not found at {key_file}")
        raise FileNotFoundError(f"Public key not found at {key_file}")

    with open(key_file, "rb") as f:
        public_key = RSA.import_key(f.read())

    cipher = PKCS1_v1_5.new(public_key)
    encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode("ascii")

    return encrypted_b64