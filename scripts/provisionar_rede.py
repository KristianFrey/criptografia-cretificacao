"""Provisiona certificados para todos os dispositivos da rede. Uso: python scripts/provisionar_rede.py"""

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
from config import DISPOSITIVOS_PADRAO


def provisionar_dispositivo(device_id: str, mac: str = None):
    print(f"\n  Dispositivo: {device_id}")
    if mac:
        print(f"    MAC: {mac}")
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert, _, _, _ = emitir_certificado_dispositivo(device_id, chave, mac_address=mac)

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
    print(f"    Certificado emitido — valido ate {meta['valido_ate']}")
    print(f"    Fingerprint: {meta['chave_publica_fingerprint_sha256'][:32]}...")
    if meta.get("mac"):
        print(f"    MAC no certificado: {meta['mac']}")


def main():
    print("=" * 60)
    print("  PROVISIONAMENTO DA REDE — Semáforos Inteligentes")
    print("=" * 60)

    print("\n[1] Autoridade Certificadora (SmartTraffic IoT CA)...")
    gerar_autoridade_certificadora()
    print(f"    {AUTORIDADE_EMISSORA} criada.")

    print("\n[2] Emissao e distribuicao local:")
    for device_id, cfg in DISPOSITIVOS_PADRAO.items():
        provisionar_dispositivo(device_id, mac=cfg.get("mac"))

    print("\n" + "=" * 60)
    print("  Provisionamento concluido!")
    print("  Execute: python Run.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
