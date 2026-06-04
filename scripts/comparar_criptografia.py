"""Tarefa 2 — Benchmark de algoritmos simétricos. Uso: python scripts/comparar_criptografia.py"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from Criptografia import (
    criptografar,
    descriptografar,
    listar_algoritmos,
    INFO_ALGORITMOS,
)

PACOTE_AMOSTRA = json.dumps({
    "device_id": "SEMAFORO_A1",
    "timestamp": "2027-05-31T12:00:00",
    "dados": {"carros": 23, "estado": "VERDE", "modo": "NORMAL"},
    "hash": "a" * 64,
    "assinatura": "b" * 344,
})

ITERACOES = 1000


def medir_algoritmo(algoritmo):
    tamanho_original = len(PACOTE_AMOSTRA.encode())
    criptografar(PACOTE_AMOSTRA, algoritmo)
    descriptografar(criptografar(PACOTE_AMOSTRA, algoritmo))

    inicio = time.perf_counter()
    for _ in range(ITERACOES):
        criptografar(PACOTE_AMOSTRA, algoritmo)
    tempo_cifrar = time.perf_counter() - inicio

    cifrado = criptografar(PACOTE_AMOSTRA, algoritmo)

    inicio = time.perf_counter()
    for _ in range(ITERACOES):
        descriptografar(cifrado)
    tempo_decifrar = time.perf_counter() - inicio

    assert descriptografar(cifrado) == PACOTE_AMOSTRA
    tamanho_cifrado = len(cifrado.encode())

    return {
        "tempo_cifrar_ms": (tempo_cifrar / ITERACOES) * 1000,
        "tempo_decifrar_ms": (tempo_decifrar / ITERACOES) * 1000,
        "tempo_total_ms": ((tempo_cifrar + tempo_decifrar) / ITERACOES) * 1000,
        "overhead_pct": ((tamanho_cifrado - tamanho_original) / tamanho_original) * 100,
        "tamanho_cifrado": tamanho_cifrado,
    }


def main():
    resultados = {a: medir_algoritmo(a) for a in listar_algoritmos()}

    print("\n" + "=" * 90)
    print("COMPARAÇÃO CRIPTOGRAFIA SIMÉTRICA — SEMÁFORO INTELIGENTE")
    print("=" * 90)
    for algo, m in resultados.items():
        info = INFO_ALGORITMOS[algo]
        print(
            f"{info['nome']:<22} {m['tempo_total_ms']:>8.4f} ms  "
            f"overhead {m['overhead_pct']:>5.1f}%"
        )


if __name__ == "__main__":
    main()
