"""
Simulador de ataque Man-in-the-Middle (MitM).

Publica pacotes falsos nos topicos de telemetria para demonstrar
como o servidor detecta e bloqueia tentativas de intrusao.

Tipos de ataque simulados:
  1. Dispositivo desconhecido (sem certificado)
  2. Dispositivo com certificado falso (assinatura invalida)
  3. Replay attack (timestamp antigo)
  4. Pacote adulterado (hash invalido)
"""

import json
import threading
import time
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paho.mqtt.client as mqtt

from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_QOS,
    topico_telemetria,
    PROTOCOLO,
    VERSAO,
)

ATAQUES = [
    "DISPOSITIVO_DESCONHECIDO",
    "CERTIFICADO_FALSO",
    "REPLAY_ATTACK",
    "PACOTE_ADULTERADO",
]


class AtacanteMitM:
    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="atacante-mitm",
        )
        self.evento_parar = threading.Event()
        self.contador = 0

    def _gerar_pacote_falso(self, tipo_ataque: str) -> dict:
        self.contador += 1
        fake_id = f"ATACANTE_{random.randint(100, 999)}"

        if tipo_ataque == "DISPOSITIVO_DESCONHECIDO":
            return {
                "protocolo": PROTOCOLO,
                "versao": VERSAO,
                "device_id": fake_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "dados": {"carros": 99, "estado": "VERDE", "tempo_fase_seg": 15,
                          "fila_metros": 0, "modo": "NORMAL", "local": "cruzamento_falso"},
                "hash": "0000000000000000000000000000000000000000000000000000000000000000",
                "assinatura": "ZmFrZWFzc2luYXR1cmFiYXNlNjQ=",
                "criptografia": "aes",
            }

        elif tipo_ataque == "CERTIFICADO_FALSO":
            return {
                "protocolo": PROTOCOLO,
                "versao": VERSAO,
                "device_id": "SEMAFORO_A1",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "dados": {"carros": 0, "estado": "VERDE", "tempo_fase_seg": 999,
                          "fila_metros": 0, "modo": "NORMAL", "local": "cruzamento_A1"},
                "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "assinatura": "QVRBUVVFLUZBTFNPUEVSSUdPU08=",
                "criptografia": "aes",
            }

        elif tipo_ataque == "REPLAY_ATTACK":
            return {
                "protocolo": PROTOCOLO,
                "versao": VERSAO,
                "device_id": "SEMAFORO_B2",
                "timestamp": "2026-01-01T00:00:00",
                "dados": {"carros": 10, "estado": "AMARELO", "tempo_fase_seg": 5,
                          "fila_metros": 20, "modo": "NORMAL", "local": "cruzamento_B2"},
                "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "assinatura": "UkVQTEFZUEFDS0VURkFMU08=",
                "criptografia": "aes",
            }

        elif tipo_ataque == "PACOTE_ADULTERADO":
            return {
                "protocolo": PROTOCOLO,
                "versao": VERSAO,
                "device_id": "SEMAFORO_A1",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "dados": {"carros": -50, "estado": "ROXO", "tempo_fase_seg": 0,
                          "fila_metros": 9999, "modo": "CAOTICO", "local": "cruzamento_A1"},
                "hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                "assinatura": "UEFDT1RFQURVTERSQUFPRkFMU08=",
                "criptografia": "aes",
            }

        return {}

    def _publicar_ataque(self):
        tipo = random.choice(ATAQUES)
        pacote = self._gerar_pacote_falso(tipo)

        from Criptografia import criptografar
        payload = criptografar(json.dumps(pacote))

        topico = topico_telemetria(pacote["device_id"])
        self.client.publish(topico, payload, qos=MQTT_QOS)
        print(f"[ATAQUE MitM #{self.contador}] Tipo: {tipo} | "
              f"Device forjado: {pacote['device_id']} | Topico: {topico}")

    def iniciar(self, intervalo: int = 8):
        self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client.loop_start()

        print("=" * 60)
        print("  ATACANTE Man-in-the-Middle — Simulador de intrusao")
        print("=" * 60)
        print(f"Tipos de ataque: {', '.join(ATAQUES)}")
        print(f"Intervalo: {intervalo}s\n")

        try:
            while not self.evento_parar.is_set():
                self._publicar_ataque()
                time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\n[ATAQUE MitM] Encerrando...")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

    def parar(self):
        self.evento_parar.set()


def main():
    atacante = AtacanteMitM()
    atacante.iniciar()


if __name__ == "__main__":
    main()
