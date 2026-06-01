"""
Tarefa 4 — Certificados digitais para dispositivos IoT (Semáforo Inteligente).

Autoridade emissora simulada: SmartTraffic IoT CA
Metadados obrigatórios no certificado: Device ID, chave pública, validade, emissor.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID, ExtensionOID

# OID privado para Device ID em certificados IoT do projeto
DEVICE_ID_OID = x509.ObjectIdentifier("1.3.6.1.4.1.37459.1.1")

AUTORIDADE_EMISSORA = "SmartTraffic IoT CA"
DIAS_VALIDADE_CA = 3650
DIAS_VALIDADE_DISPOSITIVO = 365

from config import (
    PASTA_CERTIFICADOS,
    PASTA_CHAVES,
    PASTA_DISPOSITIVOS,
    PASTA_CA,
    PASTA_EMITIDOS,
    CAMINHO_CA_CERT,
    CAMINHO_CA_PRIVADA,
    garantir_estrutura_dados,
)


def _garantir_pastas():
    garantir_estrutura_dados()


def _nome_emissor_ca():
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "RS"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Santa Cruz do Sul"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SmartTraffic"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IoT CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, AUTORIDADE_EMISSORA),
    ])


def _nome_dispositivo(device_id: str):
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SmartTraffic"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Dispositivo IoT"),
        x509.NameAttribute(NameOID.COMMON_NAME, device_id),
    ])


def _agora_utc():
    return datetime.now(timezone.utc)


def gerar_autoridade_certificadora():
    """Gera a CA simulada (par de chaves + certificado autoassinado da CA)."""
    _garantir_pastas()

    chave_ca = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    emissor = _nome_emissor_ca()
    agora = _agora_utc()

    cert_ca = (
        x509.CertificateBuilder()
        .subject_name(emissor)
        .issuer_name(emissor)
        .public_key(chave_ca.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + timedelta(days=DIAS_VALIDADE_CA))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(chave_ca, hashes.SHA256())
    )

    with open(CAMINHO_CA_PRIVADA, "wb") as f:
        f.write(
            chave_ca.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(CAMINHO_CA_CERT, "wb") as f:
        f.write(cert_ca.public_bytes(serialization.Encoding.PEM))

    return cert_ca, chave_ca


def emitir_certificado_dispositivo(device_id: str, chave_privada=None):
    """
    Emite certificado do dispositivo assinado pela CA simulada.
    Metadados: Device ID (extensão), chave pública, validade, autoridade emissora.
    """
    _garantir_pastas()

    if not CAMINHO_CA_CERT.exists() or not CAMINHO_CA_PRIVADA.exists():
        gerar_autoridade_certificadora()

    with open(CAMINHO_CA_CERT, "rb") as f:
        cert_ca = x509.load_pem_x509_certificate(f.read())

    with open(CAMINHO_CA_PRIVADA, "rb") as f:
        chave_ca = serialization.load_pem_private_key(f.read(), password=None)

    if chave_privada is None:
        chave_privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    agora = _agora_utc()
    caminho_privada = PASTA_CHAVES / f"{device_id}_private.pem"
    caminho_cert = PASTA_EMITIDOS / f"{device_id}.pem"

    cert_dispositivo = (
        x509.CertificateBuilder()
        .subject_name(_nome_dispositivo(device_id))
        .issuer_name(cert_ca.subject)
        .public_key(chave_privada.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + timedelta(days=DIAS_VALIDADE_DISPOSITIVO))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(f"{device_id.lower()}.smarttraffic.local"),
            ]),
            critical=False,
        )
        .add_extension(
            x509.UnrecognizedExtension(DEVICE_ID_OID, device_id.encode("utf-8")),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=False,
                data_encipherment=False,
                key_cert_sign=False,
                crl_sign=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(chave_ca, hashes.SHA256())
    )

    with open(caminho_privada, "wb") as f:
        f.write(
            chave_privada.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(caminho_cert, "wb") as f:
        f.write(cert_dispositivo.public_bytes(serialization.Encoding.PEM))

    return cert_dispositivo, chave_privada, caminho_cert, caminho_privada


def carregar_certificado(caminho: Path):
    with open(caminho, "rb") as f:
        return x509.load_pem_x509_certificate(f.read())


def extrair_device_id(cert: x509.Certificate) -> str:
    try:
        ext = cert.extensions.get_extension_for_oid(DEVICE_ID_OID)
        return ext.value.value.decode("utf-8")
    except x509.ExtensionNotFound:
        return cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value


def extrair_metadados(cert: x509.Certificate) -> dict:
    pub = cert.public_key()
    numeros = pub.public_numbers()
    fingerprint = cert.fingerprint(hashes.SHA256()).hex()

    return {
        "device_id": extrair_device_id(cert),
        "autoridade_emissora": cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
        "valido_de": cert.not_valid_before_utc.isoformat(),
        "valido_ate": cert.not_valid_after_utc.isoformat(),
        "serial": str(cert.serial_number),
        "chave_publica_modulo_bits": numeros.n.bit_length(),
        "chave_publica_expoente": numeros.e,
        "chave_publica_fingerprint_sha256": fingerprint,
    }


def caminhos_dispositivo(device_id: str):
    pasta = PASTA_DISPOSITIVOS / device_id
    return {
        "pasta": pasta,
        "certificado": pasta / "certificado.pem",
        "chave_privada": pasta / "private.pem",
    }


def caminhos_emissao(device_id: str):
    return {
        "certificado": PASTA_EMITIDOS / f"{device_id}.pem",
        "chave_privada": PASTA_CHAVES / f"{device_id}_private.pem",
    }


def verificar_certificado(cert: x509.Certificate, device_id_esperado: str = None) -> tuple[bool, str]:
    """Valida cadeia (CA), validade temporal e Device ID."""
    if not CAMINHO_CA_CERT.exists():
        return False, "CA de confiança não encontrada"

    cert_ca = carregar_certificado(CAMINHO_CA_CERT)
    agora = _agora_utc()

    if agora < cert.not_valid_before_utc:
        return False, "Certificado ainda não é válido"

    if agora > cert.not_valid_after_utc:
        return False, "Certificado expirado"

    try:
        cert_ca.public_key().verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            padding.PKCS1v15(),
            cert.signature_hash_algorithm,
        )
    except Exception:
        return False, "Assinatura da CA inválida — certificado não confiável"

    device_id_cert = extrair_device_id(cert)
    if device_id_esperado and device_id_cert != device_id_esperado:
        return False, f"Device ID divergente: cert={device_id_cert}, pacote={device_id_esperado}"

    emissor = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    if emissor != AUTORIDADE_EMISSORA:
        return False, f"Emissor não autorizado: {emissor}"

    return True, "Certificado válido e confiável"


def obter_certificado_confiavel(device_id: str) -> x509.Certificate | None:
    """Carrega certificado da pasta do dispositivo ou do registro da CA."""
    caminhos_disp = caminhos_dispositivo(device_id)
    if caminhos_disp["certificado"].exists():
        return carregar_certificado(caminhos_disp["certificado"])

    caminhos = caminhos_emissao(device_id)
    if caminhos["certificado"].exists():
        return carregar_certificado(caminhos["certificado"])

    return None
