"""
Tarefa 6 — SmartTraffic Secure Protocol (STSP) v1.0

Protocolo de comunicação segura para semáforos inteligentes sobre MQTT.

Camadas (dispositivo → servidor):
  1. Aplicação   — telemetria JSON (carros, estado)
  2. Integridade — SHA-256 sobre os dados
  3. Autenticidade — assinatura RSA (chave privada do certificado X.509)
  4. Confidencialidade — cifragem simétrica AES-128-EAX (padrão)
  5. Transporte  — MQTT QoS 1 (semáforo → broker → servidor central)

Tópico MQTT: smarttraffic/v1/semaforo/{device_id}/telemetria
"""

import json
from datetime import datetime

from Criptografia import criptografar, descriptografar, ALGORITMO_PADRAO
from HashUtils import gerar_hash
from Assinatura import assinar_pacote, verificar_assinatura_pacote
from Certificado import (
    obter_certificado_confiavel,
    verificar_certificado,
    extrair_metadados,
)

PROTOCOLO = "STSP"
VERSAO = "1.0"

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_QOS = 1
MQTT_CLIENT_ID_SERVIDOR = "smarttraffic-servidor"
MQTT_TOPIC_BASE = "smarttraffic/v1/semaforo"


def topic_telemetria(device_id: str) -> str:
    return f"{MQTT_TOPIC_BASE}/{device_id}/telemetria"


def topic_telemetria_wildcard() -> str:
    return f"{MQTT_TOPIC_BASE}/+/telemetria"


def montar_pacote(device_id: str, dados: dict, timestamp: str = None, algoritmo: str = None) -> dict:
    """Monta pacote STSP com hash e assinatura digital."""
    timestamp = timestamp or datetime.now().isoformat()
    mensagem = json.dumps(dados)

    pacote = {
        "protocolo": PROTOCOLO,
        "versao": VERSAO,
        "device_id": device_id,
        "timestamp": timestamp,
        "dados": dados,
        "hash": gerar_hash(mensagem),
        "criptografia": algoritmo or ALGORITMO_PADRAO,
    }
    pacote["assinatura"] = assinar_pacote(pacote, device_id)
    return pacote


def serializar_para_mqtt(pacote: dict, algoritmo: str = None) -> str:
    """Cifra o pacote STSP para publicação no payload MQTT."""
    algo = algoritmo or pacote.get("criptografia", ALGORITMO_PADRAO)
    return criptografar(json.dumps(pacote), algo)


def decodificar_mqtt(payload: str) -> dict:
    """Decifra e interpreta payload MQTT recebido."""
    pacote_json = descriptografar(payload)
    pacote = json.loads(pacote_json)

    if pacote.get("protocolo") != PROTOCOLO:
        raise ValueError(f"Protocolo inválido: {pacote.get('protocolo')}")

    return pacote


def validar_timestamp(pacote: dict, max_segundos: int = 30) -> bool:
    timestamp_pacote = datetime.fromisoformat(pacote["timestamp"])
    return (datetime.now() - timestamp_pacote).total_seconds() <= max_segundos


def processar_pacote(pacote: dict, ngfw, proxy, ids, siem) -> dict:
    """
    Pipeline completo de validação STSP no servidor central.
    Retorna dict com resultados de cada camada de segurança.
    """
    device_id = pacote.get("device_id", "unknown")
    resultado = {
        "device_id": device_id,
        "cert_ok": False,
        "ngfw_ok": False,
        "proxy_ok": False,
        "nids_ok": True,
        "hids_ok": True,
        "integridade_ok": False,
        "assinatura_ok": False,
        "timestamp_ok": False,
        "autentico": False,
        "mensagens": [],
    }

    cert = obter_certificado_confiavel(device_id)
    if cert is None:
        resultado["mensagens"].append("Certificado não registrado")
        siem.ingest("Certificado", {"device_id": device_id, "event": "UNKNOWN_DEVICE"})
        return resultado

    cert_ok, cert_msg = verificar_certificado(cert, device_id)
    cert_meta = extrair_metadados(cert)
    resultado["cert_ok"] = cert_ok
    resultado["cert_meta"] = cert_meta
    resultado["mensagens"].append(f"Certificado: {cert_msg}")

    if not cert_ok:
        siem.ingest("Certificado", {"device_id": device_id, "event": "INVALID_CERT"})
        return resultado

    ngfw_ok, ngfw_msg = ngfw.check_device(device_id)
    resultado["ngfw_ok"] = ngfw_ok
    resultado["mensagens"].append(f"NGFW: {ngfw_msg}")
    if not ngfw_ok:
        siem.ingest("NGFW", {"device_id": device_id, "event": "BLOCKED"})
        return resultado

    if not proxy.check_rate_limit(device_id):
        resultado["mensagens"].append("Proxy: rate limit excedido")
        siem.ingest("Proxy", {"device_id": device_id, "event": "RATE_LIMIT_EXCEEDED"})
        ngfw.add_to_blacklist(device_id)
        return resultado

    pacote = proxy.anonymize(pacote)
    resultado["proxy_ok"] = True
    resultado["mensagens"].append("Proxy: OK")

    nids_ok = ids.analyze_nids(pacote)
    hids_ok = ids.analyze_hids(pacote)
    resultado["nids_ok"] = nids_ok
    resultado["hids_ok"] = hids_ok

    if not nids_ok or not hids_ok:
        siem.ingest("IDS", {"device_id": device_id, "nids_ok": nids_ok, "hids_ok": hids_ok})

    siem.ingest("NGFW", {"device_id": device_id, "event": "ALLOWED"}, is_alert=False)
    siem.ingest("Proxy", {"device_id": device_id, "event": "PROXIED"}, is_alert=False)

    mensagem = json.dumps(pacote["dados"])
    resultado["integridade_ok"] = pacote["hash"] == gerar_hash(mensagem)
    resultado["timestamp_ok"] = validar_timestamp(pacote)

    assinatura_ok, assinatura_msg = verificar_assinatura_pacote(pacote, device_id)
    resultado["assinatura_ok"] = assinatura_ok
    resultado["mensagens"].append(assinatura_msg)

    resultado["autentico"] = all([
        resultado["cert_ok"],
        resultado["ngfw_ok"],
        resultado["proxy_ok"],
        resultado["integridade_ok"],
        resultado["assinatura_ok"],
        resultado["timestamp_ok"],
    ])

    return resultado
