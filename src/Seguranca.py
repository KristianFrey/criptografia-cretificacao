import time
from collections import defaultdict
from datetime import datetime


class NGFW:
    def __init__(self):
        self.whitelist = set()
        self.blacklist = set()
        self.lista_mac = set()
        self.portas_bloqueadas = {22, 23}
        self.politica = "negar-padrao"

    def adicionar_whitelist(self, device_id):
        self.whitelist.add(device_id)

    def adicionar_blacklist(self, device_id):
        self.blacklist.add(device_id)

    def adicionar_mac(self, mac):
        self.lista_mac.add(mac)

    def verificar_dispositivo(self, device_id, mac=None):
        if device_id in self.blacklist:
            return False, f"BLOQUEADO: {device_id} na blacklist"
        if self.politica == "negar-padrao" and device_id not in self.whitelist:
            return False, f"NEGADO: {device_id} nao autorizado"
        if mac and self.lista_mac and mac not in self.lista_mac:
            return False, f"NEGADO: MAC {mac} nao esta na whitelist — possivel dispositivo clonado"
        return True, "PERMITIDO"


class ProxyReverso:
    def __init__(self, limite_taxa=5):
        self.contador_requisicoes = defaultdict(list)
        self.limite_taxa = limite_taxa
        self.ip_proxy = "10.0.0.1"

    def anonimizar(self, pacote):
        pacote["proxy_ip"] = self.ip_proxy
        pacote["origem_anonimizada"] = True
        return pacote

    def verificar_limite_taxa(self, device_id):
        agora = time.time()
        self.contador_requisicoes[device_id] = [
            t for t in self.contador_requisicoes[device_id] if agora - t < 1
        ]
        if len(self.contador_requisicoes[device_id]) >= self.limite_taxa:
            return False
        self.contador_requisicoes[device_id].append(agora)
        return True


class IDS:
    def __init__(self):
        self.alertas = []
        self.janela_pacotes = defaultdict(list)
        self.segundos_janela = 10
        self.limiar_dos = 5
        self.estados_validos = {"VERDE", "AMARELO", "VERMELHO"}
        self.modos_validos = {"NORMAL", "EMERGENCIA", "MANUTENCAO"}
        self.estado_anterior = {}
        self.carros_anteriores = {}

    def analisar_nids(self, pacote):
        device_id = pacote.get("device_id", "desconhecido")
        agora = time.time()
        self.janela_pacotes[device_id] = [
            t for t in self.janela_pacotes[device_id] if agora - t < self.segundos_janela
        ]
        self.janela_pacotes[device_id].append(agora)
        if len(self.janela_pacotes[device_id]) > self.limiar_dos:
            msg = f"Possivel DoS: {len(self.janela_pacotes[device_id])} pacotes em {self.segundos_janela}s"
            self._alertar("NIDS", device_id, "ATAQUE_DOS", msg)
            return False
        return True

    def analisar_hids(self, pacote):
        device_id = pacote.get("device_id", "desconhecido")
        dados = pacote.get("dados", {})
        estado = dados.get("estado", "")
        carros = dados.get("carros", 0)
        modo = dados.get("modo", "NORMAL")
        tempo_fase = dados.get("tempo_fase_seg", 0)
        fila = dados.get("fila_metros", 0)

        if modo not in self.modos_validos:
            self._alertar("HIDS", device_id, "MODO_INVALIDO",
                          f"Modo operacional invalido: {modo}")
            return False

        if not (5 <= tempo_fase <= 300):
            self._alertar("HIDS", device_id, "TEMPO_FASE_INVALIDO",
                          f"Tempo de fase fora do padrao: {tempo_fase}s")
            return False

        if fila < 0 or fila > 500:
            self._alertar("HIDS", device_id, "FILA_INCONSISTENTE",
                          f"Fila inconsistente: {fila}m")
            return False

        if estado not in self.estados_validos:
            self._alertar("HIDS", device_id, "ESTADO_INVALIDO",
                          f"Estado invalido: {estado}")
            return False

        prev_estado = self.estado_anterior.get(device_id)
        if prev_estado and prev_estado == "VERDE" and estado == "VERMELHO":
            self._alertar("HIDS", device_id, "TRANSICAO_IRREGULAR",
                          f"Transicao irregular: {prev_estado} -> {estado} (sem AMARELO)")
            return False
        self.estado_anterior[device_id] = estado

        prev_carros = self.carros_anteriores.get(device_id)
        if prev_carros is not None and abs(carros - prev_carros) > 40:
            self._alertar("HIDS", device_id, "PICO_CARROS",
                          f"Variacao abrupta de veiculos: {prev_carros} -> {carros}")
            return False
        self.carros_anteriores[device_id] = carros

        return True

    def _alertar(self, tipo, device_id, gravidade, mensagem):
        alerta = {
            "tipo": tipo,
            "device_id": device_id,
            "gravidade": gravidade,
            "mensagem": mensagem,
            "timestamp": datetime.now().isoformat()
        }
        self.alertas.append(alerta)
        print(f"\n  [IDS:{tipo}] ALERTA {gravidade}: {mensagem}")


class SIEM:
    def __init__(self, ngfw, ao_alertar_atms=None):
        self.ngfw = ngfw
        self.registros = []
        self.ao_alertar_atms = ao_alertar_atms

    def ingerir(self, origem, evento, eh_alerta=False):
        self.registros.append({
            "origem": origem,
            "evento": evento,
            "eh_alerta": eh_alerta,
            "timestamp": datetime.now().isoformat()
        })
        if eh_alerta:
            self._correlacionar()

    def _correlacionar(self):
        recentes = [r for r in self.registros if r.get("eh_alerta") and
                    (datetime.now() - datetime.fromisoformat(r["timestamp"])).total_seconds() < 30]
        dispositivos = defaultdict(set)
        for r in recentes:
            ev = r["evento"]
            if isinstance(ev, dict):
                did = ev.get("device_id", "desconhecido")
            else:
                did = "desconhecido"
            dispositivos[did].add(r["origem"])

        for dispositivo, origens in dispositivos.items():
            if len(origens) >= 2 and dispositivo != "desconhecido":
                print(f"\n  [SIEM] CORRELACAO: {len(origens)} fontes reportando anomalias em {dispositivo}")
                print(f"  [SIEM] Ameaca critica confirmada - orquestrando resposta automatizada")
                self._resposta_automatizada(dispositivo, list(origens))

    def _resposta_automatizada(self, device_id, origens=None):
        print(f"  [SIEM] Resposta: Despachando comando para NGFW bloquear {device_id}")
        self.ngfw.adicionar_blacklist(device_id)
        if self.ao_alertar_atms:
            self.ao_alertar_atms(
                device_id,
                origens or [],
                "Ameaca critica correlacionada — dispositivo bloqueado automaticamente",
            )
