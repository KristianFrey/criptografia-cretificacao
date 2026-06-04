from Crypto.Cipher import AES, ChaCha20_Poly1305, DES3, Blowfish
import base64

# chaves simétricas por algoritmo (simulador IoT — cenário semáforo)
CHAVES = {
    "aes": b"1234567890123456",              # AES-128: 16 bytes
    "chacha20": b"0" * 32,                   # ChaCha20: 256 bits
    "des3": b"123456789012345678901234",     # 3DES: 24 bytes
    "blowfish": b"1234567890123456",         # Blowfish: 16 bytes
}

ALGORITMO_PADRAO = "aes"

# tamanhos de nonce e tag por algoritmo (modo EAX / AEAD)
_FORMATO = {
    "aes": {"nonce": 16, "tag": 16},
    "chacha20": {"nonce": 12, "tag": 16},
    "des3": {"nonce": 16, "tag": 8},
    "blowfish": {"nonce": 16, "tag": 8},
}

# metadados para comparação (Tarefa 2)
INFO_ALGORITMOS = {
    "aes": {
        "nome": "AES-128-EAX",
        "tamanho_chave_bits": 128,
        "seguranca": "Alta — padrão NIST, amplamente adotado em IoT e TLS",
        "complexidade": "Média — acelerado por hardware (AES-NI) em muitos chips",
        "uso_iot": "MQTT/TLS, Zigbee, LoRaWAN, dispositivos embarcados modernos",
    },
    "chacha20": {
        "nome": "ChaCha20-Poly1305",
        "tamanho_chave_bits": 256,
        "seguranca": "Alta — resistente a timing attacks, adotado em TLS 1.3",
        "complexidade": "Baixa em software — ideal para MCUs sem AES-NI",
        "uso_iot": "Dispositivos de baixo custo, Google IoT, WireGuard, TLS moderno",
    },
    "des3": {
        "nome": "3DES-EDE-EAX",
        "tamanho_chave_bits": 168,
        "seguranca": "Moderada — obsoleto (NIST deprecou em 2023), vulnerável a Sweet32",
        "complexidade": "Alta — 3 rodadas DES, lento e pouco eficiente em IoT",
        "uso_iot": "Legado industrial/financeiro; evitar em novos projetos",
    },
    "blowfish": {
        "nome": "Blowfish-EAX",
        "tamanho_chave_bits": 128,
        "seguranca": "Moderada — seguro com chaves adequadas, bloco de 64 bits limita volume",
        "complexidade": "Média — simples de implementar, sem aceleração hardware comum",
        "uso_iot": "Sistemas legados embarcados; substituído por AES/ChaCha20",
    },
}


def _empacotar(algoritmo, dados_binarios):
    return f"{algoritmo}|{base64.b64encode(dados_binarios).decode()}"


def _desempacotar(mensagem_criptografada):
    algoritmo, payload_b64 = mensagem_criptografada.split("|", 1)
    return algoritmo, base64.b64decode(payload_b64)


def criptografar(mensagem, algoritmo=ALGORITMO_PADRAO):
    algoritmo = algoritmo.lower()
    dados = mensagem.encode()

    if algoritmo == "aes":
        cipher = AES.new(CHAVES["aes"], AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(dados)
        pacote = cipher.nonce + tag + ciphertext

    elif algoritmo == "chacha20":
        cipher = ChaCha20_Poly1305.new(key=CHAVES["chacha20"])
        ciphertext, tag = cipher.encrypt_and_digest(dados)
        pacote = cipher.nonce + tag + ciphertext

    elif algoritmo == "des3":
        cipher = DES3.new(CHAVES["des3"], DES3.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(dados)
        pacote = cipher.nonce + tag + ciphertext

    elif algoritmo == "blowfish":
        cipher = Blowfish.new(CHAVES["blowfish"], Blowfish.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(dados)
        pacote = cipher.nonce + tag + ciphertext

    else:
        raise ValueError(f"Algoritmo não suportado: {algoritmo}")

    return _empacotar(algoritmo, pacote)


def descriptografar(mensagem_criptografada, algoritmo=None):
    if algoritmo is None:
        algoritmo, pacote = _desempacotar(mensagem_criptografada)
    else:
        algoritmo = algoritmo.lower()
        _, pacote = _desempacotar(mensagem_criptografada)

    fmt = _FORMATO[algoritmo]
    nonce_len = fmt["nonce"]
    tag_len = fmt["tag"]

    nonce = pacote[:nonce_len]
    tag = pacote[nonce_len : nonce_len + tag_len]
    ciphertext = pacote[nonce_len + tag_len :]

    if algoritmo == "aes":
        cipher = AES.new(CHAVES["aes"], AES.MODE_EAX, nonce=nonce)
        dados = cipher.decrypt_and_verify(ciphertext, tag)

    elif algoritmo == "chacha20":
        cipher = ChaCha20_Poly1305.new(key=CHAVES["chacha20"], nonce=nonce)
        dados = cipher.decrypt_and_verify(ciphertext, tag)

    elif algoritmo == "des3":
        cipher = DES3.new(CHAVES["des3"], DES3.MODE_EAX, nonce=nonce)
        dados = cipher.decrypt_and_verify(ciphertext, tag)

    elif algoritmo == "blowfish":
        cipher = Blowfish.new(CHAVES["blowfish"], Blowfish.MODE_EAX, nonce=nonce)
        dados = cipher.decrypt_and_verify(ciphertext, tag)

    else:
        raise ValueError(f"Algoritmo não suportado: {algoritmo}")

    return dados.decode()


def listar_algoritmos():
    return list(CHAVES.keys())
