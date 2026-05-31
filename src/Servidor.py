import socket
import json
from datetime import datetime

from Criptografia import descriptografar
from HashUtils import gerar_hash
from Assinatura import verificar_assinatura
from Seguranca import MockNGFW, MockReverseProxy, MockIDS, MockSIEM

HOST = '127.0.0.1'
PORT = 5000

# --- INICIALIZACAO DA ARQUITETURA DE SEGURANCA ---
ngfw = MockNGFW()
proxy = MockReverseProxy()
ids = MockIDS()
siem = MockSIEM(ngfw)

ngfw.add_to_whitelist("SEMAFORO_A1")

print("=" * 60)
print("  ARQUITETURA DE SEGURANCA - Semaforos Inteligentes")
print("  Defesa em Profundidade: NGFW | Proxy | IDS | SIEM")
print("=" * 60)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("\nServidor iniciado...")
print("Aguardando conexao...\n")

conn, addr = server.accept()
print(f"Dispositivo conectado: {addr}\n")

while True:

    data = conn.recv(4096)

    if not data:
        break

    try:

        pacote_criptografado = data.decode()

        # --- SSL Termination (Proxy) ocorre primeiro para inspecao ---
        pacote_json = descriptografar(pacote_criptografado)
        pacote = json.loads(pacote_json)

        device_id = pacote.get("device_id", "unknown")

        # ============================================================
        # 1. NGFW - Firewall de Borda (Default Deny)
        # ============================================================
        ngfw_ok, ngfw_msg = ngfw.check_device(device_id)
        print(f"\n[1/4] NGFW: {ngfw_msg}")
        if not ngfw_ok:
            siem.ingest("NGFW", {"device_id": device_id, "event": "BLOCKED"})
            continue

        # ============================================================
        # 2. Reverse Proxy - Rate Limit / Anonimizacao
        # ============================================================
        if not proxy.check_rate_limit(device_id):
            print(f"[2/4] Proxy: RATE LIMIT EXCEDIDO para {device_id}")
            siem.ingest("Proxy", {"device_id": device_id, "event": "RATE_LIMIT_EXCEEDED"})
            ngfw.add_to_blacklist(device_id)
            continue

        pacote = proxy.anonymize(pacote)
        print(f"[2/4] Proxy: OK (rate ok, origem anonimizada via {proxy.proxy_ip})")

        # ============================================================
        # 3. IDS Híbrido - NIDS (rede) + HIDS (host)
        # ============================================================
        nids_ok = ids.analyze_nids(pacote)
        hids_ok = ids.analyze_hids(pacote)

        print(f"[3/4] IDS NIDS: {'OK' if nids_ok else 'ALERTA'}")
        print(f"[3/4] IDS HIDS: {'OK' if hids_ok else 'ALERTA'}")

        if not nids_ok or not hids_ok:
            siem.ingest("IDS", {"device_id": device_id, "nids_ok": nids_ok, "hids_ok": hids_ok})

        # ============================================================
        # 4. SIEM - Ingestao e Correlacao de Eventos
        # ============================================================
        siem.ingest("NGFW", {"device_id": device_id, "event": "ALLOWED"}, is_alert=False)
        siem.ingest("Proxy", {"device_id": device_id, "event": "PROXIED"}, is_alert=False)

        if not nids_ok or not hids_ok:
            print(f"[4/4] SIEM: Alertas ingeridos - correlacionando...")
        else:
            print(f"[4/4] SIEM: OK - sem anomalias")

        # ============================================================
        # VALIDACAO ORIGINAL (hash + assinatura + timestamp)
        # ============================================================
        timestamp = pacote["timestamp"]
        timestamp_pacote = datetime.fromisoformat(timestamp)
        agora = datetime.now()
        diferenca = (agora - timestamp_pacote).total_seconds()
        timestamp_ok = diferenca <= 30

        dados = pacote["dados"]
        hash_recebido = pacote["hash"]
        assinatura = pacote["assinatura"]
        mensagem = json.dumps(dados)

        hash_calculado = gerar_hash(mensagem)
        integridade_ok = (hash_recebido == hash_calculado)
        assinatura_ok = verificar_assinatura(mensagem, assinatura)

        print("\n============================")
        print("PACOTE RECEBIDO")
        print("============================")
        print(f"\nDevice ID: {device_id}")
        print(f"Timestamp: {timestamp}")
        print(f"Dados: {dados}")
        print(f"Integridade: {integridade_ok}")
        print(f"Assinatura valida: {assinatura_ok}")
        print(f"Timestamp valido: {timestamp_ok}")

        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(f"""
            DEVICE: {device_id}
            TIMESTAMP: {timestamp}
            DADOS: {dados}
            INTEGRIDADE: {integridade_ok}
            ASSINATURA: {assinatura_ok}
            TIMESTAMP_VALIDO: {timestamp_ok}
            -----------------------------------
            """)

        if integridade_ok and assinatura_ok and timestamp_ok:
            print("\n PACOTE AUTENTICO")
        else:
            print("\n PACOTE INVALIDO")

    except Exception as e:
        print("\nERRO:", e)