"""Exibe metadados do certificado. Uso: python scripts/ler_certificado.py [DEVICE_ID]"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from Certificado import (
    carregar_certificado,
    extrair_metadados,
    caminhos_emissao,
    caminhos_dispositivo,
    verificar_certificado,
)

DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "SEMAFORO_A1"


def main():
    caminho = caminhos_dispositivo(DEVICE_ID)["certificado"]
    origem = "dispositivo"

    if not caminho.exists():
        caminho = caminhos_emissao(DEVICE_ID)["certificado"]
        origem = "registro CA"

    if not caminho.exists():
        print(f"Certificado não encontrado para {DEVICE_ID}.")
        print("Execute: python scripts/provisionar_rede.py")
        return

    cert = carregar_certificado(caminho)
    meta = extrair_metadados(cert)
    valido, msg = verificar_certificado(cert, DEVICE_ID)

    print("=" * 60)
    print(f"  CERTIFICADO — {DEVICE_ID} ({origem})")
    print("=" * 60)
    print(f"Device ID:       {meta['device_id']}")
    print(f"Emissor:         {meta['autoridade_emissora']}")
    print(f"Válido até:      {meta['valido_ate']}")
    print(f"Fingerprint:     {meta['chave_publica_fingerprint_sha256']}")
    print(f"Verificação:     {msg} ({'OK' if valido else 'FALHA'})")


if __name__ == "__main__":
    main()
