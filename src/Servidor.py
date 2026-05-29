import socket
import json

from Criptografia import descriptografar
from HashUtils import gerar_hash

HOST = '127.0.0.1'
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
server.listen()

print("Servidor iniciado...")
print("Aguardando conexão...")

conn, addr = server.accept()

print(f"Dispositivo conectado: {addr}")

while True:

    data = conn.recv(4096)

    if not data:
        break

    # recebe criptografado
    pacote_criptografado = data.decode()

    print("\n=== PACOTE CRIPTOGRAFADO ===")
    print(pacote_criptografado)

    # descriptografa
    pacote_json = descriptografar(pacote_criptografado)

    print("\n=== PACOTE DESCRIPTOGRAFADO ===")
    print(pacote_json)

    # converte JSON
    pacote = json.loads(pacote_json)

    dados = pacote["dados"]

    hash_recebido = pacote["hash"]

    # recalcula hash
    mensagem = json.dumps(dados)

    hash_calculado = gerar_hash(mensagem)

    print("\n=== HASH RECEBIDO ===")
    print(hash_recebido)

    print("\n=== HASH CALCULADO ===")
    print(hash_calculado)

    # valida integridade
    if hash_recebido == hash_calculado:

        print("\n✅ INTEGRIDADE VERIFICADA")

        print("\n=== DADOS FINAIS ===")
        print(dados)

    else:

        print("\n❌ DADOS ALTERADOS")