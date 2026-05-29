import socket
import json

from Criptografia import descriptografar
from HashUtils import gerar_hash
from Assinatura import verificar_assinatura

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

    pacote_criptografado = data.decode()

    pacote_json = descriptografar(pacote_criptografado)

    pacote = json.loads(pacote_json)

    dados = pacote["dados"]

    hash_recebido = pacote["hash"]

    assinatura = pacote["assinatura"]

    mensagem = json.dumps(dados)

    # valida hash
    hash_calculado = gerar_hash(mensagem)

    integridade_ok = hash_recebido == hash_calculado

    # valida assinatura
    assinatura_ok = verificar_assinatura(
        mensagem,
        assinatura
    )

    print("\n=== DADOS RECEBIDOS ===")
    print(dados)

    print("\nIntegridade:", integridade_ok)

    print("Assinatura válida:", assinatura_ok)

    if integridade_ok and assinatura_ok:

        print("\n✅ PACOTE AUTÊNTICO E ÍNTEGRO")

    else:

        print("\n❌ PACOTE INVÁLIDO")