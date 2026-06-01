"""
Tarefa 4 — Gera a CA simulada e emite certificado do dispositivo semáforo.
Executar na raiz do projeto: python GerarCertificado.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

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
    print("  Cenário: Semáforo Inteligente em Cidades Inteligentes")
    print("=" * 60)

    print("\n[1/3] Gerando Autoridade Certificadora simulada...")
    cert_ca, _ = gerar_autoridade_certificadora()
    print(f"      CA criada: {AUTORIDADE_EMISSORA}")

    print(f"\n[2/3] Emitindo certificado para dispositivo {DEVICE_ID}...")
    cert, _, caminho_cert, caminho_priv = emitir_certificado_dispositivo(DEVICE_ID)
    print(f"      Certificado: {caminho_cert}")
    print(f"      Chave privada: {caminho_priv}")

    print("\n[3/3] Metadados obrigatórios do certificado:")
    meta = extrair_metadados(cert)
    print(f"      Device ID:           {meta['device_id']}")
    print(f"      Autoridade Emissora: {meta['autoridade_emissora']}")
    print(f"      Válido de:           {meta['valido_de']}")
    print(f"      Válido até:          {meta['valido_ate']}")
    print(f"      Chave pública:       RSA {meta['chave_publica_modulo_bits']} bits")
    print(f"      Fingerprint SHA-256: {meta['chave_publica_fingerprint_sha256']}")

    print("\nCertificado emitido com sucesso!")
    print("Próximo passo: python DistribuirCertificado.py")


if __name__ == "__main__":
    main()
