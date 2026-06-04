"""Broker MQTT embarcado para simulação local (amqtt)."""

import asyncio
import threading
import time

from amqtt.broker import Broker

from Protocolo import MQTT_HOST, MQTT_PORT

_thread = None


def _executar_broker(host: str, port: int):
    config = {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": f"{host}:{port}",
            }
        }
    }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def iniciar():
        broker = Broker(config)
        await broker.start()
        while True:
            await asyncio.sleep(3600)

    loop.run_until_complete(iniciar())


def iniciar_broker_em_thread(host: str = MQTT_HOST, port: int = MQTT_PORT):
    """Inicia broker MQTT em thread daemon (para demo sem Mosquitto externo)."""
    global _thread
    if _thread and _thread.is_alive():
        return

    _thread = threading.Thread(
        target=_executar_broker,
        args=(host, port),
        daemon=True,
        name="mqtt-broker",
    )
    _thread.start()
    time.sleep(0.8)
