"""Servidor HTTP leve para servir dados JSON ao frontend SIEM."""

import json
import http.server
import os
from pathlib import Path

from config import CAMINHO_LOG_JSON, RAIZ

PORTA_SIEM = 8090


class ServidorSIEM(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RAIZ / "siem" / "out"), **kwargs)

    def do_GET(self):
        if self.path == "/api/log":
            self._servir_log()
        else:
            super().do_GET()

    def _servir_log(self):
        entradas = []
        try:
            if CAMINHO_LOG_JSON.exists():
                with open(CAMINHO_LOG_JSON, "r", encoding="utf-8") as f:
                    linhas = f.read().strip().split("\n")
                    entradas = [json.loads(l) for l in linhas if l.strip()]
        except Exception:
            pass

        ataques = [e for e in entradas if
                    e.get("classificacao", "").startswith("MITM") or
                    e.get("classificacao") == "DISPOSITIVO_NAO_CADASTRADO"]
        ambulancias = [e for e in entradas if e.get("tipo") == "PRESENCA_AMBULANCIA"]
        autenticos = [e for e in entradas if e.get("classificacao") == "AUTENTICO"]

        ultimo_estado = {}
        for e in autenticos:
            ts = e.get("timestamp_servidor", "")
            if e["device_id"] not in ultimo_estado or ts > ultimo_estado[e["device_id"]].get("timestamp_servidor", ""):
                ultimo_estado[e["device_id"]] = e

        resposta = {
            "total": len(entradas),
            "entradas": entradas[-50:][::-1],
            "ataques": ataques[-20:][::-1],
            "ambulancias": ambulancias[-5:][::-1],
            "dispositivos": ultimo_estado,
            "ultimo_ataque": ataques[-1] if ataques else None,
            "ambulancia_ativa": ambulancias[-1] if ambulancias else None,
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(resposta, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass


def iniciar_servidor_siem(porta: int = PORTA_SIEM):
    from functools import partial
    handler = partial(ServidorSIEM)
    servidor = http.server.HTTPServer(("0.0.0.0", porta), handler)
    print(f"[SIEM-HTTP] Servidor do painel SIEM em http://localhost:{porta}")
    return servidor
