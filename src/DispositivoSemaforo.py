import sys
import time
import threading
import paho.mqtt.client as mqtt

from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_QOS,
    PROTOCOLO,
    VERSAO,
    topico_telemetria,
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
from Telemetria import GeradorTelemetria

INTERVALO_SEG = 5
DISPOSITIVOS_PADRAO = ("SEMAFORO_A1", "SEMAFORO_B2")


def _validar_certificado_local(device_id: str):
    caminho = caminhos_dispositivo(device_id)["certificado"]
    if not caminho.exists():
        caminho = caminhos_emissao(device_id)["certificado"]
    if not caminho.exists():
        print(f"Certificado nao encontrado para {device_id}.")
        print("Execute na raiz do projeto:")
        print("  python scripts/provisionar_rede.py")
        sys.exit(1)

    cert = carregar_certificado(caminho)
    ok, msg = verificar_certificado(cert, device_id)
    if not ok:
        print(f"Certificado invalido: {msg}")
        sys.exit(1)

    meta = extrair_metadados(cert)
    print(f"Dispositivo autenticado: {meta['device_id']}  MAC: {meta.get('mac', 'N/D')}")
    print(f"Certificado valido ate: {meta['valido_ate']}")
    return meta


def publicar_telemetria(client: mqtt.Client, device_id: str, gerador: GeradorTelemetria, cert_info: dict):
    dados = gerador.proximo_pacote()
    pacote = montar_pacote(device_id, dados)
    payload = serializar_para_mqtt(pacote)
    topico = topico_telemetria(device_id)
    client.publish(topico, payload, qos=MQTT_QOS)

    print(f"\n[SEMAFORO {device_id}] Estado={dados['estado']} Carros={dados['carros']} "
          f"Fila={dados['fila_metros']}m Modo={dados['modo']}")


def criar_cliente_mqtt(device_id: str) -> mqtt.Client:
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"semaforo-{device_id}",
    )
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    return client


def executar_dispositivo(device_id: str, gerador: GeradorTelemetria = None,
                         cert_info: dict = None, client: mqtt.Client = None,
                         evento_parar: threading.Event = None):
    if cert_info is None:
        cert_info = _validar_certificado_local(device_id)
    if gerador is None:
        gerador = GeradorTelemetria(device_id)
    cliente_proprio = client is None
    if cliente_proprio:
        client = criar_cliente_mqtt(device_id)
        client.loop_start()
        print("=" * 60)
        print(f"  DISPOSITIVO IoT — {device_id} (Edge / Semaforo Inteligente)")
        print("=" * 60)
        print(f"Broker: {MQTT_HOST}:{MQTT_PORT}")

    try:
        while True:
            if evento_parar and evento_parar.is_set():
                break
            publicar_telemetria(client, device_id, gerador, cert_info)
            time.sleep(INTERVALO_SEG)
    except KeyboardInterrupt:
        print("\nEncerrando dispositivo...")
    finally:
        if cliente_proprio:
            client.loop_stop()
            client.disconnect()


def main():
    device_id = sys.argv[1] if len(sys.argv) > 1 else "SEMAFORO_A1"
    if device_id not in DISPOSITIVOS_PADRAO:
        print(f"Aviso: {device_id} nao esta na lista padrao {DISPOSITIVOS_PADRAO}")
    executar_dispositivo(device_id)


if __name__ == "__main__":
    main()
