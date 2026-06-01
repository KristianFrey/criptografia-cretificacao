# Estrutura do projeto

```
Criptografia/
├── README.md                 # Início rápido
├── requirements.txt
├── docs/                     # Documentação e referências
│   ├── Cenario-T2-T3.md
│   ├── Tarefa4-Certificados-MitM.md
│   ├── Tarefa6-ProtocoloMQTT.md
│   ├── ESTRUTURA.md
│   └── referencias/          # PDF do Trabalho 2
├── dados/                    # Chaves, certificados, logs (gitignored)
├── scripts/                  # Utilitários e demonstrações
│   ├── provisionar_rede.py
│   ├── gerar_certificado.py
│   ├── distribuir_certificado.py
│   ├── ler_certificado.py
│   ├── comparar_criptografia.py
│   └── demonstrar_assinatura.py
└── src/                      # Código principal (simulador)
    ├── config.py             # Caminhos centralizados
    ├── Servidor.py           # Servidor Fog/Cloud + MQTT
    ├── DispositivoSemaforo.py
    ├── Protocolo.py          # STSP v1.0
    ├── Criptografia.py
    ├── HashUtils.py
    ├── Assinatura.py
    ├── Certificado.py
    ├── Telemetria.py
    ├── Seguranca.py          # NGFW, Proxy, IDS, SIEM (T2)
    └── BrokerMQTT.py
```

## Responsabilidades

| Pasta | Conteúdo |
|-------|----------|
| `src/` | Aplicação em execução contínua (dispositivo + servidor) |
| `scripts/` | Tarefas pontuais (certificados, benchmarks, demos) |
| `dados/` | Artefatos gerados e sensíveis |
| `docs/` | Textos para entrega e apresentação |
