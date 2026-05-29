from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# chave AES de 16 bytes
CHAVE = b'1234567890123456'


def criptografar(mensagem):

    cipher = AES.new(CHAVE, AES.MODE_EAX)

    nonce = cipher.nonce

    ciphertext, tag = cipher.encrypt_and_digest(mensagem.encode())

    pacote = nonce + ciphertext

    return base64.b64encode(pacote).decode()


def descriptografar(mensagem_criptografada):

    dados = base64.b64decode(mensagem_criptografada)

    nonce = dados[:16]

    ciphertext = dados[16:]

    cipher = AES.new(CHAVE, AES.MODE_EAX, nonce=nonce)

    mensagem = cipher.decrypt(ciphertext)

    return mensagem.decode()