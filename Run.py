#!/usr/bin/env python3
"""
Run.py — Orquestrador principal do SmartTraffic.

Inicia automaticamente:
  1. Servidor HTTP SIEM (painel web na porta 8090)
  2. Broker MQTT embarcado
  3. Servidor central (validacao + logging JSON)
  4. Cruzamento (2 semaforos coordenados)
  5. Atacante MitM (publica pacotes falsos a cada 10s)
  6. Ambulancia (entra em emergencia apos alguns segundos)

Uso:
  python Run.py

Abra http://localhost:8090 no navegador para ver o painel SIEM.
Pressione Ctrl+C para encerrar tudo.
"""

import sys
import time
import threading
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from BrokerMQTT import iniciar_broker_em_thread
from Servidor import ao_conectar, ao_receber_mensagem, ngfw, proxy, ids, siem
from ServidorSIEM import iniciar_servidor_siem
from Protocolo import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_QOS,
    MQTT_PORT_TLS,
    MQTT_CLIENT_ID_SERVIDOR,
    PROTOCOLO,
    VERSAO,
    topico_telemetria_curinga,
    topico_alertas_atms,
    topico_presenca_ambulancia_curinga,
)
from config import DISPOSITIVOS_PADRAO
import paho.mqtt.client as mqtt

threads = []
evento_parar_global = threading.Event()

DELAY_ATAQUE = 15
DELAY_AMBULANCIA = 25
DURACAO_AMBULANCIA = 20
INTERVALO_ATAQUE = 10


def _iniciar_cruzamento():
    print("\n[Run] Iniciando Cruzamento (SEMAFORO_A1 + SEMAFORO_B2)...")
    from Cruzamento import Cruzamento
    cruz = Cruzamento()
    cruz.iniciar()


def _iniciar_atacante():
    print(f"\n[Run] Aguardando {DELAY_ATAQUE}s antes de iniciar atacante MitM...")
    evento_parar_global.wait(DELAY_ATAQUE)
    if evento_parar_global.is_set():
        return
    print("\n[Run] Iniciando Atacante MitM...")
    from MitM import AtacanteMitM
    atacante = AtacanteMitM()
    atacante.iniciar(intervalo=INTERVALO_ATAQUE)


def _iniciar_ambulancia():
    print(f"\n[Run] Aguardando {DELAY_AMBULANCIA}s antes de iniciar Ambulancia...")
    evento_parar_global.wait(DELAY_AMBULANCIA)
    if evento_parar_global.is_set():
        return
    print("\n[Run] Iniciando Ambulancia (emergencia em 5s)...")
    from Ambulancia import Ambulancia
    amb = Ambulancia(device_id="AMBULANCIA_E1")
    t = threading.Thread(
        target=lambda: amb.iniciar(ativar_sirene_apos=5),
        daemon=True, name="ambulancia"
    )
    t.start()
    threads.append(t)

    evento_parar_global.wait(DURACAO_AMBULANCIA)
    if amb and amb.gerador.sirene_ativa:
        print("\n[Run] Desativando sirene da ambulancia...")
        amb.desativar_emergencia()
        evento_parar_global.wait(8)
        print("\n[Run] Encerrando ambulancia...")
        amb.parar()


def _iniciar_siem():
    servidor = iniciar_servidor_siem(porta=8090)
    t = threading.Thread(target=servidor.serve_forever, daemon=True, name="siem-http")
    t.start()
    threads.append(t)


def _iniciar_servidor():
    print("=" * 60)
    print("  SmartTraffic — Execucao Automatizada")
    print(f"  Protocolo: {PROTOCOLO} v{VERSAO}")
    print("=" * 60)
    print(f"Dispositivos autorizados: {', '.join(DISPOSITIVOS_PADRAO.keys())}")
    print(f"Painel SIEM:          http://localhost:8090")
    print(f"Ataque MitM em:       {DELAY_ATAQUE}s")
    print(f"Ambulancia em:        {DELAY_AMBULANCIA}s (duracao {DURACAO_AMBULANCIA}s)")
    print("=" * 60)

    print("\n[1/5] Iniciando servidor HTTP SIEM (painel web)...")
    _iniciar_siem()

    print("\n[2/5] Iniciando broker MQTT embarcado...")
    iniciar_broker_em_thread()
    print(f"      Broker: {MQTT_HOST}:{MQTT_PORT} (prod.: TLS porta {MQTT_PORT_TLS})")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID_SERVIDOR,
    )
    client.on_connect = ao_conectar
    client.on_message = ao_receber_mensagem

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    t_cruz = threading.Thread(target=_iniciar_cruzamento, daemon=True, name="cruzamento")
    t_ataque = threading.Thread(target=_iniciar_atacante, daemon=True, name="atacante")
    t_ambulancia = threading.Thread(target=_iniciar_ambulancia, daemon=True, name="ambulancia")

    threads.extend([t_cruz, t_ataque, t_ambulancia])

    print("\n[3/5] Iniciando Cruzamento (semaforos)...")
    t_cruz.start()

    print("\n[4/5] Agendando atacante MitM...")
    t_ataque.start()

    print("\n[5/5] Agendando ambulancia...")
    t_ambulancia.start()

    print(f"\n[Run] ABRA http://localhost:8090 para ver o painel SIEM.")
    print("[Run] Sistema em execucao. Pressione Ctrl+C para encerrar.\n")

    client.loop_forever()


def main():
    def _tratar_sinal(sig, frame):
        print("\n[Run] Encerrando todos os componentes...")
        evento_parar_global.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, _tratar_sinal)
    signal.signal(signal.SIGTERM, _tratar_sinal)

    _iniciar_servidor()


if __name__ == "__main__":
    main()
