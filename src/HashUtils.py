import hashlib

def gerar_hash(mensagem):
    
    hash_obj = hashlib.sha256(mensagem.encode())

    return hash_obj.hexdigest()