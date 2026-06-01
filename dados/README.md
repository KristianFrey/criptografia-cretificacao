# Dados do projeto (não versionar chaves em repositório público)

Gerados localmente por `python scripts/provisionar_rede.py`.

```
dados/
├── chaves/           # CA e chaves privadas de emissão
├── certificados/     # CA e certificados emitidos
│   ├── ca/
│   └── emitidos/
├── dispositivos/     # certificado + chave por semáforo (Edge)
│   ├── SEMAFORO_A1/
│   └── SEMAFORO_B2/
└── logs/             # logs do servidor central
```
