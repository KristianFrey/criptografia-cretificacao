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
    topico_telemetria_curinga,
    topico_alertas_atms,
    topico_presenca_ambulancia_curinga,
    montar_alerta_atms,
    decodificar_mqtt,
    processar_pacote,
)
from BrokerMQTT import iniciar_broker_em_thread
from Seguranca import NGFW, ProxyReverso, IDS, SIEM
from config import (
    CAMINHO_LOG_JSON,
    CAMINHO_LOG_SERVIDOR,
    DISPOSITIVOS_PADRAO,
    garantir_estrutura_dados,
    mac_autorizado,
)

DISPOSITIVOS_AUTORIZADOS = tuple(DISPOSITIVOS_PADRAO.keys())

ngfw = NGFW()
proxy = ProxyReverso()
ids = IDS()
siem = SIEM(ngfw)
_mqtt_client = None

for device_id, cfg in DISPOSITIVOS_PADRAO.items():
    ngfw.adicionar_whitelist(device_id)
    if cfg.get("mac"):
        ngfw.adicionar_mac(cfg["mac"])


def _publicar_alerta_atms(device_id: str, fontes: list, mensagem: str):
    global _mqtt_client
    if _mqtt_client is None:
        return
    alerta = montar_alerta_atms(device_id, "CRITICA", mensagem, fontes)
    topico = topico_alertas_atms()
    _mqtt_client.publish(topico, json.dumps(alerta), qos=MQTT_QOS)
    print(f"\n  [ATMS] Alerta publicado em {topico}")
    print(f"  [ATMS] {mensagem}")


siem.ao_alertar_atms = _publicar_alerta_atms


def _imprimir_resultado(pacote: dict, resultado: dict):
    cert_meta = resultado.get("cert_meta", {})
    print("\n============================")
    print("PACOTE STSP RECEBIDO (MQTT)")
    print("============================")
    print(f"Protocolo:    {pacote.get('protocolo')} v{pacote.get('versao')}")
    print(f"Device ID:    {resultado['device_id']}")
    print(f"Timestamp:    {pacote.get('timestamp')}")
    print(f"Dados:        {pacote.get('dados')}")
    print(f"Cifra:        {pacote.get('criptografia', 'aes')}")
    if resultado.get("mac"):
        print(f"MAC:          {resultado['mac']}")

    if cert_meta:
        print(f"Emissor CA:   {cert_meta.get('autoridade_emissora')}")

    print(f"Certificado:  {resultado['cert_ok']}")
    print(f"MAC OK:       {resultado.get('mac_ok', False)}")
    print(f"NGFW:         {resultado['ngfw_ok']}")
    print(f"Proxy:        {resultado['proxy_ok']}")
    print(f"IDS NIDS:     {resultado['nids_ok']}")
    print(f"IDS HIDS:     {resultado['hids_ok']}")
    print(f"Hash OK:      {resultado['integridade_ok']}")
    print(f"Assinatura:   {resultado['assinatura_ok']}")
    print(f"Timestamp:    {resultado['timestamp_ok']}")

    classificacao = resultado.get("classificacao", "?")
    if resultado["autentico"]:
        print(f"\n PACOTE AUTENTICO ({classificacao})")
    else:
        print(f"\n PACOTE INVALIDO ({classificacao})")


def _registrar_log_json(pacote: dict, resultado: dict):
    garantir_estrutura_dados()
    entrada = {
        "timestamp_servidor": __import__("datetime").datetime.now().isoformat(),
        "tipo": "PACOTE",
        "protocolo": pacote.get("protocolo"),
        "versao": pacote.get("versao"),
        "device_id": resultado["device_id"],
        "timestamp_pacote": pacote.get("timestamp"),
        "dados": pacote.get("dados"),
        "criptografia": pacote.get("criptografia", "aes"),
        "mac": resultado.get("mac"),
        "cert_ok": resultado["cert_ok"],
        "mac_ok": resultado.get("mac_ok", False),
        "ngfw_ok": resultado["ngfw_ok"],
        "proxy_ok": resultado["proxy_ok"],
        "nids_ok": resultado["nids_ok"],
        "hids_ok": resultado["hids_ok"],
        "integridade_ok": resultado["integridade_ok"],
        "assinatura_ok": resultado["assinatura_ok"],
        "timestamp_ok": resultado["timestamp_ok"],
        "autentico": resultado["autentico"],
        "classificacao": resultado["classificacao"],
        "mensagens": resultado["mensagens"],
    }
    with open(CAMINHO_LOG_JSON, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def _registrar_log_ambulancia(topico: str, payload: dict):
    garantir_estrutura_dados()
    entrada = {
        "timestamp_servidor": __import__("datetime").datetime.now().isoformat(),
        "tipo": "PRESENCA_AMBULANCIA",
        "topico": topico,
        "dados": payload,
    }
    with open(CAMINHO_LOG_JSON, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    print(f"\n  [AMBULANCIA] Presenca detectada: {payload.get('device_id', '?')}")
    print(f"  [AMBULANCIA] Local: ({payload.get('latitude', '?')}, {payload.get('longitude', '?')})")
    print(f"  [AMBULANCIA] Sirene: {'ATIVA' if payload.get('sirene_ativa') else 'DESLIGADA'}")


def ao_conectar(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        topico_tel = topico_telemetria_curinga()
        topico_atms = topico_alertas_atms()
        topico_amb = topico_presenca_ambulancia_curinga()
        client.subscribe(topico_tel, qos=MQTT_QOS)
        client.subscribe(topico_atms, qos=MQTT_QOS)
        client.subscribe(topico_amb, qos=MQTT_QOS)
        print(f"Inscrito em: {topico_tel}")
        print(f"Inscrito em: {topico_atms} (monitoramento ATMS)")
        print(f"Inscrito em: {topico_amb} (monitoramento Ambulancia)\n")
    else:
        print(f"Falha na conexao MQTT: {reason_code}")


def ao_receber_mensagem(client, userdata, msg):
    if msg.topic == topico_alertas_atms():
        print(f"\n[ATMS] Alerta no dashboard: {msg.payload.decode()[:120]}...")
        return

    if "ambulancia" in msg.topic and "presenca" in msg.topic:
        try:
            payload = json.loads(msg.payload.decode())
            _registrar_log_ambulancia(msg.topic, payload)
        except Exception as e:
            print(f"\nERRO ao processar presenca de ambulancia [{msg.topic}]: {e}")
        return

    try:
        pacote = decodificar_mqtt(msg.payload.decode())
        resultado = processar_pacote(pacote, ngfw, proxy, ids, siem)
        _imprimir_resultado(pacote, resultado)
        _registrar_log_json(pacote, resultado)
    except Exception as e:
        print(f"\nERRO ao processar mensagem MQTT [{msg.topic}]: {e}")


def iniciar_servidor():
    global _mqtt_client

    print("=" * 60)
    print("  SERVIDOR CENTRAL (Fog/Cloud) — SmartTraffic STSP/MQTT")
    print(f"  Protocolo: {PROTOCOLO} v{VERSAO}")
    print("  Camadas T2: NGFW | Proxy | IDS (Snort/Wazuh sim.) | SIEM")
    print("  Camadas T3: AES | SHA-256 | RSA | Certificado X.509 | MAC")
    print("=" * 60)
    print(f"Dispositivos autorizados: {', '.join(DISPOSITIVOS_AUTORIZADOS)}")

    print("\nIniciando broker MQTT embarcado (DMZ simulada)...")
    iniciar_broker_em_thread()
    print(f"Broker: {MQTT_HOST}:{MQTT_PORT} (prod.: TLS porta {MQTT_PORT_TLS})")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID_SERVIDOR,
    )
    client.on_connect = ao_conectar
    client.on_message = ao_receber_mensagem

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    _mqtt_client = client
    print("Servidor conectado. Aguardando telemetria dos semaforos...\n")

    client.loop_forever()


def main():
    iniciar_servidor()


if __name__ == "__main__":
    main()
