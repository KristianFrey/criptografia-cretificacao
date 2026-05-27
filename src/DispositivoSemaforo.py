import socket
import time
import random
import json

from HashUtils import gerar_hash

HOST = '127.0.0.1'
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

while True:

    dados = {
        "cruzamento": "A1",
        "carros": random.randint(0, 50),
        "estado": random.choice(["VERDE", "AMARELO", "VERMELHO"])
    }

    mensagem = json.dumps(dados)

    hash_mensagem = gerar_hash(mensagem)

    pacote = {
        "dados": dados,
        "hash": hash_mensagem
    }

    pacote_json = json.dumps(pacote)

    client.send(pacote_json.encode())

    print("\n=== PACOTE ENVIADO ===")
    print(pacote_json)

    time.sleep(5)