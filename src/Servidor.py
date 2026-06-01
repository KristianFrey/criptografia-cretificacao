import json
from datetime import datetime

import paho.mqtt.client as mqtt

from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_QOS,
    MQTT_CLIENT_ID_SERVIDOR,
    PROTOCOLO,
    VERSAO,
    topic_telemetria_wildcard,
    decodificar_mqtt,
    processar_pacote,
)
from BrokerMQTT import iniciar_broker_em_thread
from Seguranca import MockNGFW, MockReverseProxy, MockIDS, MockSIEM

ngfw = MockNGFW()
proxy = MockReverseProxy()
ids = MockIDS()
siem = MockSIEM(ngfw)
ngfw.add_to_whitelist("SEMAFORO_A1")


def _imprimir_resultado(pacote: dict, resultado: dict):
    cert_meta = resultado.get("cert_meta", {})
    print("\n============================")
    print("PACOTE STSP RECEBIDO (MQTT)")
    print("============================")
    print(f"Protocolo:   {pacote.get('protocolo')} v{pacote.get('versao')}")
    print(f"Device ID:   {resultado['device_id']}")
    print(f"Timestamp:   {pacote.get('timestamp')}")
    print(f"Dados:       {pacote.get('dados')}")
    print(f"Cifra:       {pacote.get('criptografia', 'aes')}")

    if cert_meta:
        print(f"Emissor CA:  {cert_meta.get('autoridade_emissora')}")

    print(f"Certificado: {resultado['cert_ok']}")
    print(f"NGFW:        {resultado['ngfw_ok']}")
    print(f"Proxy:       {resultado['proxy_ok']}")
    print(f"IDS NIDS:    {resultado['nids_ok']}")
    print(f"IDS HIDS:    {resultado['hids_ok']}")
    print(f"Hash OK:     {resultado['integridade_ok']}")
    print(f"Assinatura:  {resultado['assinatura_ok']}")
    print(f"Timestamp:   {resultado['timestamp_ok']}")

    if resultado["autentico"]:
        print("\n PACOTE AUTENTICO")
    else:
        print("\n PACOTE INVALIDO")


def _registrar_log(pacote: dict, resultado: dict):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(f"""
        PROTOCOLO: {PROTOCOLO} v{VERSAO}
        DEVICE: {resultado['device_id']}
        TIMESTAMP: {pacote.get('timestamp')}
        DADOS: {pacote.get('dados')}
        CERTIFICADO: {resultado['cert_ok']}
        NGFW: {resultado['ngfw_ok']}
        INTEGRIDADE: {resultado['integridade_ok']}
        ASSINATURA: {resultado['assinatura_ok']}
        TIMESTAMP_VALIDO: {resultado['timestamp_ok']}
        AUTENTICO: {resultado['autentico']}
        -----------------------------------
        """)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        topico = topic_telemetria_wildcard()
        client.subscribe(topico, qos=MQTT_QOS)
        print(f"Inscrito no tópico: {topico}\n")
    else:
        print(f"Falha na conexão MQTT: {reason_code}")


def on_message(client, userdata, msg):
    try:
        pacote = decodificar_mqtt(msg.payload.decode())
        resultado = processar_pacote(pacote, ngfw, proxy, ids, siem)
        _imprimir_resultado(pacote, resultado)
        _registrar_log(pacote, resultado)
    except Exception as e:
        print(f"\nERRO ao processar mensagem MQTT [{msg.topic}]: {e}")


def main():
    print("=" * 60)
    print("  SERVIDOR CENTRAL — SmartTraffic STSP sobre MQTT")
    print(f"  Protocolo: {PROTOCOLO} v{VERSAO}")
    print("  Defesa em Profundidade: NGFW | Proxy | IDS | SIEM")
    print("=" * 60)

    print("\nIniciando broker MQTT embarcado...")
    iniciar_broker_em_thread()
    print(f"Broker ativo em {MQTT_HOST}:{MQTT_PORT}")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID_SERVIDOR,
    )
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    print("Servidor MQTT conectado. Aguardando telemetria...\n")

    client.loop_forever()


if __name__ == "__main__":
    main()
