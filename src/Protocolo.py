"""
Tarefa 6 — SmartTraffic Secure Protocol (STSP) v1.0

Protocolo de comunicacao segura para semaforos inteligentes sobre MQTT.

Camadas (dispositivo -> servidor):
  1. Aplicacao       — telemetria JSON (carros, estado, fase, fila, modo)
  2. Integridade     — SHA-256 sobre os dados
  3. Autenticidade   — assinatura RSA (chave privada do certificado X.509)
  4. Confidencialidade — cifragem simetrica AES-128-EAX (padrao)
  5. Transporte      — MQTT QoS 1 (semaforo -> broker -> servidor central)
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
MQTT_PORT_TLS = 8883
MQTT_QOS = 1
MQTT_CLIENT_ID_SERVIDOR = "smarttraffic-servidor"
MQTT_TOPICO_BASE = "smarttraffic/v1/semaforo"
MQTT_TOPICO_ATMS = "smarttraffic/v1/atms/alertas"
MQTT_TOPICO_AMBULANCIA = "smarttraffic/v1/ambulancia"


def topico_telemetria(device_id: str) -> str:
    return f"{MQTT_TOPICO_BASE}/{device_id}/telemetria"


def topico_telemetria_curinga() -> str:
    return f"{MQTT_TOPICO_BASE}/+/telemetria"


def topico_alertas_atms() -> str:
    return MQTT_TOPICO_ATMS


def topico_presenca_ambulancia_curinga() -> str:
    return f"{MQTT_TOPICO_AMBULANCIA}/+/presenca"


def topico_presenca_ambulancia(ambulancia_id: str) -> str:
    return f"{MQTT_TOPICO_AMBULANCIA}/{ambulancia_id}/presenca"


def montar_alerta_atms(device_id: str, severidade: str, mensagem: str, fontes: list) -> dict:
    return {
        "protocolo": PROTOCOLO,
        "tipo": "alerta_siem",
        "device_id": device_id,
        "severidade": severidade,
        "mensagem": mensagem,
        "fontes_correlacionadas": fontes,
        "timestamp": datetime.now().isoformat(),
        "destino": "ATMS_DASHBOARD",
    }


def montar_pacote(device_id: str, dados: dict, timestamp: str = None, algoritmo: str = None) -> dict:
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
    algo = algoritmo or pacote.get("criptografia", ALGORITMO_PADRAO)
    return criptografar(json.dumps(pacote), algo)


def decodificar_mqtt(payload: str) -> dict:
    pacote_json = descriptografar(payload)
    pacote = json.loads(pacote_json)

    if pacote.get("protocolo") != PROTOCOLO:
        raise ValueError(f"Protocolo invalido: {pacote.get('protocolo')}")

    return pacote


def validar_timestamp(pacote: dict, max_segundos: int = 30) -> bool:
    timestamp_pacote = datetime.fromisoformat(pacote["timestamp"])
    return (datetime.now() - timestamp_pacote).total_seconds() <= max_segundos


def processar_pacote(pacote: dict, ngfw, proxy, ids, siem) -> dict:
    device_id = pacote.get("device_id", "desconhecido")
    resultado = {
        "device_id": device_id,
        "cert_ok": False,
        "mac_ok": False,
        "ngfw_ok": False,
        "proxy_ok": False,
        "nids_ok": True,
        "hids_ok": True,
        "integridade_ok": False,
        "assinatura_ok": False,
        "timestamp_ok": False,
        "autentico": False,
        "classificacao": "DESCONHECIDO",
        "mensagens": [],
    }

    cert = obter_certificado_confiavel(device_id)
    if cert is None:
        resultado["mensagens"].append("Certificado nao registrado")
        resultado["classificacao"] = "DISPOSITIVO_NAO_CADASTRADO"
        siem.ingerir("Certificado", {"device_id": device_id, "evento": "DISPOSITIVO_DESCONHECIDO"})
        return resultado

    cert_ok, cert_msg = verificar_certificado(cert, device_id)
    cert_meta = extrair_metadados(cert)
    resultado["cert_ok"] = cert_ok
    resultado["cert_meta"] = cert_meta
    resultado["mensagens"].append(f"Certificado: {cert_msg}")

    if not cert_ok:
        if "MAC" in cert_msg:
            resultado["classificacao"] = "MITM_MAC_FALSIFICADO"
            siem.ingerir("Certificado", {"device_id": device_id, "evento": "MAC_INVALIDO", "mensagem": cert_msg}, eh_alerta=True)
        else:
            resultado["classificacao"] = "MITM_CERTIFICADO_INVALIDO"
            siem.ingerir("Certificado", {"device_id": device_id, "evento": "CERTIFICADO_INVALIDO"})
        return resultado

    mac = cert_meta.get("mac")
    resultado["mac"] = mac
    resultado["mac_ok"] = mac is not None

    ngfw_ok, ngfw_msg = ngfw.verificar_dispositivo(device_id, mac)
    resultado["ngfw_ok"] = ngfw_ok
    resultado["mensagens"].append(f"NGFW: {ngfw_msg}")
    if not ngfw_ok:
        resultado["classificacao"] = "MITM_NGFW_BLOQUEADO"
        siem.ingerir("NGFW", {"device_id": device_id, "evento": "BLOQUEADO", "mac": mac})
        return resultado

    if not proxy.verificar_limite_taxa(device_id):
        resultado["mensagens"].append("Proxy: limite de taxa excedido")
        resultado["classificacao"] = "NEGADO_TAXA"
        siem.ingerir("Proxy", {"device_id": device_id, "evento": "LIMITE_TAXA_EXCEDIDO"})
        ngfw.adicionar_blacklist(device_id)
        return resultado

    pacote = proxy.anonimizar(pacote)
    resultado["proxy_ok"] = True
    resultado["mensagens"].append("Proxy: OK")

    nids_ok = ids.analisar_nids(pacote)
    hids_ok = ids.analisar_hids(pacote)
    resultado["nids_ok"] = nids_ok
    resultado["hids_ok"] = hids_ok

    if not nids_ok or not hids_ok:
        siem.ingerir("IDS", {"device_id": device_id, "nids_ok": nids_ok, "hids_ok": hids_ok}, eh_alerta=True)
        if not nids_ok:
            siem.ingerir(
                "MQTT_BROKER",
                {"device_id": device_id, "evento": "DOS_SUSPEITO"},
                eh_alerta=True,
            )

    siem.ingerir("NGFW", {"device_id": device_id, "evento": "PERMITIDO"}, eh_alerta=False)
    siem.ingerir("Proxy", {"device_id": device_id, "evento": "PROXIADO"}, eh_alerta=False)

    mensagem = json.dumps(pacote["dados"])
    resultado["integridade_ok"] = pacote["hash"] == gerar_hash(mensagem)
    resultado["timestamp_ok"] = validar_timestamp(pacote)

    assinatura_ok, assinatura_msg = verificar_assinatura_pacote(pacote, device_id)
    resultado["assinatura_ok"] = assinatura_ok
    resultado["mensagens"].append(assinatura_msg)

    if not assinatura_ok:
        resultado["classificacao"] = "MITM_ASSINATURA_INVALIDA"

    resultado["autentico"] = all([
        resultado["cert_ok"],
        resultado["ngfw_ok"],
        resultado["proxy_ok"],
        resultado["integridade_ok"],
        resultado["assinatura_ok"],
        resultado["timestamp_ok"],
    ])

    if resultado["autentico"]:
        resultado["classificacao"] = "AUTENTICO"

    return resultado
