"""
Tarefa 2 — Comparação de algoritmos de criptografia simétrica para IoT.
Executar a partir da pasta src: python CompararCriptografia.py
"""

import json
import time

from Criptografia import (
    criptografar,
    descriptografar,
    listar_algoritmos,
    INFO_ALGORITMOS,
)

# pacote de amostra semelhante ao enviado pelo semáforo inteligente
PACOTE_AMOSTRA = json.dumps({
    "device_id": "SEMAFORO_A1",
    "timestamp": "2027-05-31T12:00:00",
    "dados": {"carros": 23, "estado": "VERDE"},
    "hash": "a" * 64,
    "assinatura": "b" * 344,
})

ITERACOES = 1000


def medir_algoritmo(algoritmo):
    tamanho_original = len(PACOTE_AMOSTRA.encode())

    # warmup
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

    decifrado = descriptografar(cifrado)
    assert decifrado == PACOTE_AMOSTRA

    tamanho_cifrado = len(cifrado.encode())
    overhead_bytes = tamanho_cifrado - tamanho_original
    overhead_pct = (overhead_bytes / tamanho_original) * 100

    return {
        "tempo_cifrar_ms": (tempo_cifrar / ITERACOES) * 1000,
        "tempo_decifrar_ms": (tempo_decifrar / ITERACOES) * 1000,
        "tempo_total_ms": ((tempo_cifrar + tempo_decifrar) / ITERACOES) * 1000,
        "tamanho_original": tamanho_original,
        "tamanho_cifrado": tamanho_cifrado,
        "overhead_bytes": overhead_bytes,
        "overhead_pct": overhead_pct,
    }


def imprimir_tabela(resultados):
    print("\n" + "=" * 90)
    print("COMPARAÇÃO DE CRIPTOGRAFIA SIMÉTRICA — SEMÁFORO INTELIGENTE (IoT)")
    print("=" * 90)
    print(f"Pacote de amostra: {len(PACOTE_AMOSTRA)} caracteres | Iterações: {ITERACOES}")
    print("-" * 90)
    print(
        f"{'Algoritmo':<22} {'Chave':>6} {'Cifrar(ms)':>12} {'Decifrar(ms)':>13} "
        f"{'Total(ms)':>10} {'Overhead':>10} {'Tamanho':>8}"
    )
    print("-" * 90)

    for algo, medidas in resultados.items():
        info = INFO_ALGORITMOS[algo]
        print(
            f"{info['nome']:<22} {info['tamanho_chave_bits']:>4}b "
            f"{medidas['tempo_cifrar_ms']:>12.4f} {medidas['tempo_decifrar_ms']:>13.4f} "
            f"{medidas['tempo_total_ms']:>10.4f} "
            f"{medidas['overhead_pct']:>9.1f}% {medidas['tamanho_cifrado']:>8}"
        )

    print("-" * 90)


def imprimir_analise(resultados):
    mais_rapido = min(resultados, key=lambda a: resultados[a]["tempo_total_ms"])
    menor_overhead = min(resultados, key=lambda a: resultados[a]["overhead_bytes"])

    print("\nANÁLISE QUALITATIVA")
    print("-" * 90)

    for algo in listar_algoritmos():
        info = INFO_ALGORITMOS[algo]
        print(f"\n[{info['nome']}]")
        print(f"  Segurança:    {info['seguranca']}")
        print(f"  Complexidade: {info['complexidade']}")
        print(f"  Uso em IoT:   {info['uso_iot']}")

    print("\n" + "-" * 90)
    print("CONCLUSÕES PARA O CENÁRIO DE SEMÁFORO INTELIGENTE")
    print("-" * 90)
    print(
        f"• Mais rápido neste teste: {INFO_ALGORITMOS[mais_rapido]['nome']} "
        f"({resultados[mais_rapido]['tempo_total_ms']:.4f} ms/op)"
    )
    print(
        f"• Menor overhead de pacote: {INFO_ALGORITMOS[menor_overhead]['nome']} "
        f"(+{resultados[menor_overhead]['overhead_bytes']} bytes)"
    )
    print("• Recomendado para produção IoT: AES-128 ou ChaCha20-Poly1305")
    print("• 3DES e Blowfish: apenas legado; não recomendados em novos deployments")
    print("• Algoritmo padrão do simulador: AES-128-EAX (confidencialidade + autenticação AEAD)")


def main():
    resultados = {}
    for algoritmo in listar_algoritmos():
        resultados[algoritmo] = medir_algoritmo(algoritmo)

    imprimir_tabela(resultados)
    imprimir_analise(resultados)


if __name__ == "__main__":
    main()
