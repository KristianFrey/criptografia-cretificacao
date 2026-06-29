# Estrutura do projeto

```
criptografia-cretificacao/
├── Run.py                       # Orquestrador principal (executa tudo)
├── DemonstrarAssinatura.py      # Demo de assinatura (raiz)
├── requirements.txt             # Dependencias Python
├── README.md                    # Inicio rapido
├── TODO.md                      # Itens pendentes/concluidos
├── DOCUMENTACAO_COMPLETA.md     # Documentacao teknica completa
├── ativar_venv.sh               # Ativa o venv e entra em src/
├── src/                         # Codigo principal (simulador)
│   ├── config.py                # Caminhos centralizados, dispositivos, whitelist MAC
│   ├── Servidor.py              # Servidor central (validacao + logging JSON)
│   ├── ServidorSIEM.py          # HTTP server para dashboard SIEM (porta 8090)
│   ├── Protocolo.py             # STSP v1.0 (protocolo seguro completo)
│   ├── Criptografia.py          # 4 algoritmos simetricos (AES, ChaCha20, 3DES, Blowfish)
│   ├── HashUtils.py             # SHA-256 + autenticacao login/senha com hash
│   ├── Assinatura.py            # RSA-PKCS#1 v1.5 + SHA-256
│   ├── Certificado.py           # CA + certificados X.509
│   ├── Seguranca.py             # NGFW, Proxy Reverso, IDS (NIDS+HIDS), SIEM
│   ├── Telemetria.py            # Geracao realista de dados de sensores
│   ├── BrokerMQTT.py            # Broker MQTT embarcado (amqtt)
│   ├── DispositivoSemaforo.py   # Simulador de semaforo
│   ├── Cruzamento.py            # Coordenacao de cruzamento (2 semaforos)
│   ├── Ambulancia.py            # Simulador de ambulancia
│   └── MitM.py                  # Atacante Man-in-the-Middle (4 tipos)
├── scripts/                     # Utilitarios e demonstracoes
│   ├── provisionar_rede.py      # Gera CA + certificados para todos dispositivos
│   ├── gerar_certificado.py     # Gera CA + 1 certificado
│   ├── distribuir_certificado.py# Simula distribuicao segura de certificados
│   ├── ler_certificado.py       # Exibe metadados de certificado
│   ├── comparar_criptografia.py # Benchmark dos 4 algoritmos simetricos
│   ├── demonstrar_assinatura.py # Demo de assinatura com 4 cenarios
│   └── demonstrar_auth.py       # Desafio extra: autenticacao login/senha com hash
├── docs/                        # Documentacao e referencias
│   ├── ESTRUTURA.md             # Este arquivo
│   ├── CONTEXTO_TRABALHO3.md    # Contexto para relatorio (mapeamento tarefa x codigo)
│   ├── Cenario-T2-T3.md         # Mapeamento T2 -> T3
│   ├── Tarefa4-Certificados-MitM.md # Certificados e defesa MitM
│   ├── Tarefa6-ProtocoloMQTT.md # Especificacao do protocolo STSP
│   ├── comparar_criptografia_output.txt # Saida real do benchmark
│   └── referencias/             # PDFs do Trabalho 2
├── dados/                       # Chaves, certificados, logs (gitignored)
│   ├── chaves/
│   ├── certificados/
│   │   ├── ca/
│   │   └── emitidos/
│   ├── dispositivos/
│   └── logs/
└── siem/                        # Frontend Next.js (painel SIEM)
```

## Responsabilidades

| Pasta | Conteudo |
|-------|----------|
| `src/` | Aplicacao em execucao continua (dispositivo + servidor) |
| `scripts/` | Tarefas pontuais (certificados, benchmarks, demos) |
| `dados/` | Artefatos gerados e sensíveis |
| `docs/` | Textos para entrega, apresentacao e contexto do relatorio |
| `siem/` | Frontend do painel SIEM (Next.js, servido na porta 8090) |
