from cryptography import x509

with open("certificados/certificado.pem", "rb") as f:
    cert = x509.load_pem_x509_certificate(f.read())

print("Subject:")
print(cert.subject)

print("\nIssuer:")
print(cert.issuer)

print("\nVálido até:")
print(cert.not_valid_after)

print("\nNúmero serial:")
print(cert.serial_number)