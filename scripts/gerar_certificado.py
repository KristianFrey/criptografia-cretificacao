"""Emite CA e certificado de um dispositivo. Uso: python scripts/gerar_certificado.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from Certificado import (
    AUTORIDADE_EMISSORA,
    gerar_autoridade_certificadora,
    emitir_certificado_dispositivo,
    extrair_metadados,
)

DEVICE_ID = "SEMAFORO_A1"


def main():
    print("=" * 60)
    print("  TAREFA 4 — Emissão de Certificado Digital IoT")
    print("=" * 60)

    gerar_autoridade_certificadora()
    print(f"CA: {AUTORIDADE_EMISSORA}")

    cert, _, caminho_cert, caminho_priv = emitir_certificado_dispositivo(DEVICE_ID)
    meta = extrair_metadados(cert)

    print(f"\nDevice ID:     {meta['device_id']}")
    print(f"Certificado:   {caminho_cert}")
    print(f"Chave privada: {caminho_priv}")
    print(f"Válido até:    {meta['valido_ate']}")
    print("\nPara rede completa: python scripts/provisionar_rede.py")


if __name__ == "__main__":
    main()
