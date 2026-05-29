import socket
import time
import random
import json

from Criptografia import criptografar
from HashUtils import gerar_hash
from Assinatura import assinar_mensagem

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

    # hash
    hash_mensagem = gerar_hash(mensagem)

    # assinatura digital
    assinatura = assinar_mensagem(mensagem)

    pacote = {
        "dados": dados,
        "hash": hash_mensagem,
        "assinatura": assinatura
    }

    pacote_json = json.dumps(pacote)

    pacote_criptografado = criptografar(pacote_json)

    client.send(pacote_criptografado.encode())

    print("\n=== DADOS ===")
    print(mensagem)

    print("\n=== HASH ===")
    print(hash_mensagem)

    print("\n=== ASSINATURA ===")
    print(assinatura[:50], "...")

    time.sleep(5)