"""
Tarefa 4 — Simulação de distribuição segura de certificados para dispositivos IoT.

Fluxo:
  1. Dispositivo gera par de chaves localmente (chave privada nunca sai do dispositivo)
  2. Dispositivo envia solicitação de registro (Device ID + chave pública) à CA
  3. CA valida identidade na whitelist e assina o certificado
  4. CA entrega certificado em canal cifrado (PSK de provisionamento — simulação TLS)
  5. Dispositivo armazena certificado em pasta local segura

Uso: python scripts/distribuir_certificado.py
"""

import base64
import hashlib
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from Crypto.Cipher import AES

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from Certificado import (
    AUTORIDADE_EMISSORA,
    gerar_autoridade_certificadora,
    emitir_certificado_dispositivo,
    carregar_certificado,
    extrair_metadados,
    caminhos_dispositivo,
    CAMINHO_CA_CERT,
)

DEVICE_ID = "SEMAFORO_A1"

# PSK simulada — em produção viria de fábrica ou QR code no dispositivo
PSK_PROVISIONAMENTO = hashlib.sha256(b"SmartTraffic-Provision-2027").digest()[:16]

# TODO: trocar pra mac, trocar log para JSON, fazer instanciador de semaforos. verificar se é possivel fazer um orquestrador de uma avenida/cruzamento. Implementar o modo de emergencia nos semaforos (abrir quando necessario)
# TODO: revisar se deve usar TAREFA 5 — Assinatura Digital RSA (Semáforo Inteligente).

WHITELIST = {"SEMAFORO_A1", "SEMAFORO_B2", "SEMAFORO_C3", "CAMERA_A1"}


def _cifrar_psk(dados: bytes) -> str:
    cipher = AES.new(PSK_PROVISIONAMENTO, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(dados)
    pacote = cipher.nonce + tag + ciphertext
    return base64.b64encode(pacote).decode()


def _decifrar_psk(token: str) -> bytes:
    pacote = base64.b64decode(token)
    nonce, tag, ciphertext = pacote[:16], pacote[16:32], pacote[32:]
    cipher = AES.new(PSK_PROVISIONAMENTO, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def dispositivo_gerar_chaves():
    print(f"\n[DISPOSITIVO {DEVICE_ID}] Gerando par de chaves RSA localmente...")
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = chave.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    print("      Chave privada permanece no dispositivo (nunca transmitida).")
    return chave, pub_pem


def dispositivo_solicitar_registro(pub_pem: bytes) -> dict:
    solicitacao = {
        "device_id": DEVICE_ID,
        "chave_publica_pem": pub_pem.decode(),
        "tipo": "semaforo_inteligente",
    }
    print(f"\n[DISPOSITIVO {DEVICE_ID}] Enviando solicitação de registro à CA...")
    return solicitacao


def ca_validar_e_emitir(solicitacao: dict, chave_privada_dispositivo):
    device_id = solicitacao["device_id"]
    print(f"\n[CA {AUTORIDADE_EMISSORA}] Recebida solicitação de {device_id}")

    if device_id not in WHITELIST:
        raise PermissionError(f"Dispositivo {device_id} não está na whitelist da CA")

    print("      Whitelist: OK")
    print("      Assinando certificado com metadados obrigatórios...")

    if not CAMINHO_CA_CERT.exists():
        gerar_autoridade_certificadora()

    cert, _, caminho_cert, _ = emitir_certificado_dispositivo(device_id, chave_privada_dispositivo)
    return cert, caminho_cert


def ca_entregar_certificado_cifrado(cert_pem: bytes) -> str:
    print(f"\n[CA] Entregando certificado via canal cifrado (PSK de provisionamento)...")
    token = _cifrar_psk(cert_pem)
    print("      Certificado cifrado com AES-128-EAX + PSK.")
    return token


def dispositivo_receber_e_armazenar(token: str, chave_privada):
    print(f"\n[DISPOSITIVO {DEVICE_ID}] Recebendo e decifrando certificado...")
    cert_pem = _decifrar_psk(token)

    caminhos = caminhos_dispositivo(DEVICE_ID)
    caminhos["pasta"].mkdir(parents=True, exist_ok=True)

    with open(caminhos["certificado"], "wb") as f:
        f.write(cert_pem)

    with open(caminhos["chave_privada"], "wb") as f:
        f.write(
            chave_privada.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    print(f"      Certificado salvo: {caminhos['certificado']}")
    print(f"      Chave privada salva: {caminhos['chave_privada']}")

    cert = carregar_certificado(caminhos["certificado"])
    return cert


def main():
    print("=" * 60)
    print("  TAREFA 4 — Distribuição Segura de Certificados IoT")
    print("  Cenário: Semáforo Inteligente")
    print("=" * 60)

    chave_disp, pub_pem = dispositivo_gerar_chaves()
    solicitacao = dispositivo_solicitar_registro(pub_pem)
    cert, _ = ca_validar_e_emitir(solicitacao, chave_disp)
    token = ca_entregar_certificado_cifrado(
        cert.public_bytes(serialization.Encoding.PEM)
    )
    cert_final = dispositivo_receber_e_armazenar(token, chave_disp)

    meta = extrair_metadados(cert_final)
    print("\n" + "=" * 60)
    print("  DISTRIBUIÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Device ID:           {meta['device_id']}")
    print(f"  Autoridade Emissora: {meta['autoridade_emissora']}")
    print(f"  Válido até:          {meta['valido_ate']}")
    print(f"  Fingerprint:         {meta['chave_publica_fingerprint_sha256']}")
    print("\n  O dispositivo pode iniciar comunicação segura com o servidor.")


if __name__ == "__main__":
    main()
