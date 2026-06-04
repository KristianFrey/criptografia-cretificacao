"""
Cruzamento Inteligente — Orquestrador de 2 semaforos coordenados.

Gerencia dois dispositivos semaforo em um cruzamento:
  - Semaforo A1 (via principal)
  - Semaforo B2 (via secundaria)

Logica de coordenacao:
  - A1 VERDE  =>  B2 VERMELHO
  - A1 VERMELHO => B2 VERDE
  - Emergencia: ambos abrem verde para direcao da ambulancia, oposto vermelho.

Tambem assina topico de presenca de ambulancias para acionar modo EMERGENCIA.
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
    topico_telemetria,
    topico_presenca_ambulancia_curinga,
    montar_pacote,
    serializar_para_mqtt,
)
from Telemetria import GeradorTelemetria
from DispositivoSemaforo import (
    INTERVALO_SEG,
    publicar_telemetria,
    criar_cliente_mqtt,
    _validar_certificado_local,
)

SEMAFORO_PRINCIPAL = "SEMAFORO_A1"
SEMAFORO_SECUNDARIO = "SEMAFORO_B2"


class Cruzamento:
    def __init__(self):
        self.evento_parar = threading.Event()
        self.modo_emergencia = threading.Event()
        self.ambulancia_proxima = threading.Event()
        self.dados_ambulancia = None
        self._lock = threading.Lock()

        self.gerador_a1 = GeradorTelemetria(SEMAFORO_PRINCIPAL)
        self.gerador_b2 = GeradorTelemetria(SEMAFORO_SECUNDARIO)

        self.cert_a1 = _validar_certificado_local(SEMAFORO_PRINCIPAL)
        self.cert_b2 = _validar_certificado_local(SEMAFORO_SECUNDARIO)

        self.client_a1 = criar_cliente_mqtt(SEMAFORO_PRINCIPAL)
        self.client_b2 = criar_cliente_mqtt(SEMAFORO_SECUNDARIO)
        self.client_escuta = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="cruzamento-escuta",
        )

        self.client_a1.loop_start()
        self.client_b2.loop_start()

        self._configurar_escuta_ambulancia()

    def _configurar_escuta_ambulancia(self):
        def ao_conectar(client, userdata, flags, reason_code, properties):
            topico = topico_presenca_ambulancia_curinga()
            client.subscribe(topico, qos=MQTT_QOS)
            print(f"[CRUZAMENTO] Escutando ambulancias em: {topico}")

        def ao_receber(client, userdata, msg):
            try:
                dados = json.loads(msg.payload.decode())
                if dados.get("sirene_ativa"):
                    with self._lock:
                        self.dados_ambulancia = dados
                        self.ambulancia_proxima.set()
                        self.modo_emergencia.set()
                    print(f"\n[CRUZAMENTO] AMBULANCIA DETECTADA! {dados.get('device_id')}")
                    print(f"[CRUZAMENTO] Entrando em modo EMERGENCIA — liberando via principal")
            except Exception as e:
                pass

        self.client_escuta.on_connect = ao_conectar
        self.client_escuta.on_message = ao_receber
        self.client_escuta.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client_escuta.loop_start()

    def _coordenar_estados(self):
        if self.modo_emergencia.is_set():
            self.gerador_a1.estado = "VERDE"
            self.gerador_a1.definir_modo_emergencia(True)
            self.gerador_b2.estado = "VERMELHO"
            self.gerador_b2.definir_modo_emergencia(True)
        else:
            self.gerador_a1.definir_modo_emergencia(False)
            self.gerador_b2.definir_modo_emergencia(False)
            a1_verde = self.gerador_a1.estado == "VERDE"
            b2_verde = self.gerador_b2.estado == "VERDE"
            if a1_verde and b2_verde:
                self.gerador_b2.estado = "VERMELHO"
            elif not a1_verde and not b2_verde:
                self.gerador_b2.estado = "VERDE"

    def _verificar_fim_emergencia(self):
        if self.modo_emergencia.is_set():
            with self._lock:
                if self.dados_ambulancia is None:
                    return
                import random
                if random.random() < 0.15:
                    self.modo_emergencia.clear()
                    self.ambulancia_proxima.clear()
                    self.dados_ambulancia = None
                    print("\n[CRUZAMENTO] Ambulancia saiu da area. Voltando ao modo NORMAL.")

    def _thread_semaforo(self, device_id, gerador, cert_info, client):
        while not self.evento_parar.is_set():
            self._coordenar_estados()
            self._verificar_fim_emergencia()
            publicar_telemetria(client, device_id, gerador, cert_info)
            time.sleep(INTERVALO_SEG)

    def iniciar(self):
        print("=" * 60)
        print("  CRUZAMENTO INTELIGENTE — SmartTraffic")
        print(f"  Semaforos: {SEMAFORO_PRINCIPAL} (principal) + {SEMAFORO_SECUNDARIO} (secundario)")
        print("  Escuta ambulancia: SIM")
        print("=" * 60)

        t_a1 = threading.Thread(
            target=self._thread_semaforo,
            args=(SEMAFORO_PRINCIPAL, self.gerador_a1, self.cert_a1, self.client_a1),
            daemon=True, name="semaforo-a1"
        )
        t_b2 = threading.Thread(
            target=self._thread_semaforo,
            args=(SEMAFORO_SECUNDARIO, self.gerador_b2, self.cert_b2, self.client_b2),
            daemon=True, name="semaforo-b2"
        )

        t_a1.start()
        t_b2.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[CRUZAMENTO] Encerrando...")
            self.evento_parar.set()
            self.client_a1.loop_stop()
            self.client_a1.disconnect()
            self.client_b2.loop_stop()
            self.client_b2.disconnect()
            self.client_escuta.loop_stop()
            self.client_escuta.disconnect()


def main():
    cruzamento = Cruzamento()
    cruzamento.iniciar()


if __name__ == "__main__":
    main()
