import socket
import json

from Criptografia import descriptografar
from HashUtils import gerar_hash
from Assinatura import verificar_assinatura
from datetime import datetime

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

    try:

        # pacote criptografado
        pacote_criptografado = data.decode()

        # descriptografa
        pacote_json = descriptografar(
            pacote_criptografado
        )

        # converte json
        pacote = json.loads(pacote_json)

        device_id = pacote["device_id"]

        timestamp = pacote["timestamp"]

        # converte timestamp recebido
        timestamp_pacote = datetime.fromisoformat(
            timestamp
        )

        # horário atual
        agora = datetime.now()

        # diferença em segundos
        diferenca = (
            agora - timestamp_pacote
        ).total_seconds()

        # valida expiração
        timestamp_ok = diferenca <= 30

        dados = pacote["dados"]

        hash_recebido = pacote["hash"]

        assinatura = pacote["assinatura"]

        mensagem = json.dumps(dados)

        # valida hash
        hash_calculado = gerar_hash(mensagem)

        integridade_ok = (
            hash_recebido == hash_calculado
        )

        # valida assinatura
        assinatura_ok = verificar_assinatura(
            mensagem,
            assinatura
        )

        print("\n============================")
        print("PACOTE RECEBIDO")
        print("============================")

        print("\nDevice ID:")
        print(device_id)

        print("\nTimestamp:")
        print(timestamp)

        print("\nDados:")
        print(dados)

        print("\nIntegridade:")
        print(integridade_ok)

        print("\nAssinatura válida:")
        print(assinatura_ok)
        
        print("\nTimestamp válido:")
        print(timestamp_ok)

        # salva log
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(
                f"""
            DEVICE: {device_id}
            TIMESTAMP: {timestamp}
            DADOS: {dados}
            INTEGRIDADE: {integridade_ok}
            ASSINATURA: {assinatura_ok}
            TIMESTAMP_VALIDO: {timestamp_ok}
            -----------------------------------
            """
            )
                        

        # validação final
        if integridade_ok and assinatura_ok and timestamp_ok:

            print("\n✅ PACOTE AUTÊNTICO")

        else:

            print("\n❌ PACOTE INVÁLIDO")

    except Exception as e:

        print("\nERRO:")
        print(e)