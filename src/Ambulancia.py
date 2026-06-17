"""
Ambulancia — Veiculo de emergencia que publica presenca via MQTT.

Publica no topico:
  smarttraffic/v1/ambulancia/{device_id}/presenca

Dados publicados: device_id, latitude, longitude, velocidade, direcao, sirene_ativa.

O Cruzamento assina o topico curinga e detecta a aproximacao,
entrando em modo EMERGENCIA para liberar a passagem.
"""

import json
import threading
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paho.mqtt.client as mqtt

from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_QOS,
    topico_presenca_ambulancia,
    montar_pacote,
    serializar_para_mqtt,
)
from Telemetria import GeradorTelemetriaAmbulancia
from DispositivoSemaforo import _validar_certificado_local

DEVICE_ID_PADRAO = "AMBULANCIA_E1"
INTERVALO_PRESENCA = 3


class Ambulancia:
    def __init__(self, device_id: str = DEVICE_ID_PADRAO):
        self.device_id = device_id
        self.gerador = GeradorTelemetriaAmbulancia(device_id)
        self.cert_info = _validar_certificado_local(device_id)
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"ambulancia-{device_id}",
        )
        self.evento_parar = threading.Event()

    def _publicar_presenca(self):
        dados = self.gerador.proximo_pacote()
        dados["sirene_ativa"] = self.gerador.sirene_ativa
        pacote = montar_pacote(self.device_id, dados)
        pacote["tipo"] = "PRESENCA_AMBULANCIA"
        payload = serializar_para_mqtt(pacote)

        topico = topico_presenca_ambulancia(self.device_id)
        self.client.publish(topico, payload, qos=MQTT_QOS)

        status_sirene = "LIGADA" if dados["sirene_ativa"] else "DESLIGADA"
        print(f"[AMBULANCIA {self.device_id}] Presenca publicada — "
              f"Sirene: {status_sirene} | Vel: {dados['velocidade']}km/h | "
              f"({dados['latitude']}, {dados['longitude']})")

    def ativar_emergencia(self):
        print(f"\n[AMBULANCIA {self.device_id}] EMERGENCIA ATIVADA! Sirene ligada, aproximando do cruzamento.")
        self.gerador.ativar_sirene()

    def desativar_emergencia(self):
        print(f"\n[AMBULANCIA {self.device_id}] Emergencia desativada — sirene desligada.")
        self.gerador.desativar_sirene()

    def iniciar(self, ativar_sirene_apos: int = None):
        self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client.loop_start()

        print("=" * 60)
        print(f"  AMBULANCIA IoT — {self.device_id}")
        print("=" * 60)
        print(f"Topico: {topico_presenca_ambulancia(self.device_id)}")
        print(f"Broker: {MQTT_HOST}:{MQTT_PORT}")

        inicio = time.time()

        try:
            while not self.evento_parar.is_set():
                if ativar_sirene_apos and not self.gerador.sirene_ativa:
                    if time.time() - inicio >= ativar_sirene_apos:
                        self.ativar_emergencia()
                self._publicar_presenca()
                time.sleep(INTERVALO_PRESENCA)
        except KeyboardInterrupt:
            print(f"\n[AMBULANCIA {self.device_id}] Encerrando...")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

    def parar(self):
        self.evento_parar.set()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("device_id", nargs="?", default=DEVICE_ID_PADRAO)
    parser.add_argument("--duracao", type=int, default=0)
    args = parser.parse_args()

    ambulancia = Ambulancia(args.device_id)
    if args.duracao > 0:
        threading.Timer(args.duracao, ambulancia.parar).start()
    ambulancia.iniciar(ativar_sirene_apos=2)

if __name__ == "__main__":
    main()
