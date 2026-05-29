import socket
import time
import random
import json

from Criptografia import criptografar
from HashUtils import gerar_hash

HOST = '127.0.0.1'
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

while True:

    # Dados do semáforo
    dados = {
        "cruzamento": "A1",
        "carros": random.randint(0, 50),
        "estado": random.choice(["VERDE", "AMARELO", "VERMELHO"])
    }

    # transforma em JSON
    mensagem = json.dumps(dados)

    # gera hash SHA256
    hash_mensagem = gerar_hash(mensagem)

    # cria pacote completo
    pacote = {
        "dados": dados,
        "hash": hash_mensagem
    }

    # transforma pacote em JSON
    pacote_json = json.dumps(pacote)

    # criptografa tudo
    pacote_criptografado = criptografar(pacote_json)

    # envia
    client.send(pacote_criptografado.encode())

    print("\n=== DADOS ORIGINAIS ===")
    print(mensagem)

    print("\n=== HASH SHA-256 ===")
    print(hash_mensagem)

    print("\n=== PACOTE CRIPTOGRAFADO ===")
    print(pacote_criptografado)

    time.sleep(5)