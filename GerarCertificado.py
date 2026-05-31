from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

# gerar chave privada
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# salvar chave privada
with open("chaves/private_cert.pem", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# certificado
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "RS"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Santa Cruz do Sul"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SmartTraffic"),
    x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IoT"),
    x509.NameAttribute(NameOID.COMMON_NAME, "SEMAFORO_A1"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .sign(private_key, hashes.SHA256())
)

# salvar certificado
with open("certificados/certificado.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Certificado criado com sucesso!")