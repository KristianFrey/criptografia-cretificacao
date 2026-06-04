# Tarefa 6 — SmartTraffic Secure Protocol (STSP) v1.0 sobre MQTT

## Visão geral

O **STSP** (SmartTraffic Secure Protocol) define como semáforos inteligentes enviam telemetria ao servidor central de forma segura, usando **MQTT** como camada de transporte IoT.

## Camadas de segurança

```
┌─────────────────────────────────────────┐
│  Transporte MQTT (QoS 1)                │  smarttraffic/v1/semaforo/{id}/telemetria
├─────────────────────────────────────────┤
│  Confidencialidade — AES-128-EAX        │  payload cifrado
├─────────────────────────────────────────┤
│  Autenticidade — RSA + certificado X.509│  assinatura digital
├─────────────────────────────────────────┤
│  Integridade — SHA-256                  │  hash dos dados
├─────────────────────────────────────────┤
│  Aplicação — JSON telemetria            │  carros, estado
└─────────────────────────────────────────┘
```

## Formato do pacote STSP (antes da cifragem)

```json
{
  "protocolo": "STSP",
  "versao": "1.0",
  "device_id": "SEMAFORO_A1",
  "timestamp": "2027-05-31T12:00:00",
  "dados": {"carros": 23, "estado": "VERDE"},
  "hash": "<sha256>",
  "assinatura": "<rsa-base64>",
  "criptografia": "aes"
}
```

O payload publicado no MQTT é o pacote JSON **cifrado** (`aes|base64...`).

## Tópicos MQTT

| Tópico | Direção | Descrição |
|--------|---------|-----------|
| `smarttraffic/v1/semaforo/{device_id}/telemetria` | Dispositivo → Servidor | Telemetria cifrada |
| `smarttraffic/v1/semaforo/+/telemetria` | Servidor (subscribe) | Wildcard para todos os semáforos |

- **QoS:** 1 (entrega pelo menos uma vez)
- **Broker:** embarcado local (`127.0.0.1:1883`) via `BrokerMQTT.py`
- **Produção (T2):** MQTT/TLS na porta **8883** na DMZ; STSP permanece como camada de aplicação
- **ATMS:** alertas SIEM em `smarttraffic/v1/atms/alertas`

## Fluxo dispositivo → servidor

1. Dispositivo monta pacote STSP (`Protocolo.montar_pacote`)
2. Calcula SHA-256 dos dados
3. Assina com chave privada do certificado
4. Cifra pacote com AES
5. Publica no tópico MQTT
6. Servidor decifra, valida certificado, NGFW, Proxy, IDS, hash, assinatura e timestamp

## Como executar

```powershell
# Terminal 1 — Servidor (inicia broker + assinante MQTT)
cd c:\desenv\Criptografia\src
..\venv\Scripts\python.exe Servidor.py

# Terminal 2 — Dispositivo semáforo
cd c:\desenv\Criptografia\src
..\venv\Scripts\python.exe DispositivoSemaforo.py
```

## Arquivos

| Arquivo | Função |
|---------|--------|
| `src/Protocolo.py` | Definição STSP, montagem e validação de pacotes |
| `src/BrokerMQTT.py` | Broker MQTT embarcado (amqtt) |
| `src/DispositivoSemaforo.py` | Publicador MQTT |
| `src/Servidor.py` | Assinante MQTT + pipeline de segurança |
