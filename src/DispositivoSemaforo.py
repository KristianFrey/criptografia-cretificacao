import socket
import time
import random
import json

from datetime import datetime

from Criptografia import criptografar
from HashUtils import gerar_hash
from Assinatura import assinar_mensagem

HOST = '127.0.0.1'
PORT = 5000

DEVICE_ID = "SEMAFORO_A1"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

while True:

    # dados do semáforo
    dados = {
        "carros": random.randint(0, 50),
        "estado": random.choice([
            "VERDE",
            "AMARELO",
            "VERMELHO"
        ])
    }

    # timestamp
    timestamp = datetime.now().isoformat()

    # mensagem original
    mensagem = json.dumps(dados)

    # hash SHA-256
    hash_mensagem = gerar_hash(mensagem)

    # assinatura digital RSA
    assinatura = assinar_mensagem(mensagem)

    # pacote final
    pacote = {
        "device_id": DEVICE_ID,
        "timestamp": timestamp,
        "dados": dados,
        "hash": hash_mensagem,
        "assinatura": assinatura
    }

    # transforma em json
    pacote_json = json.dumps(pacote)

    # criptografa
    pacote_criptografado = criptografar(pacote_json)

    # envia
    client.send(pacote_criptografado.encode())

    print("\n============================")
    print("PACOTE ENVIADO")
    print("============================")

    print("\nDevice ID:")
    print(DEVICE_ID)

    print("\nTimestamp:")
    print(timestamp)

    print("\nDados:")
    print(dados)

    print("\nHash:")
    print(hash_mensagem)

    print("\nAssinatura:")
    print(assinatura[:50], "...")

    time.sleep(5)