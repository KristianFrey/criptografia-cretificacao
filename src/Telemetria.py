"""Geração de telemetria realista para semáforos inteligentes (cenário Smart City)."""

import random

MODOS_VALIDOS = {"NORMAL", "EMERGENCIA", "MANUTENCAO"}
ESTADOS = ("VERDE", "AMARELO", "VERMELHO")
TRANSICOES = {
    "VERDE": "AMARELO",
    "AMARELO": "VERMELHO",
    "VERMELHO": "VERDE",
}


class GeradorTelemetria:
    """Simula sensor de contagem e controlador de fase na Edge."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.estado = "VERDE"
        self.carros = random.randint(5, 25)
        self.tempo_fase_seg = 45
        self.fila_metros = random.randint(0, 80)
        self.modo = "NORMAL"

    def _avancar_fase(self):
        self.estado = TRANSICOES[self.estado]
        self.tempo_fase_seg = {
            "VERDE": random.randint(30, 60),
            "AMARELO": random.randint(3, 8),
            "VERMELHO": random.randint(25, 50),
        }[self.estado]

    def proximo_pacote(self) -> dict:
        if random.random() < 0.25:
            self._avancar_fase()

        self.carros = max(0, min(50, self.carros + random.randint(-8, 12)))
        self.fila_metros = max(0, min(200, self.fila_metros + random.randint(-15, 20)))

        if random.random() < 0.02:
            self.modo = "EMERGENCIA"
        elif self.modo == "EMERGENCIA" and random.random() < 0.3:
            self.modo = "NORMAL"

        return {
            "carros": self.carros,
            "estado": self.estado,
            "tempo_fase_seg": self.tempo_fase_seg,
            "fila_metros": self.fila_metros,
            "modo": self.modo,
            "local": f"cruzamento_{self.device_id[-2:]}",
        }
