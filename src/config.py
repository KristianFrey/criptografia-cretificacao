"""
Caminhos centralizados do projeto SmartTraffic.
Todos os módulos devem importar pastas daqui.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PASTA_SRC = RAIZ / "src"
PASTA_SCRIPTS = RAIZ / "scripts"
PASTA_DOCS = RAIZ / "docs"

PASTA_DADOS = RAIZ / "dados"
PASTA_CHAVES = PASTA_DADOS / "chaves"
PASTA_CERTIFICADOS = PASTA_DADOS / "certificados"
PASTA_DISPOSITIVOS = PASTA_DADOS / "dispositivos"
PASTA_LOGS = PASTA_DADOS / "logs"

PASTA_CA = PASTA_CERTIFICADOS / "ca"
PASTA_EMITIDOS = PASTA_CERTIFICADOS / "emitidos"

CAMINHO_CA_CERT = PASTA_CA / "ca.pem"
CAMINHO_CA_PRIVADA = PASTA_CHAVES / "ca_private.pem"
CAMINHO_LOG_SERVIDOR = PASTA_LOGS / "servidor.log"
CAMINHO_LOG_JSON = PASTA_LOGS / "servidor.jsonl"

DISPOSITIVOS_PADRAO = {
    "SEMAFORO_A1": {
        "tipo": "semaforo",
        "mac": "AA:BB:CC:DD:01:A1",
        "cruzamento": "CRUZAMENTO_ALPHA",
    },
    "SEMAFORO_B2": {
        "tipo": "semaforo",
        "mac": "AA:BB:CC:DD:02:B2",
        "cruzamento": "CRUZAMENTO_ALPHA",
    },
    "AMBULANCIA_E1": {
        "tipo": "ambulancia",
        "mac": "AA:BB:CC:DD:03:E1",
        "cruzamento": None,
    },
}

MAC_WHITELIST = {d["mac"] for d in DISPOSITIVOS_PADRAO.values()}


def garantir_estrutura_dados():
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


def mac_autorizado(mac: str) -> bool:
    return mac in MAC_WHITELIST
