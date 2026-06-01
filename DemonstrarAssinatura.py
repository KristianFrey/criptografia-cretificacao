"""
Tarefa 5 — Demonstração de assinatura digital RSA em pacotes IoT.
Executar na raiz: python DemonstrarAssinatura.py
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from Assinatura import (
    assinar_pacote,
    verificar_assinatura_pacote,
    conteudo_assinado,
    info_assinatura,
)

DEVICE_ID = "SEMAFORO_A1"

PACOTE_AMOSTRA = {
    "device_id": DEVICE_ID,
    "timestamp": "2027-05-31T14:30:00",
    "dados": {"carros": 18, "estado": "VERMELHO"},
    "hash": "placeholder_hash_sha256",
}


def main():
    print("=" * 60)
    print("  TAREFA 5 — Assinatura Digital RSA (Semáforo Inteligente)")
    print("=" * 60)

    try:
        meta = info_assinatura(DEVICE_ID)
    except FileNotFoundError:
        print("\nCertificado/chaves não encontrados.")
        print("Execute: python GerarCertificado.py && python DistribuirCertificado.py")
        return

    print(f"\nDispositivo:     {meta['device_id']}")
    print(f"Algoritmo:       {meta['algoritmo']}")
    print(f"Chave privada:   {meta['chave_privada']}")
    print(f"Certificado:     {meta['certificado']}")
    print(f"Chave pública:   RSA {meta['chave_publica_bits']} bits (extraída do certificado)")
    print(f"Fingerprint:     {meta['fingerprint_certificado']}")

    conteudo = conteudo_assinado(
        PACOTE_AMOSTRA["device_id"],
        PACOTE_AMOSTRA["timestamp"],
        PACOTE_AMOSTRA["dados"],
    )
    print(f"\nConteúdo assinado (canônico):")
    print(f"  {conteudo}")

    pacote = copy.deepcopy(PACOTE_AMOSTRA)
    pacote["assinatura"] = assinar_pacote(pacote)
    print(f"\nAssinatura gerada (Base64, {len(pacote['assinatura'])} chars):")
    print(f"  {pacote['assinatura'][:64]}...")

    # Teste 1: pacote íntegro
    ok, msg = verificar_assinatura_pacote(pacote)
    print(f"\n[TESTE 1] Pacote original:     {'PASSOU' if ok else 'FALHOU'} — {msg}")

    # Teste 2: dados alterados (simula tampering)
    pacote_tamper = copy.deepcopy(pacote)
    pacote_tamper["dados"]["estado"] = "VERDE"
    ok2, msg2 = verificar_assinatura_pacote(pacote_tamper)
    print(f"[TESTE 2] Dados adulterados:   {'PASSOU' if ok2 else 'FALHOU'} — {msg2}")

    # Teste 3: timestamp alterado
    pacote_ts = copy.deepcopy(pacote)
    pacote_ts["timestamp"] = "2027-01-01T00:00:00"
    ok3, msg3 = verificar_assinatura_pacote(pacote_ts)
    print(f"[TESTE 3] Timestamp alterado:  {'PASSOU' if ok3 else 'FALHOU'} — {msg3}")

    # Teste 4: assinatura corrompida
    pacote_sig = copy.deepcopy(pacote)
    pacote_sig["assinatura"] = pacote_sig["assinatura"][:-4] + "XXXX"
    ok4, msg4 = verificar_assinatura_pacote(pacote_sig)
    print(f"[TESTE 4] Assinatura inválida: {'PASSOU' if ok4 else 'FALHOU'} — {msg4}")

    print("\n" + "-" * 60)
    print("RESUMO")
    print("-" * 60)
    print("• Assinatura = RSA com chave PRIVADA do certificado do dispositivo")
    print("• Verificação = RSA com chave PÚBLICA extraída do certificado X.509")
    print("• Garante autenticidade e não-repúdio dos dados do semáforo")
    esperado = ok and not ok2 and not ok3 and not ok4
    print(f"\nDemonstração: {'CONCLUÍDA COM SUCESSO' if esperado else 'VERIFICAR FALHAS'}")


if __name__ == "__main__":
    main()
