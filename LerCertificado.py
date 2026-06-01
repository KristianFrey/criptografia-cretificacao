"""
Tarefa 4 — Exibe metadados obrigatórios do certificado do dispositivo.
Executar na raiz: python LerCertificado.py [DEVICE_ID]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

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
    origem = "dispositivo (pós-distribuição)"

    if not caminho.exists():
        caminho = caminhos_emissao(DEVICE_ID)["certificado"]
        origem = "registro da CA (pré-distribuição)"

    if not caminho.exists():
        print(f"Certificado não encontrado para {DEVICE_ID}.")
        print("Execute: python GerarCertificado.py")
        return

    cert = carregar_certificado(caminho)
    meta = extrair_metadados(cert)
    valido, msg = verificar_certificado(cert, DEVICE_ID)

    print("=" * 60)
    print(f"  CERTIFICADO DIGITAL — {DEVICE_ID}")
    print(f"  Origem: {origem}")
    print("=" * 60)

    print(f"\nDevice ID:             {meta['device_id']}")
    print(f"Autoridade Emissora:   {meta['autoridade_emissora']}")
    print(f"Válido de:             {meta['valido_de']}")
    print(f"Válido até:            {meta['valido_ate']}")
    print(f"Número serial:         {meta['serial']}")
    print(f"Chave pública (bits):  {meta['chave_publica_modulo_bits']}")
    print(f"Expoente público:      {meta['chave_publica_expoente']}")
    print(f"Fingerprint SHA-256:     {meta['chave_publica_fingerprint_sha256']}")

    print(f"\nSubject:  {cert.subject.rfc4514_string()}")
    print(f"Issuer:   {cert.issuer.rfc4514_string()}")
    print(f"\nVerificação: {msg} ({'OK' if valido else 'FALHA'})")


if __name__ == "__main__":
    main()
