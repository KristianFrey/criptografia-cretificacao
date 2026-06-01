"""
Caminhos centralizados do projeto SmartTraffic.
Todos os módulos devem importar pastas daqui.
"""

from pathlib import Path

# Raiz do repositório (pasta Criptografia/)
RAIZ = Path(__file__).resolve().parent.parent

# Código e documentação
PASTA_SRC = RAIZ / "src"
PASTA_SCRIPTS = RAIZ / "scripts"
PASTA_DOCS = RAIZ / "docs"

# Dados sensíveis e gerados (não versionar — ver .gitignore)
PASTA_DADOS = RAIZ / "dados"
PASTA_CHAVES = PASTA_DADOS / "chaves"
PASTA_CERTIFICADOS = PASTA_DADOS / "certificados"
PASTA_DISPOSITIVOS = PASTA_DADOS / "dispositivos"
PASTA_LOGS = PASTA_DADOS / "logs"

# Subpastas de certificados
PASTA_CA = PASTA_CERTIFICADOS / "ca"
PASTA_EMITIDOS = PASTA_CERTIFICADOS / "emitidos"

CAMINHO_CA_CERT = PASTA_CA / "ca.pem"
CAMINHO_CA_PRIVADA = PASTA_CHAVES / "ca_private.pem"
CAMINHO_LOG_SERVIDOR = PASTA_LOGS / "servidor.log"


def garantir_estrutura_dados():
    """Cria pastas de dados se não existirem."""
    for pasta in (
        PASTA_DADOS,
        PASTA_CHAVES,
        PASTA_CERTIFICADOS,
        PASTA_CA,
        PASTA_EMITIDOS,
        PASTA_DISPOSITIVOS,
        PASTA_LOGS,
    ):
        pasta.mkdir(parents=True, exist_ok=True)
