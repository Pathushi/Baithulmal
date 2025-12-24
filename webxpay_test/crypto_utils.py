import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


def encrypt_payment(unique_id: str, amount: str, key_file="public_key.pem") -> str:
    """
    Exactly matches PHP:
        openssl_public_encrypt($plaintext, $encrypt, $publickey);
        base64_encode($encrypt);
    """

    plaintext = f"{unique_id}|{amount}"

    # Load public key
    with open(key_file, "rb") as f:
        public_key = RSA.import_key(f.read())

    cipher = PKCS1_v1_5.new(public_key)

    encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode("ascii")

    print("PLAINTEXT:", plaintext)
    print("PAYMENT (PY):", encrypted_b64)

    return encrypted_b64
