# Semáforos Inteligentes — Segurança em IoT (Trabalho 3)

**Disciplina:** Segurança em IoT · **Cenário:** Smart Cities · **Equipe:** Julio Becker, João Winkelmann, Kristian Frey

## Estrutura do projeto

```
Criptografia/
├── src/          → simulador (servidor + dispositivo)
├── scripts/      → demos e provisionamento
├── dados/        → certificados, chaves, logs
└── docs/         → documentação + PDF do T2
```

Detalhes: [docs/ESTRUTURA.md](docs/ESTRUTURA.md)

## Configuração

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python scripts/provisionar_rede.py
```

## Executar simulador

```powershell
# Terminal 1 — Servidor (broker MQTT + validações T2/T3)
cd src
python Servidor.py

# Terminal 2 — Semáforo A1
cd src
python DispositivoSemaforo.py SEMAFORO_A1

# Terminal 3 (opcional) — Semáforo B2
cd src
python DispositivoSemaforo.py SEMAFORO_B2
```

## Scripts (`scripts/`)

| Script | Descrição |
|--------|-----------|
| `provisionar_rede.py` | CA + certificados A1 e B2 |
| `gerar_certificado.py` | Emite certificado de um dispositivo |
| `distribuir_certificado.py` | Simula provisionamento seguro (PSK) |
| `ler_certificado.py` | Exibe metadados X.509 |
| `comparar_criptografia.py` | Benchmark AES, ChaCha20, 3DES, Blowfish |
| `demonstrar_assinatura.py` | Testes de assinatura RSA |

## Documentação

- [Cenário T2 + T3](docs/Cenario-T2-T3.md)
- [Certificados e MitM](docs/Tarefa4-Certificados-MitM.md)
- [Protocolo STSP / MQTT](docs/Tarefa6-ProtocoloMQTT.md)
- PDF Trabalho 2: `docs/referencias/`

## Produção vs. simulador

| Item | Simulador | Trabalho 2 (produção) |
|------|-----------|------------------------|
| MQTT | `1883` + broker embarcado | `8883` TLS na DMZ |
| IDS/SIEM | `src/Seguranca.py` | Snort + Wazuh |
