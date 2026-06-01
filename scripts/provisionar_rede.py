"""Provisiona certificados para SEMAFORO_A1 e SEMAFORO_B2. Uso: python scripts/provisionar_rede.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from Certificado import (
    AUTORIDADE_EMISSORA,
    gerar_autoridade_certificadora,
    emitir_certificado_dispositivo,
    extrair_metadados,
    carregar_certificado,
    caminhos_dispositivo,
)

DISPOSITIVOS = ("SEMAFORO_A1", "SEMAFORO_B2")


def provisionar_dispositivo(device_id: str):
    print(f"\n  Dispositivo {device_id}")
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert, _, _, _ = emitir_certificado_dispositivo(device_id, chave)

    caminhos = caminhos_dispositivo(device_id)
    caminhos["pasta"].mkdir(parents=True, exist_ok=True)

    with open(caminhos["certificado"], "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(caminhos["chave_privada"], "wb") as f:
        f.write(
            chave.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    meta = extrair_metadados(cert)
    print(f"    Certificado emitido — válido até {meta['valido_ate']}")
    print(f"    Fingerprint: {meta['chave_publica_fingerprint_sha256'][:32]}...")


def main():
    print("=" * 60)
    print("  PROVISIONAMENTO DA REDE — Semáforos Inteligentes")
    print("=" * 60)

    print("\n[1] Autoridade Certificadora (SmartTraffic IoT CA)...")
    gerar_autoridade_certificadora()
    print(f"    {AUTORIDADE_EMISSORA} criada.")

    print("\n[2] Emissão e distribuição local:")
    for device_id in DISPOSITIVOS:
        provisionar_dispositivo(device_id)

    print("\n" + "=" * 60)
    print("  Concluído. Execute: python src/Servidor.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
