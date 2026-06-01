# Alinhamento Trabalho 2 (cenário) + Trabalho 3 (implementação)

Baseado no PDF **Semáforos Inteligentes — Trabalho 2** e no código STSP/MQTT.

## Continuidade entre trabalhos

```
Trabalho 1 — Ameaças e superfície de ataque
    ↓
Trabalho 2 — NGFW, DMZ, Proxy, IDS (Snort/Wazuh), SIEM, MQTT/TLS
    ↓
Trabalho 3 — STSP: confidencialidade, integridade, autenticidade (certificado + assinatura)
```

## Superfície de ataque → defesas

| Superfície (PDF T2) | Defesa T2 | Defesa T3 (código) |
|---------------------|-----------|---------------------|
| Dispositivos IoT expostos | NGFW whitelist | Certificado X.509 por semáforo |
| Comunicação MQTT / sem fio | DMZ, MQTT TLS **8883** | AES-128-EAX no payload STSP |
| Controladores Edge | Forward proxy, cache | `DispositivoSemaforo.py` + telemetria rica |
| APIs / dashboard ATMS | Proxy reverso, HTTPS 443 | Tópico `smarttraffic/v1/atms/alertas` |
| Cloud/Fog | SIEM Wazuh | `Servidor.py` + correlação `MockSIEM` |
| Tampering de dados | IDS HIDS | SHA-256 + assinatura RSA |
| Dispositivo falso | Default deny | Assinatura com chave do certificado |
| DoS no broker MQTT | Snort NIDS | `MockIDS` + correlação SIEM → bloqueio NGFW |

## Mapeamento de componentes

| Componente PDF | Simulação no projeto |
|----------------|----------------------|
| Broker MQTT (DMZ) | `BrokerMQTT.py` — porta 1883 |
| NGFW borda | `MockNGFW` |
| Proxy reverso | `MockReverseProxy` |
| Snort (NIDS) | `MockIDS.analyze_nids` |
| Wazuh (HIDS) | `MockIDS.analyze_hids` |
| Wazuh SIEM | `MockSIEM` |
| Dashboard ATMS | assinante do tópico `atms/alertas` |
| Semáforos A1, B2… | `SEMAFORO_A1`, `SEMAFORO_B2` |
| FIWARE / NGSI | não implementado (escopo futuro) |

## Fluxo de incidente (PDF página SIEM)

1. NIDS detecta possível DoS MQTT → alerta  
2. SIEM correlaciona com evento `MQTT_BROKER`  
3. Classifica ameaça crítica → bloqueia no NGFW  
4. Publica alerta no tópico ATMS  

## Limitações declaradas na apresentação

- Broker local **sem TLS**; em produção STSP roda sobre **MQTT/TLS 8883**.  
- Snort/Wazuh são **simulados** com as mesmas políticas do T2.  
- Arquitetura Edge→Fog→Cloud **simplificada** em dois processos Python.  
