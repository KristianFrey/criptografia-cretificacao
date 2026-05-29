from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64

# assinar mensagem
def assinar_mensagem(mensagem):

    with open("../chaves/private.pem", "rb") as f:
        private_key = RSA.import_key(f.read())

    hash_obj = SHA256.new(mensagem.encode())

    assinatura = pkcs1_15.new(private_key).sign(hash_obj)

    return base64.b64encode(assinatura).decode()


# verificar assinatura
def verificar_assinatura(mensagem, assinatura_recebida):

    with open("../chaves/public.pem", "rb") as f:
        public_key = RSA.import_key(f.read())

    hash_obj = SHA256.new(mensagem.encode())

    assinatura = base64.b64decode(assinatura_recebida)

    try:

        pkcs1_15.new(public_key).verify(hash_obj, assinatura)

        return True

    except:

        return False