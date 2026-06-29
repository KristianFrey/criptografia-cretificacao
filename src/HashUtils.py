import hashlib
import json
import os
from pathlib import Path

CAMINHO_USUARIOS = Path(__file__).resolve().parent.parent / "dados" / "usuarios.json"


def gerar_hash(mensagem):
    return hashlib.sha256(mensagem.encode()).hexdigest()

def _carregar_usuarios():
    if CAMINHO_USUARIOS.exists():
        return json.loads(CAMINHO_USUARIOS.read_text())
    return {}


def _salvar_usuarios(usuarios):
    CAMINHO_USUARIOS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_USUARIOS.write_text(json.dumps(usuarios, indent=2))


def registrar_usuario(usuario, senha):
    usuarios = _carregar_usuarios()
    if usuario in usuarios:
        return False, "Usuario ja existe"
    salt = os.urandom(16).hex()
    hash_senha = gerar_hash(salt + senha)
    usuarios[usuario] = {"salt": salt, "hash": hash_senha}
    _salvar_usuarios(usuarios)
    return True, "Registrado com sucesso"


def autenticar_usuario(usuario, senha):
    usuarios = _carregar_usuarios()
    if usuario not in usuarios:
        return False, "Usuario nao encontrado"
    entry = usuarios[usuario]
    if gerar_hash(entry["salt"] + senha) == entry["hash"]:
        return True, "Autenticado"
    return False, "Senha invalida"