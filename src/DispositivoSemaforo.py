import sys

import time



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

from Telemetria import GeradorTelemetria



INTERVALO_SEG = 5

DISPOSITIVOS_PADRAO = ("SEMAFORO_A1", "SEMAFORO_B2")





def _validar_certificado_local(device_id: str):

    caminho = caminhos_dispositivo(device_id)["certificado"]

    if not caminho.exists():

        caminho = caminhos_emissao(device_id)["certificado"]

    if not caminho.exists():

        print(f"Certificado não encontrado para {device_id}.")

        print("Execute na raiz do projeto:")

        print("  python scripts/provisionar_rede.py")

        sys.exit(1)



    cert = carregar_certificado(caminho)

    ok, msg = verificar_certificado(cert, device_id)

    if not ok:

        print(f"Certificado inválido: {msg}")

        sys.exit(1)



    meta = extrair_metadados(cert)

    print(f"Dispositivo autenticado: {meta['device_id']}")

    print(f"Certificado válido até: {meta['valido_ate']}")

    return meta





def publicar_telemetria(client: mqtt.Client, device_id: str, gerador: GeradorTelemetria, cert_info: dict):

    dados = gerador.proximo_pacote()

    pacote = montar_pacote(device_id, dados)

    payload = serializar_para_mqtt(pacote)

    topico = topic_telemetria(device_id)



    client.publish(topico, payload, qos=MQTT_QOS)



    print("\n============================")

    print("PACOTE STSP PUBLICADO (MQTT)")

    print("============================")

    print(f"Protocolo:   {PROTOCOLO} v{VERSAO}")

    print(f"Tópico:      {topico}")

    print(f"Device ID:   {device_id}")

    print(f"Timestamp:   {pacote['timestamp']}")

    print(f"Dados:       {dados}")

    print(f"Hash:        {pacote['hash'][:32]}...")

    print(f"Certificado: {cert_info['chave_publica_fingerprint_sha256'][:32]}...")

    print(f"Assinatura:  {pacote['assinatura'][:50]}...")





def executar_dispositivo(device_id: str):

    cert_info = _validar_certificado_local(device_id)

    gerador = GeradorTelemetria(device_id)



    print("=" * 60)

    print(f"  DISPOSITIVO IoT — {device_id} (Edge / Semáforo Inteligente)")

    print("=" * 60)

    print(f"Broker: {MQTT_HOST}:{MQTT_PORT}")



    client = mqtt.Client(

        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,

        client_id=f"semaforo-{device_id}",

    )

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    client.loop_start()



    try:

        while True:

            publicar_telemetria(client, device_id, gerador, cert_info)

            time.sleep(INTERVALO_SEG)

    except KeyboardInterrupt:

        print("\nEncerrando dispositivo...")

    finally:

        client.loop_stop()

        client.disconnect()





def main():

    device_id = sys.argv[1] if len(sys.argv) > 1 else "SEMAFORO_A1"

    if device_id not in DISPOSITIVOS_PADRAO:

        print(f"Aviso: {device_id} não está na lista padrão {DISPOSITIVOS_PADRAO}")

    executar_dispositivo(device_id)





if __name__ == "__main__":

    main()

