"""
Tarefa 5 — Assinatura digital RSA para pacotes IoT.

Fluxo:
  - Dispositivo assina com chave privada vinculada ao certificado X.509
  - Servidor verifica com chave pública extraída do certificado digital
  - Algoritmo: RSA-PKCS#1 v1.5 + SHA-256
"""

import json
from pathlib import Path

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from cryptography.hazmat.primitives import serialization
import base64

from Certificado import (
    carregar_certificado,
    caminhos_dispositivo,
    caminhos_emissao,
    extrair_metadados,
)

ALGORITMO = "RSA-PKCS1v15 + SHA-256"


def conteudo_assinado(device_id: str, timestamp: str, dados: dict) -> str:
    """Representação canônica do pacote — device_id, timestamp e dados."""
    payload = json.dumps(dados, sort_keys=True, separators=(",", ":"))
    return f"{device_id}|{timestamp}|{payload}"


def _caminho_chave_privada(device_id: str) -> Path:
    disp = caminhos_dispositivo(device_id)["chave_privada"]
    if disp.exists():
        return disp
    emitido = caminhos_emissao(device_id)["chave_privada"]
    if emitido.exists():
        return emitido
    raise FileNotFoundError(
        f"Chave privada não encontrada para {device_id}. "
        "Execute GerarCertificado.py e DistribuirCertificado.py"
    )


def _caminho_certificado(device_id: str) -> Path:
    disp = caminhos_dispositivo(device_id)["certificado"]
    if disp.exists():
        return disp
    emitido = caminhos_emissao(device_id)["certificado"]
    if emitido.exists():
        return emitido
    raise FileNotFoundError(
        f"Certificado não encontrado para {device_id}. "
        "Execute GerarCertificado.py e DistribuirCertificado.py"
    )


def chave_publica_do_certificado(device_id: str) -> RSA.RsaKey:
    """Extrai chave pública RSA do certificado digital do dispositivo."""
    cert = carregar_certificado(_caminho_certificado(device_id))
    pub_pem = cert.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return RSA.import_key(pub_pem)


def info_assinatura(device_id: str) -> dict:
    """Metadados da assinatura para demonstração e logs."""
    cert = carregar_certificado(_caminho_certificado(device_id))
    meta = extrair_metadados(cert)
    return {
        "device_id": device_id,
        "algoritmo": ALGORITMO,
        "chave_privada": str(_caminho_chave_privada(device_id)),
        "certificado": str(_caminho_certificado(device_id)),
        "chave_publica_bits": meta["chave_publica_modulo_bits"],
        "fingerprint_certificado": meta["chave_publica_fingerprint_sha256"],
    }


def assinar_mensagem(mensagem: str, device_id: str = "SEMAFORO_A1") -> str:
    """Assina conteúdo arbitrário com a chave privada do certificado."""
    with open(_caminho_chave_privada(device_id), "rb") as f:
        private_key = RSA.import_key(f.read())

    hash_obj = SHA256.new(mensagem.encode())
    assinatura = pkcs1_15.new(private_key).sign(hash_obj)
    return base64.b64encode(assinatura).decode()


def assinar_pacote(pacote: dict, device_id: str = None) -> str:
    """Assina pacote IoT (device_id + timestamp + dados) com chave privada do certificado."""
    device_id = device_id or pacote["device_id"]
    conteudo = conteudo_assinado(pacote["device_id"], pacote["timestamp"], pacote["dados"])
    return assinar_mensagem(conteudo, device_id)


def verificar_assinatura(mensagem: str, assinatura_recebida: str, device_id: str = "SEMAFORO_A1") -> bool:
    """Verifica assinatura usando chave pública extraída do certificado."""
    ok, _ = verificar_assinatura_detalhada(mensagem, assinatura_recebida, device_id)
    return ok


def verificar_assinatura_detalhada(
    mensagem: str, assinatura_recebida: str, device_id: str = "SEMAFORO_A1"
) -> tuple[bool, str]:
    """Verifica assinatura e retorna (sucesso, mensagem descritiva)."""
    try:
        public_key = chave_publica_do_certificado(device_id)
    except FileNotFoundError as e:
        return False, str(e)

    hash_obj = SHA256.new(mensagem.encode())

    try:
        assinatura = base64.b64decode(assinatura_recebida)
        pkcs1_15.new(public_key).verify(hash_obj, assinatura)
        return True, f"Assinatura válida ({ALGORITMO}) — chave pública do certificado {device_id}"
    except (ValueError, TypeError):
        return False, "Assinatura inválida — dados alterados ou certificado/chave incompatível"


def verificar_assinatura_pacote(pacote: dict, device_id: str = None) -> tuple[bool, str]:
    """Verifica assinatura do pacote IoT completo."""
    device_id = device_id or pacote.get("device_id", "SEMAFORO_A1")
    conteudo = conteudo_assinado(pacote["device_id"], pacote["timestamp"], pacote["dados"])
    return verificar_assinatura_detalhada(conteudo, pacote["assinatura"], device_id)
