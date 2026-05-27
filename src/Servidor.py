import socket

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

    print("Mensagem recebida:")
    print(data.decode())