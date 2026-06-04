"""Geracao de telemetria realista para semaforos inteligentes (cenario Smart City)."""

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
        self._modo_forcado = None

    def definir_modo_emergencia(self, ativo: bool = True):
        self._modo_forcado = "EMERGENCIA" if ativo else None

    def _avancar_fase(self):
        self.estado = TRANSICOES[self.estado]
        self.tempo_fase_seg = {
            "VERDE": random.randint(30, 60),
            "AMARELO": random.randint(3, 8),
            "VERMELHO": random.randint(25, 50),
        }[self.estado]

    def proximo_pacote(self) -> dict:
        if self._modo_forcado:
            self.modo = self._modo_forcado
        elif random.random() < 0.25:
            self._avancar_fase()
            if random.random() < 0.02:
                self.modo = "EMERGENCIA"
            elif self.modo == "EMERGENCIA" and random.random() < 0.3:
                self.modo = "NORMAL"

        self.carros = max(0, min(50, self.carros + random.randint(-8, 12)))
        self.fila_metros = max(0, min(200, self.fila_metros + random.randint(-15, 20)))

        return {
            "carros": self.carros,
            "estado": self.estado,
            "tempo_fase_seg": self.tempo_fase_seg,
            "fila_metros": self.fila_metros,
            "modo": self.modo,
            "local": f"cruzamento_{self.device_id[-2:]}",
        }


class GeradorTelemetriaAmbulancia:
    """Simula deslocamento de ambulancia pela cidade."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.latitude = random.uniform(-23.55, -23.50)
        self.longitude = random.uniform(-46.63, -46.60)
        self.velocidade = 0
        self.direcao = random.choice(["NORTE", "SUL", "LESTE", "OESTE"])
        self.sirene_ativa = False

    def ativar_sirene(self):
        self.sirene_ativa = True
        self.velocidade = random.randint(60, 100)

    def desativar_sirene(self):
        self.sirene_ativa = False
        self.velocidade = random.randint(20, 40)

    def proximo_pacote(self) -> dict:
        if self.sirene_ativa:
            self.velocidade = max(60, self.velocidade + random.randint(-5, 5))
            delta_lat = random.uniform(-0.002, 0.002)
            delta_lon = random.uniform(-0.002, 0.002)
        else:
            self.velocidade = random.randint(0, 40)
            delta_lat = random.uniform(-0.0005, 0.0005)
            delta_lon = random.uniform(-0.0005, 0.0005)

        self.latitude += delta_lat
        self.longitude += delta_lon

        if random.random() < 0.1:
            self.direcao = random.choice(["NORTE", "SUL", "LESTE", "OESTE"])

        return {
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "velocidade": self.velocidade,
            "direcao": self.direcao,
            "sirene_ativa": self.sirene_ativa,
        }
