from Crypto.PublicKey import RSA

# gera chave RSA 2048 bits
key = RSA.generate(2048)

# chave privada
private_key = key.export_key()

# chave pública
public_key = key.publickey().export_key()

# salva privada
with open("chaves/private.pem", "wb") as f:
    f.write(private_key)

# salva pública
with open("chaves/public.pem", "wb") as f:
    f.write(public_key)

print("Chaves RSA geradas com sucesso!")