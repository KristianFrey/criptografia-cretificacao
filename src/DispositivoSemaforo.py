import sys
import time
import random
import json

from datetime import datetime

import paho.mqtt.client as mqtt

from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_QOS,
    PROTOCOLO,
    VERSAO,
    topic_telemetria,
    montar_pacote,
    serializar_para_mqtt,
)
from Certificado import (
    caminhos_dispositivo,
    caminhos_emissao,
    carregar_certificado,
    extrair_metadados,
    verificar_certificado,
)

DEVICE_ID = "SEMAFORO_A1"
INTERVALO_SEG = 5


def _validar_certificado_local():
    caminho = caminhos_dispositivo(DEVICE_ID)["certificado"]
    if not caminho.exists():
        caminho = caminhos_emissao(DEVICE_ID)["certificado"]
    if not caminho.exists():
        print("Certificado não encontrado.")
        print("Execute na raiz do projeto:")
        print("  python GerarCertificado.py")
        print("  python DistribuirCertificado.py")
        sys.exit(1)

    cert = carregar_certificado(caminho)
    ok, msg = verificar_certificado(cert, DEVICE_ID)
    if not ok:
        print(f"Certificado inválido: {msg}")
        sys.exit(1)

    meta = extrair_metadados(cert)
    print(f"Dispositivo autenticado: {meta['device_id']}")
    print(f"Certificado válido até: {meta['valido_ate']}")
    return meta


def publicar_telemetria(client: mqtt.Client, cert_info: dict):
    dados = {
        "carros": random.randint(0, 50),
        "estado": random.choice(["VERDE", "AMARELO", "VERMELHO"]),
    }

    pacote = montar_pacote(DEVICE_ID, dados)
    payload = serializar_para_mqtt(pacote)
    topico = topic_telemetria(DEVICE_ID)

    client.publish(topico, payload, qos=MQTT_QOS)

    print("\n============================")
    print("PACOTE STSP PUBLICADO (MQTT)")
    print("============================")
    print(f"Protocolo:   {PROTOCOLO} v{VERSAO}")
    print(f"Tópico:      {topico}")
    print(f"Device ID:   {DEVICE_ID}")
    print(f"Timestamp:   {pacote['timestamp']}")
    print(f"Dados:       {dados}")
    print(f"Hash:        {pacote['hash']}")
    print(f"Certificado: {cert_info['chave_publica_fingerprint_sha256'][:32]}...")
    print(f"Assinatura:  {pacote['assinatura'][:50]}...")


def main():
    cert_info = _validar_certificado_local()

    print("=" * 60)
    print("  DISPOSITIVO IoT — Semáforo Inteligente (MQTT/STSP)")
    print("=" * 60)
    print(f"Broker: {MQTT_HOST}:{MQTT_PORT}")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"semaforo-{DEVICE_ID}",
    )
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            publicar_telemetria(client, cert_info)
            time.sleep(INTERVALO_SEG)
    except KeyboardInterrupt:
        print("\nEncerrando dispositivo...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
