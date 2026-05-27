import socket
import json

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

    data = conn.recv(1024)

    if not data:
        break

    pacote = json.loads(data.decode())

    dados = pacote["dados"]
    hash_recebido = pacote["hash"]

    mensagem = json.dumps(dados)

    hash_calculado = gerar_hash(mensagem)

    print("\n=== PACOTE RECEBIDO ===")
    print(dados)

    print("\nHash recebido:")
    print(hash_recebido)

    print("\nHash calculado:")
    print(hash_calculado)

    if hash_recebido == hash_calculado:
        print("\n✅ Integridade VERIFICADA")
    else:
        print("\n❌ Dados ALTERADOS")