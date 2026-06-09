"""
Run.py — Orquestrador principal do SmartTraffic.

Fluxo automatico (clone => ativar_venv => Run.py => FIM):
  1. Provisiona certificados (sempre, garante ambiente limpo)
  2. Compila frontend SIEM (se necessario)
  3. Inicia servidor HTTP SIEM (painel web na porta 8090)
  4. Inicia broker MQTT embarcado
  5. Inicia servidor central (validacao + logging JSON)
  6. Inicia Cruzamento (2 semaforos coordenados)
  7. Agenda atacante MitM (publica pacotes falsos)
  8. Agenda ambulancia (entra em emergencia)

Uso:
  python Run.py

Abra http://localhost:8090 no navegador para ver o painel SIEM.
Pressione Ctrl+C para encerrar tudo.
"""

import os
import subprocess
import sys
import time
import threading
import signal
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

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
)
from config import DISPOSITIVOS_PADRAO, CAMINHO_CA_CERT, garantir_estrutura_dados
import paho.mqtt.client as mqtt

threads = []
evento_parar_global = threading.Event()

DELAY_ATAQUE = 15
DELAY_AMBULANCIA = 25
DURACAO_AMBULANCIA = 20
INTERVALO_ATAQUE = 10


def _provisionar():
    print("=" * 60)
    print("  [SETUP] Provisionando certificados da rede...")
    print("=" * 60)
    script = RAIZ / "scripts" / "provisionar_rede.py"
    resultado = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(RAIZ)
    )
    if resultado.returncode != 0:
        print("ERRO no provisionamento:")
        print(resultado.stderr)
        sys.exit(1)
    print(resultado.stdout)


def _compilar_frontend():
    pasta_siem = RAIZ / "siem"
    _use_shell = sys.platform == "win32"
    if not (pasta_siem / "node_modules").exists():
        print("\n  [SETUP] Instalando dependencias do frontend (npm install)...")
        subprocess.run(["npm", "install"], cwd=str(pasta_siem), check=True, shell=_use_shell)

    precisa_build = not (pasta_siem / "out" / "index.html").exists()
    if precisa_build:
        print("\n  [SETUP] Compilando frontend SIEM (npm run build)...")
        subprocess.run(["npm", "run", "build"], cwd=str(pasta_siem), check=True, shell=_use_shell)
        print("  [SETUP] Frontend compilado em siem/out/")
    else:
        print("  [SETUP] Frontend ja compilado, pulando build.")


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

    threading.Timer(2.0, lambda: webbrowser.open("http://localhost:8090")).start()

    client.loop_forever()


def main():
    def _tratar_sinal(sig, frame):
        print("\n[Run] Encerrando todos os componentes...")
        evento_parar_global.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, _tratar_sinal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _tratar_sinal)

    garantir_estrutura_dados()

    print("\n[SETUP] Verificando e provisionando certificados...")
    _provisionar()

    print("\n[SETUP] Verificando e compilando frontend SIEM...")
    _compilar_frontend()

    _iniciar_servidor()


if __name__ == "__main__":
    main()
