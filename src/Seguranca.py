import time
from collections import defaultdict
from datetime import datetime


class MockNGFW:
    def __init__(self):
        self.whitelist = set()
        self.blacklist = set()
        self.blocked_ports = {22, 23}
        self.policy = "default-deny"

    def add_to_whitelist(self, device_id):
        self.whitelist.add(device_id)

    def add_to_blacklist(self, device_id):
        self.blacklist.add(device_id)

    def check_device(self, device_id):
        if device_id in self.blacklist:
            return False, f"BLACKLISTED: {device_id}"
        if self.policy == "default-deny" and device_id not in self.whitelist:
            return False, f"DEFAULT_DENY: {device_id} nao autorizado"
        return True, "ALLOWED"


class MockReverseProxy:
    def __init__(self, rate_limit=5):
        self.request_counts = defaultdict(list)
        self.rate_limit = rate_limit
        self.proxy_ip = "10.0.0.1"

    def anonymize(self, pacote):
        pacote["proxy_ip"] = self.proxy_ip
        pacote["source_anonymized"] = True
        return pacote

    def check_rate_limit(self, device_id):
        now = time.time()
        self.request_counts[device_id] = [
            t for t in self.request_counts[device_id] if now - t < 1
        ]
        if len(self.request_counts[device_id]) >= self.rate_limit:
            return False
        self.request_counts[device_id].append(now)
        return True


class MockIDS:
    def __init__(self):
        self.alerts = []
        self.packet_window = defaultdict(list)
        self.window_seconds = 10
        self.dos_threshold = 5
        self.valid_states = {"VERDE", "AMARELO", "VERMELHO"}
        self.prev_state = {}
        self.prev_carros = {}

    def analyze_nids(self, pacote):
        device_id = pacote.get("device_id", "unknown")
        now = time.time()
        self.packet_window[device_id] = [
            t for t in self.packet_window[device_id] if now - t < self.window_seconds
        ]
        self.packet_window[device_id].append(now)
        if len(self.packet_window[device_id]) > self.dos_threshold:
            msg = f"Possivel DoS: {len(self.packet_window[device_id])} pacotes em {self.window_seconds}s"
            self._alert("NIDS", device_id, "DOS_ATTACK", msg)
            return False
        return True

    def analyze_hids(self, pacote):
        device_id = pacote.get("device_id", "unknown")
        dados = pacote.get("dados", {})
        estado = dados.get("estado", "")
        carros = dados.get("carros", 0)

        if estado not in self.valid_states:
            self._alert("HIDS", device_id, "INVALID_STATE",
                        f"Estado invalido: {estado}")
            return False

        prev_estado = self.prev_state.get(device_id)
        if prev_estado and prev_estado == "VERDE" and estado == "VERMELHO":
            self._alert("HIDS", device_id, "ILLEGAL_TRANSITION",
                        f"Transicao irregular: {prev_estado} -> {estado} (sem AMARELO)")
            return False
        self.prev_state[device_id] = estado

        prev_carros = self.prev_carros.get(device_id)
        if prev_carros is not None and abs(carros - prev_carros) > 40:
            self._alert("HIDS", device_id, "CARROS_SPIKE",
                        f"Variacao abrupta de veiculos: {prev_carros} -> {carros}")
            return False
        self.prev_carros[device_id] = carros

        return True

    def _alert(self, tipo, device_id, severity, message):
        alerta = {
            "tipo": tipo,
            "device_id": device_id,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.alerts.append(alerta)
        print(f"\n  [IDS:{tipo}] ALERTA {severity}: {message}")


class MockSIEM:
    def __init__(self, ngfw):
        self.ngfw = ngfw
        self.logs = []

    def ingest(self, source, event, is_alert=False):
        self.logs.append({
            "source": source,
            "event": event,
            "is_alert": is_alert,
            "timestamp": datetime.now().isoformat()
        })
        if is_alert:
            self._correlate()

    def _correlate(self):
        recent = [l for l in self.logs if l.get("is_alert") and
                  (datetime.now() - datetime.fromisoformat(l["timestamp"])).total_seconds() < 30]
        devices = defaultdict(set)
        for log in recent:
            ev = log["event"]
            if isinstance(ev, dict):
                did = ev.get("device_id", "unknown")
            else:
                did = "unknown"
            devices[did].add(log["source"])

        for device, sources in devices.items():
            if len(sources) >= 2 and device != "unknown":
                print(f"\n  [SIEM] CORRELACAO: {len(sources)} fontes reportando anomalias em {device}")
                print(f"  [SIEM] Ameaca critica confirmada - orquestrando resposta automatizada")
                self._automated_response(device)

    def _automated_response(self, device_id):
        print(f"  [SIEM] Resposta: Despachando comando para NGFW bloquear {device_id}")
        self.ngfw.add_to_blacklist(device_id)
