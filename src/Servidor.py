import json

import paho.mqtt.client as mqtt

from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_PORT_TLS,
    MQTT_QOS,
    MQTT_CLIENT_ID_SERVIDOR,
    PROTOCOLO,
    VERSAO,
    topic_telemetria_wildcard,
    topic_atms_alertas,
    montar_alerta_atms,
    decodificar_mqtt,
    processar_pacote,
)
from BrokerMQTT import iniciar_broker_em_thread
from Seguranca import MockNGFW, MockReverseProxy, MockIDS, MockSIEM
from config import CAMINHO_LOG_SERVIDOR, garantir_estrutura_dados

DISPOSITIVOS_AUTORIZADOS = ("SEMAFORO_A1", "SEMAFORO_B2")

ngfw = MockNGFW()
proxy = MockReverseProxy()
ids = MockIDS()
siem = MockSIEM(ngfw)
_mqtt_client = None

for device_id in DISPOSITIVOS_AUTORIZADOS:
    ngfw.add_to_whitelist(device_id)


def _publicar_alerta_atms(device_id: str, fontes: list, mensagem: str):
    global _mqtt_client
    if _mqtt_client is None:
        return
    alerta = montar_alerta_atms(device_id, "CRITICA", mensagem, fontes)
    topico = topic_atms_alertas()
    _mqtt_client.publish(topico, json.dumps(alerta), qos=MQTT_QOS)
    print(f"\n  [ATMS] Alerta publicado em {topico}")
    print(f"  [ATMS] {mensagem}")


siem.on_atms_alert = _publicar_alerta_atms


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
    garantir_estrutura_dados()
    with open(CAMINHO_LOG_SERVIDOR, "a", encoding="utf-8") as f:
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
        client.subscribe(topic_atms_alertas(), qos=MQTT_QOS)
        print(f"Inscrito em: {topico}")
        print(f"Inscrito em: {topic_atms_alertas()} (monitoramento ATMS)\n")
    else:
        print(f"Falha na conexão MQTT: {reason_code}")


def on_message(client, userdata, msg):
    if msg.topic == topic_atms_alertas():
        print(f"\n[ATMS] Alerta no dashboard: {msg.payload.decode()[:120]}...")
        return

    try:
        pacote = decodificar_mqtt(msg.payload.decode())
        resultado = processar_pacote(pacote, ngfw, proxy, ids, siem)
        _imprimir_resultado(pacote, resultado)
        _registrar_log(pacote, resultado)
    except Exception as e:
        print(f"\nERRO ao processar mensagem MQTT [{msg.topic}]: {e}")


def main():
    global _mqtt_client

    print("=" * 60)
    print("  SERVIDOR CENTRAL (Fog/Cloud) — SmartTraffic STSP/MQTT")
    print(f"  Protocolo: {PROTOCOLO} v{VERSAO}")
    print("  Camadas T2: NGFW | Proxy | IDS (Snort/Wazuh sim.) | SIEM")
    print("  Camadas T3: AES | SHA-256 | RSA | Certificado X.509")
    print("=" * 60)
    print(f"Dispositivos autorizados: {', '.join(DISPOSITIVOS_AUTORIZADOS)}")

    print("\nIniciando broker MQTT embarcado (DMZ simulada)...")
    iniciar_broker_em_thread()
    print(f"Broker: {MQTT_HOST}:{MQTT_PORT} (prod.: TLS porta {MQTT_PORT_TLS})")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID_SERVIDOR,
    )
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    _mqtt_client = client
    print("Servidor conectado. Aguardando telemetria dos semáforos...\n")

    client.loop_forever()


if __name__ == "__main__":
    main()
