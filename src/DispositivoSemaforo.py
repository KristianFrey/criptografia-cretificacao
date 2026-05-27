import socket
import time
import random
import json

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

    client.send(mensagem.encode())

    print("Dados enviados:")
    print(mensagem)

    time.sleep(5)