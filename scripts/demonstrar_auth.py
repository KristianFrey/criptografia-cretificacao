"""
Desafio Extra (Tarefa 3) — Autenticacao login/senha com hash SHA-256.
Uso: python scripts/demonstrar_auth.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from HashUtils import registrar_usuario, autenticar_usuario, CAMINHO_USUARIOS


def main():
    print("=" * 60)
    print("  DESAFIO EXTRA — Autenticacao com Hash (SHA-256 + Salt)")
    print("=" * 60)

    if CAMINHO_USUARIOS.exists():
        CAMINHO_USUARIOS.unlink()

    print("\n[1] Registrando usuario 'admin' com senha 's3nh@forte'...")
    ok, msg = registrar_usuario("admin", "s3nh@forte")
    print(f"    {msg}")

    print("\n[2] Registrando usuario 'operator' com senha 'iot2027'...")
    ok, msg = registrar_usuario("operator", "iot2027")
    print(f"    {msg}")

    print("\n[3] Tentando registrar 'admin' novamente (deve falhar)...")
    ok, msg = registrar_usuario("admin", "outra_senha")
    print(f"    {msg}")

    print("\n[4] Login correto: admin / s3nh@forte...")
    ok, msg = autenticar_usuario("admin", "s3nh@forte")
    print(f"    {msg} {'OK' if ok else 'FALHOU'}")

    print("\n[5] Login errado: admin / senha_errada...")
    ok, msg = autenticar_usuario("admin", "senha_errada")
    print(f"    {msg} {'(rejeitado correto)' if not ok else 'FALHOU - deveria rejeitar'}")

    print("\n[6] Login: usuario inexistente...")
    ok, msg = autenticar_usuario("nao_existe", "qualquer")
    print(f"    {msg}")

    print("\n[7] Login correto: operator / iot2027...")
    ok, msg = autenticar_usuario("operator", "iot2027")
    print(f"    {msg} {'OK' if ok else 'FALHOU'}")

    print("\n" + "-" * 60)
    print("ARMAZENAMENTO (dados/usuarios.json):")
    print("-" * 60)
    print(CAMINHO_USUARIOS.read_text())

    print("-" * 60)
    print("RESUMO")
    print("-" * 60)
    print("• Senhas armazenadas como: SHA-256(salt + senha)")
    print("• Salt: 16 bytes aleatorios por usuario (os.urandom)")
    print("• Mesma senha gera hash diferente (protecao contra rainbow tables)")
    print("• Em producao: usar bcrypt/scrypt/argon2 (estas funcoes usam")
    print("  SHA-256 por didatica, conforme o edital pede hash criptografico)")


if __name__ == "__main__":
    main()
