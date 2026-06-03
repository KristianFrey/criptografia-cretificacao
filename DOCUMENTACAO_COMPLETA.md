# Documentação Completa - Semáforos Inteligentes (Segurança em IoT)

**Disciplina:** Segurança em IoT  
**Cenário:** Smart Cities  
**Equipe:** Julio Becker, João Winkelmann, Kristian Frey  
**Trabalho:** 3 - Criptografia e Protocolo Seguro

---

## Índice

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Estrutura de Diretórios](#estrutura-de-diretórios)
3. [Arquivos do `src/` - Código Principal](#arquivos-do-src---código-principal)
4. [Arquivos do `scripts/` - Scripts de Utilidade](#arquivos-do-scripts---scripts-de-utilidade)
5. [Arquivos do `docs/` - Documentação Técnica](#arquivos-do-docs---documentação-técnica)
6. [Conceitos Técnicos Explicados](#conceitos-técnicos-explicados)
7. [Como Executar o Projeto](#como-executar-o-projeto)
8. [Fluxo de Dados End-to-End](#fluxo-de-dados-end-to-end)
9. [Mapeamento Trabalho 2 → Trabalho 3](#mapeamento-trabalho-2--trabalho-3)

---

## Visão Geral do Projeto

Este projeto implementa um **sistema de semáforos inteligentes** com segurança criptográfica completa para o cenário de Smart Cities. O objetivo é demonstrar como proteger a comunicação entre dispositivos IoT (semáforos) e um servidor central usando:

- **Criptografia simétrica** (AES-128) para confidencialidade
- **Hash SHA-256** para integridade de dados
- **Assinatura digital RSA** para autenticidade
- **Certificados digitais X.509** para identidade de dispositivos
- **Protocolo MQTT** para transporte de mensagens
- **Sistema de segurança multicamadas** (NGFW, Proxy, IDS, SIEM)

### Cenário

Imagine uma cidade inteligente onde semáforos comunicam dados de tráfego em tempo real para um servidor central. Esses dados incluem:
- Número de carros
- Estado atual do semáforo (VERDE, AMARELO, VERMELHO)
- Tempo da fase atual
- Tamanho da fila
- Modo operacional (NORMAL, EMERGÊNCIA, MANUTENÇÃO)

Sem segurança, um atacante poderia:
- Falsificar dados de tráfego
- Alterar o estado dos semáforos
- Intercepta comunicações
- Lançar ataques DoS

Este projeto implementa todas as defesas necessárias.

---

## Estrutura de Diretórios

```
Criptografia/
├── README.md                 # Guia rápido de início
├── requirements.txt          # Dependências Python
├── .gitignore               # Arquivos sensíveis ignorados do Git
├── DOCUMENTACAO_COMPLETA.md # Este arquivo
│
├── src/                     # CÓDIGO PRINCIPAL (simulador em execução)
│   ├── config.py            # Configuração de caminhos
│   ├── Servidor.py          # Servidor central (Fog/Cloud)
│   ├── DispositivoSemaforo.py # Dispositivo IoT (semáforo)
│   ├── Protocolo.py         # Protocolo STSP v1.0
│   ├── Criptografia.py      # Criptografia simétrica
│   ├── HashUtils.py         # Funções de hash
│   ├── Assinatura.py        # Assinatura digital RSA
│   ├── Certificado.py       # Certificados X.509
│   ├── Telemetria.py        # Geração de dados de telemetria
│   ├── Seguranca.py         # Simulação NGFW, Proxy, IDS, SIEM
│   └── BrokerMQTT.py        # Broker MQTT embarcado
│
├── scripts/                 # SCRIPTS DE UTILIDADE (tarefas pontuais)
│   ├── provisionar_rede.py      # Configura toda a rede (CA + certificados)
│   ├── gerar_certificado.py     # Emite certificado de um dispositivo
│   ├── distribuir_certificado.py # Simula provisionamento seguro
│   ├── ler_certificado.py       # Exibe metadados do certificado
│   ├── comparar_criptografia.py # Benchmark de algoritmos
│   └── demonstrar_assinatura.py # Testes de assinatura RSA
│
├── docs/                    # DOCUMENTAÇÃO TÉCNICA
│   ├── ESTRUTURA.md             # Estrutura do projeto
│   ├── Cenario-T2-T3.md         # Alinhamento Trabalho 2 e 3
│   ├── Tarefa4-Certificados-MitM.md # Certificados e MitM
│   ├── Tarefa6-ProtocoloMQTT.md # Protocolo STSP/MQTT
│   └── referencias/             # PDF do Trabalho 2
│
└── dados/                   # DADOS SENSÍVEIS (não versionados)
    ├── certificados/        # Certificados CA e dispositivos
    ├── chaves/              # Chaves privadas
    ├── dispositivos/        # Certificados distribuídos
    └── logs/                # Logs do servidor
```

---

## Arquivos do `src/` - Código Principal

### `config.py` - Configuração Centralizada

**O que faz:** Define todos os caminhos de pastas e arquivos do projeto em um único lugar.

**Por que existe:** Evita que cada arquivo tenha caminhos hardcoded. Se você precisar mover pastas, só altera aqui.

**Principais funções:**
- `RAIZ` - Caminho raiz do projeto
- `PASTA_DADOS`, `PASTA_CHAVES`, `PASTA_CERTIFICADOS` - Caminhos para dados sensíveis
- `garantir_estrutura_dados()` - Cria as pastas se não existirem

---

### `Criptografia.py` - Criptografia Simétrica

**O que faz:** Implementa criptografia simétrica para proteger a confidencialidade dos dados.

**Algoritmos suportados:**
- **AES-128-EAX** (padrão) - Algoritmo moderno, seguro, amplamente usado
- **ChaCha20-Poly1305** - Alternativa segura para dispositivos sem aceleração hardware
- **3DES-EAX** - Algoritmo legado (obsoleto, apenas para comparação)
- **Blowfish-EAX** - Algoritmo legado (apenas para comparação)

**Principais funções:**
- `criptografar(mensagem, algoritmo)` - Cifra uma mensagem
- `descriptografar(mensagem_criptografada)` - Decifra uma mensagem
- `listar_algoritmos()` - Retorna lista de algoritmos disponíveis

**Como funciona:**
1. Gera um nonce (número usado uma vez) aleatório
2. Cifra os dados com o algoritmo escolhido
3. Gera uma tag de autenticação (MAC)
4. Empacota: `algoritmo|base64(nonce + tag + ciphertext)`

---

### `HashUtils.py` - Funções de Hash

**O que faz:** Gera hashes SHA-256 para garantir integridade de dados.

**Principais funções:**
- `gerar_hash(mensagem)` - Retorna hash SHA-256 em hexadecimal

**Por que SHA-256?**
- Padrão industrial amplamente aceito
- Resistente a colisões
- Rápido de calcular
- Fixo de 64 caracteres em hexadecimal

---

### `Certificado.py` - Certificados Digitais X.509

**O que faz:** Implementa toda a lógica de certificados digitais para autenticação de dispositivos IoT.

**Conceitos chave:**
- **CA (Autoridade Certificadora):** Entidade confiável que assina certificados
- **Certificado:** Documento que vincula uma identidade (Device ID) a uma chave pública
- **Cadeia de confiança:** Servidor confia na CA, CA confia nos dispositivos

**Principais funções:**
- `gerar_autoridade_certificadora()` - Cria a CA simulada (SmartTraffic IoT CA)
- `emitir_certificado_dispositivo(device_id)` - Emite certificado para um semáforo
- `verificar_certificado(cert, device_id)` - Valida certificado (cadeia, validade, Device ID)
- `extrair_metadados(cert)` - Extrai informações do certificado
- `obter_certificado_confiavel(device_id)` - Carrega certificado de dispositivo registrado

**Metadados no certificado:**
- Device ID (extensão X.509 personalizada)
- Chave pública RSA (2048 bits)
- Validade (1 ano para dispositivos, 10 anos para CA)
- Emissor (SmartTraffic IoT CA)
- Fingerprint SHA-256 da chave pública

---

### `Assinatura.py` - Assinatura Digital RSA

**O que faz:** Implementa assinatura digital RSA para garantir autenticidade e não-repúdio.

**Algoritmo:** RSA-PKCS#1 v1.5 + SHA-256

**Fluxo de assinatura:**
1. Dispositivo usa sua **chave privada** (do certificado) para assinar
2. Servidor usa a **chave pública** (extraída do certificado) para verificar
3. Se a verificação falha, o pacote foi alterado ou é falso

**Principais funções:**
- `assinar_mensagem(mensagem, device_id)` - Assina qualquer texto
- `assinar_pacote(pacote, device_id)` - Assina pacote IoT completo
- `verificar_assinatura(mensagem, assinatura, device_id)` - Verifica assinatura
- `verificar_assinatura_pacote(pacote, device_id)` - Verifica assinatura do pacote

**Conteúdo assinado:** `device_id|timestamp|dados_json`

---

### `Protocolo.py` - SmartTraffic Secure Protocol (STSP) v1.0

**O que faz:** Define o protocolo de comunicação segura entre semáforos e servidor.

**Camadas de segurança (de baixo para cima):**
1. **Transporte MQTT** - QoS 1, tópicos estruturados
2. **Confidencialidade** - AES-128-EAX no payload
3. **Autenticidade** - Assinatura RSA com certificado
4. **Integridade** - SHA-256 dos dados
5. **Aplicação** - JSON com telemetria

**Formato do pacote STSP (antes da cifragem):**
```json
{
  "protocolo": "STSP",
  "versao": "1.0",
  "device_id": "SEMAFORO_A1",
  "timestamp": "2027-05-31T12:00:00",
  "dados": {"carros": 23, "estado": "VERDE", ...},
  "hash": "<sha256>",
  "assinatura": "<rsa-base64>",
  "criptografia": "aes"
}
```

**Tópicos MQTT:**
- Telemetria: `smarttraffic/v1/semaforo/{device_id}/telemetria`
- Alertas ATMS: `smarttraffic/v1/atms/alertas`

**Principais funções:**
- `montar_pacote(device_id, dados)` - Monta pacote com hash e assinatura
- `serializar_para_mqtt(pacote)` - Cifra pacote para publicação
- `decodificar_mqtt(payload)` - Decifra e interpreta payload recebido
- `processar_pacote(pacote, ngfw, proxy, ids, siem)` - Pipeline completo de validação

---

### `Telemetria.py` - Geração de Telemetria

**O que faz:** Simula dados realistas de semáforos inteligentes.

**Dados gerados:**
- `carros` - Número de veículos no cruzamento (0-50)
- `estado` - Estado atual (VERDE, AMARELO, VERMELHO)
- `tempo_fase_seg` - Tempo da fase atual em segundos
- `fila_metros` - Tamanho da fila em metros (0-200)
- `modo` - Modo operacional (NORMAL, EMERGÊNCIA, MANUTENÇÃO)
- `local` - Identificação do cruzamento

**Comportamento simulado:**
- Transições de estado seguem padrão real (VERDE → AMARELO → VERMELHO → VERDE)
- Número de carros varia gradualmente
- Filas crescem e diminuem realisticamente
- Eventos de emergência ocorrem aleatoriamente (2% de chance)

**Classe principal:**
- `GeradorTelemetria(device_id)` - Gerador de dados para um semáforo
- `proximo_pacote()` - Retorna próximo conjunto de dados

---

### `Seguranca.py` - Simulação de Camadas de Segurança (Trabalho 2)

**O que faz:** Implementa simulações das camadas de segurança definidas no Trabalho 2.

**Componentes simulados:**

#### `MockNGFW` - Next-Generation Firewall
- Whitelist de dispositivos autorizados
- Blacklist de dispositivos bloqueados
- Política "default-deny" (bloqueia tudo não autorizado)
- Bloqueio de portas perigosas (22, 23)

#### `MockReverseProxy` - Proxy Reverso
- Rate limiting (limite de requisições por segundo)
- Anonimização de IP de origem
- Cache (simulado)

#### `MockIDS` - Intrusion Detection System
- **NIDS (Network IDS):** Detecta ataques de rede (DoS)
  - Monitora volume de pacotes por dispositivo
  - Detecta padrões de DoS
- **HIDS (Host IDS):** Detecta anomalias nos dados
  - Valida estados do semáforo
  - Valida tempos de fase
  - Detecta transições ilegais
  - Detecta variações anormais de carros

#### `MockSIEM` - Security Information and Event Management
- Coleta logs de todas as fontes (NGFW, Proxy, IDS)
- Correlaciona eventos de múltiplas fontes
- Detecta ameaças críticas
- Resposta automatizada (bloqueio no NGFW)
- Publica alertas no dashboard ATMS

---

### `BrokerMQTT.py` - Broker MQTT Embarcado

**O que faz:** Implementa um broker MQTT local para simulação sem dependência externa.

**Por que existe:** Em produção, usaria Mosquitto na DMZ. No simulador, usamos broker embarcado para facilitar testes locais.

**Características:**
- Usa biblioteca `amqtt`
- Executa em thread daemon
- Porta padrão: 1883 (simulação)
- Em produção: 8883 com TLS

**Principais funções:**
- `iniciar_broker_em_thread(host, port)` - Inicia broker em background

---

### `DispositivoSemaforo.py` - Dispositivo IoT (Semáforo)

**O que faz:** Simula um semáforo inteligente publicando telemetria.

**Fluxo de execução:**
1. Valida certificado local
2. Conecta ao broker MQTT
3. Gera telemetria realisticamente
4. Monta pacote STSP (hash + assinatura + cifragem)
5. Publica no tópico MQTT
6. Repete a cada 5 segundos

**Principais funções:**
- `executar_dispositivo(device_id)` - Loop principal do dispositivo
- `publicar_telemetria(client, device_id, gerador, cert_info)` - Publica um pacote
- `_validar_certificado_local(device_id)` - Verifica certificado antes de iniciar

**Dispositivos padrão:**
- `SEMAFORO_A1` - Cruzamento A1
- `SEMAFORO_B2` - Cruzamento B2

---

### `Servidor.py` - Servidor Central (Fog/Cloud)

**O que faz:** Servidor central que recebe telemetria dos semáforos e aplica todas as validações de segurança.

**Fluxo de execução:**
1. Inicia broker MQTT embarcado
2. Configura camadas de segurança (NGFW, Proxy, IDS, SIEM)
3. Conecta ao broker como assinante
4. Inscreve-se em tópicos de telemetria
5. Para cada mensagem recebida:
   - Decifra payload
   - Valida certificado
   - Verifica NGFW (whitelist/blacklist)
   - Verifica Proxy (rate limit)
   - Analisa IDS (NIDS + HIDS)
   - Verifica integridade (hash)
   - Verifica autenticidade (assinatura)
   - Verifica timestamp (anti-replay)
   - Regra log
   - Publica alertas se necessário

**Principais funções:**
- `main()` - Inicialização e loop principal
- `on_connect()` - Callback de conexão MQTT
- `on_message()` - Callback de recebimento de mensagem
- `_imprimir_resultado()` - Exibe resultado das validações
- `_registrar_log()` - Salva log em arquivo

**Dispositivos autorizados:** SEMAFORO_A1, SEMAFORO_B2

---

## Arquivos do `scripts/` - Scripts de Utilidade

### `provisionar_rede.py` - Provisionamento Completo

**O que faz:** Configura toda a rede IoT de uma vez (CA + certificados de todos os dispositivos).

**Quando usar:** Primeira vez que você roda o projeto, ou quando precisa reconfigurar tudo.

**Fluxo:**
1. Gera Autoridade Certificadora (SmartTraffic IoT CA)
2. Para cada dispositivo (SEMAFORO_A1, SEMAFORO_B2):
   - Gera par de chaves RSA
   - Emite certificado assinado pela CA
   - Salva certificado na pasta do dispositivo
   - Salva chave privada na pasta do dispositivo

**Comando:**
```powershell
python scripts/provisionar_rede.py
```

---

### `gerar_certificado.py` - Emitir Certificado Único

**O que faz:** Emite certificado para um único dispositivo (SEMAFORO_A1 por padrão).

**Quando usar:** Para testar emissão de certificado ou adicionar novo dispositivo.

**Fluxo:**
1. Gera CA se não existir
2. Gera par de chaves para o dispositivo
3. Emite certificado assinado pela CA
4. Exibe metadados do certificado

**Comando:**
```powershell
python scripts/gerar_certificado.py
```

---

### `distribuir_certificado.py` - Simulação de Provisionamento Seguro

**O que faz:** Simula o fluxo real de distribuição segura de certificados em IoT.

**Diferença para `gerar_certificado.py`:**
- Chave privada é gerada **no dispositivo** (nunca sai de lá)
- Dispositivo envia apenas chave pública para a CA
- CA entrega certificado cifrado com PSK de provisionamento
- Simula canal seguro (TLS em produção)

**Fluxo detalhado:**
1. **Dispositivo** gera par de chaves localmente
2. **Dispositivo** envia solicitação (Device ID + chave pública) à CA
3. **CA** valida Device ID na whitelist
4. **CA** assina certificado com chave privada da CA
5. **CA** cifra certificado com PSK de provisionamento (AES-128-EAX)
6. **CA** envia certificado cifrado ao dispositivo
7. **Dispositivo** decifra com PSK
8. **Dispositivo** armazena certificado e chave privada

**Comando:**
```powershell
python scripts/distribuir_certificado.py
```

---

### `ler_certificado.py` - Visualizar Metadados

**O que faz:** Exibe informações detalhadas de um certificado.

**Quando usar:** Para verificar se um certificado foi emitido corretamente.

**Informações exibidas:**
- Device ID
- Emissor (CA)
- Validade até
- Fingerprint SHA-256
- Status de verificação

**Comando:**
```powershell
python scripts/ler_certificado.py SEMAFORO_A1
```

---

### `comparar_criptografia.py` - Benchmark de Algoritmos

**O que faz:** Compara performance de diferentes algoritmos de criptografia simétrica.

**Métricas medidas:**
- Tempo de cifragem (ms)
- Tempo de decifragem (ms)
- Tempo total (ms)
- Overhead de tamanho (%)

**Algoritmos testados:**
- AES-128-EAX
- ChaCha20-Poly1305
- 3DES-EAX
- Blowfish-EAX

**Comando:**
```powershell
python scripts/comparar_criptografia.py
```

---

### `demonstrar_assinatura.py` - Testes de Assinatura RSA

**O que faz:** Demonstra como a assinatura digital garante integridade e autenticidade.

**Testes realizados:**
1. **Pacote original** - Deve passar
2. **Dados adulterados** - Deve falhar (estado alterado)
3. **Timestamp alterado** - Deve falhar (replay attack)
4. **Assinatura corrompida** - Deve falhar (assinatura inválida)

**Comando:**
```powershell
python scripts/demonstrar_assinatura.py
```

---

## Arquivos do `docs/` - Documentação Técnica

### `ESTRUTURA.md` - Estrutura do Projeto

**Conteúdo:** Visão geral da estrutura de diretórios e responsabilidades de cada pasta.

### `Cenario-T2-T3.md` - Alinhamento Trabalho 2 e 3

**Conteúdo:** Explica como o Trabalho 3 (implementação) se conecta com o cenário definido no Trabalho 2.

**Mapeamento:**
- Superfície de ataque → defesas implementadas
- Componentes do PDF → simulações no código
- Fluxo de incidente → implementação no SIEM

### `Tarefa4-Certificados-MitM.md` - Certificados e MitM

**Conteúdo:** Explicação detalhada de:
- O que são certificados digitais
- Como mitigam ataques Man-in-the-Middle
- Aplicação em IoT
- Limitações em dispositivos com poucos recursos

### `Tarefa6-ProtocoloMQTT.md` - Protocolo STSP/MQTT

**Conteúdo:** Documentação do protocolo STSP:
- Camadas de segurança
- Formato do pacote
- Tópicos MQTT
- Fluxo dispositivo → servidor

---

## Conceitos Técnicos Explicados

### Criptografia Simétrica vs Assimétrica

**Criptografia Simétrica (AES):**
- Mesma chave para cifrar e decifrar
- Rápida e eficiente
- Usada para grandes volumes de dados
- Exemplo: Cifrar telemetria dos semáforos

**Criptografia Assimétrica (RSA):**
- Chave pública (cifrar/verificar) + chave privada (decifrar/assinar)
- Mais lenta
- Usada para assinaturas digitais e troca de chaves
- Exemplo: Assinar pacotes STSP

### Hash Criptográfico

**O que é:** Função unidirecional que gera "impressão digital" de dados.

**Propriedades:**
- Impossível reverter hash para dados originais
- Pequena alteração nos dados = hash completamente diferente
- Impraticável encontrar dois dados com mesmo hash (colisão)

**Uso no projeto:** SHA-256 para garantir que dados não foram alterados.

### Assinatura Digital

**O que faz:** Prova que uma mensagem veio de quem diz que veio e não foi alterada.

**Como funciona:**
1. Emissor assina com sua **chave privada**
2. Qualquer um pode verificar com a **chave pública** do emissor
3. Se verificação falha, mensagem foi alterada ou assinatura é falsa

**Propriedades:**
- **Autenticidade:** Prova origem
- **Integridade:** Detecta alterações
- **Não-repúdio:** Emissor não pode negar que assinou

### Certificado Digital

**O que é:** Documento eletrônico que vincula identidade a chave pública, assinado por CA confiável.

**Analogia:** Como carteira de identidade com foto assinada pelo governo.

**Componentes:**
- Identidade (Device ID)
- Chave pública
- Assinatura da CA
- Validade
- Emissor

**Uso no projeto:** Cada semáforo tem certificado único emitido pela SmartTraffic IoT CA.

### MQTT (Message Queuing Telemetry Transport)

**O que é:** Protocolo de mensagens leve para IoT.

**Características:**
- Publicar/Inscrever (pub/sub)
- Leve e eficiente
- QoS (Quality of Service) níveis 0, 1, 2
- Tópicos hierárquicos

**Uso no projeto:** Semáforos publicam telemetria, servidor se inscreve para receber.

### Camadas de Defesa em Profundidade

**Conceito:** Múltiplas camadas de segurança, cada uma protegendo contra diferentes ameaças.

**No projeto:**
1. **NGFW** - Bloqueia dispositivos não autorizados
2. **Proxy** - Rate limiting e anonimização
3. **IDS (NIDS)** - Detecta ataques de rede (DoS)
4. **IDS (HIDS)** - Detecta anomalias nos dados
5. **SIEM** - Correlaciona eventos e responde
6. **Certificados** - Autenticação de dispositivos
7. **Assinatura** - Garante autenticidade de dados
8. **Hash** - Garante integridade
9. **Criptografia** - Confidencialidade

---

## Como Executar o Projeto

### 1. Configuração Inicial

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Provisionar Certificados

```powershell
# Configurar toda a rede (CA + certificados A1 e B2)
python scripts/provisionar_rede.py
```

### 3. Executar Simulador

**Terminal 1 - Servidor:**
```powershell
cd src
python Servidor.py
```

**Terminal 2 - Semáforo A1:**
```powershell
cd src
python DispositivoSemaforo.py SEMAFORO_A1
```

**Terminal 3 (opcional) - Semáforo B2:**
```powershell
cd src
python DispositivoSemaforo.py SEMAFORO_B2
```

### 4. Executar Scripts de Demonstração

```powershell
# Comparar algoritmos de criptografia
python scripts/comparar_criptografia.py

# Testar assinatura digital
python scripts/demonstrar_assinatura.py

# Visualizar certificado
python scripts/ler_certificado.py SEMAFORO_A1
```

---

## Fluxo de Dados End-to-End

### 1. Dispositivo (Semáforo) → Servidor

```
DispositivoSemaforo.py
    ↓
GeradorTelemetria.gera_dados()
    ↓
Protocolo.montar_pacote()
    ├─ HashUtils.gerar_hash() → SHA-256 dos dados
    ├─ Assinatura.assinar_pacote() → RSA com chave privada
    └─ Criptografia.criptografar() → AES-128
    ↓
MQTT Client.publish()
    ↓
Broker MQTT (1883)
    ↓
Servidor.py (on_message)
    ↓
Protocolo.decodificar_mqtt()
    ├─ Criptografia.descriptografar() → AES-128
    └─ JSON parse
    ↓
Protocolo.processar_pacote()
    ├─ Certificado.verificar_certificado() → Valida CA, validade, Device ID
    ├─ Seguranca.MockNGFW.check_device() → Whitelist/blacklist
    ├─ Seguranca.MockReverseProxy.check_rate_limit() → Rate limit
    ├─ Seguranca.MockIDS.analyze_nids() → Detecta DoS
    ├─ Seguranca.MockIDS.analyze_hids() → Valida dados
    ├─ HashUtils.gerar_hash() → Verifica integridade
    ├─ Assinatura.verificar_assinatura_pacote() → Verifica autenticidade
    └─ Protocolo.validar_timestamp() → Anti-replay
    ↓
Servidor.registrar_log()
    ↓
Servidor.publicar_alerta_ATMS() (se necessário)
```

### 2. Pipeline de Validação no Servidor

```
Pacote recebido
    ↓
[1] Certificado válido?
    ├─ NÃO → Rejeitar, logar, alertar SIEM
    └─ SIM → Continuar
    ↓
[2] NGFW autoriza?
    ├─ NÃO → Rejeitar, adicionar blacklist, alertar SIEM
    └─ SIM → Continuar
    ↓
[3] Proxy rate limit OK?
    ├─ NÃO → Rejeitar, adicionar blacklist, alertar SIEM
    └─ SIM → Continuar
    ↓
[4] IDS NIDS (DoS)?
    ├─ DETECTADO → Alertar SIEM, possível bloqueio
    └─ OK → Continuar
    ↓
[5] IDS HIDS (anomalias)?
    ├─ DETECTADO → Alertar SIEM
    └─ OK → Continuar
    ↓
[6] Hash integridade?
    ├─ NÃO → Rejeitar, dados alterados
    └─ SIM → Continuar
    ↓
[7] Assinatura válida?
    ├─ NÃO → Rejeitar, falsificação ou alteração
    └─ SIM → Continuar
    ↓
[8] Timestamp válido?
    ├─ NÃO → Rejeitar, replay attack
    └─ SIM → Continuar
    ↓
[9] PACOTE AUTÊNTICO → Processar dados
```

---

## Mapeamento Trabalho 2 → Trabalho 3

### Trabalho 2 (Cenário e Arquitetura)

Definiu:
- Superfície de ataque do sistema
- Arquitetura de segurança (NGFW, DMZ, Proxy, IDS, SIEM)
- Tecnologias (MQTT/TLS, Snort, Wazuh)
- Fluxo de incidentes

### Trabalho 3 (Implementação)

Implementou:
- **Criptografia simétrica** (AES-128) → Confidencialidade
- **Hash SHA-256** → Integridade
- **Assinatura RSA** → Autenticidade
- **Certificados X.509** → Identidade de dispositivos
- **Protocolo STSP** → Formato padronizado de comunicação
- **Simulação MQTT** → Transporte de mensagens
- **Mock NGFW/Proxy/IDS/SIEM** → Camadas de segurança do T2

### Continuidade

```
Trabalho 1: Ameaças e superfície de ataque
    ↓
Trabalho 2: Arquitetura de defesa (NGFW, DMZ, Proxy, IDS, SIEM)
    ↓
Trabalho 3: Implementação de criptografia e protocolo seguro
```

### Correspondências

| Trabalho 2 (PDF) | Trabalho 3 (Código) |
|------------------|---------------------|
| Broker MQTT na DMZ (porta 8883 TLS) | `BrokerMQTT.py` (porta 1883 simulado) |
| NGFW borda | `MockNGFW` |
| Proxy reverso | `MockReverseProxy` |
| Snort (NIDS) | `MockIDS.analyze_nids()` |
| Wazuh (HIDS) | `MockIDS.analyze_hids()` |
| Wazuh SIEM | `MockSIEM` |
| Dashboard ATMS | Tópico `smarttraffic/v1/atms/alertas` |
| Semáforos A1, B2 | `SEMAFORO_A1`, `SEMAFORO_B2` |
| Comunicação segura | STSP + AES + RSA + Certificados |

---

## Resumo para Apresentação

### O que o projeto faz

Implementa um sistema de semáforos inteligentes com segurança criptográfica completa, demonstrando como proteger comunicação IoT em cenários de Smart Cities.

### Tecnologias utilizadas

- **Python** - Linguagem principal
- **PyCryptodome** - Criptografia (AES, RSA)
- **Cryptography** - Certificados X.509
- **Paho-MQTT** - Cliente MQTT
- **AMQTT** - Broker MQTT embarcado

### Camadas de segurança implementadas

1. **NGFW** - Controle de acesso (whitelist/blacklist)
2. **Proxy** - Rate limiting e anonimização
3. **IDS** - Detecção de intrusão (NIDS + HIDS)
4. **SIEM** - Correlação de eventos e resposta
5. **Certificados** - Autenticação de dispositivos
6. **Assinatura** - Autenticidade de dados
7. **Hash** - Integridade de dados
8. **Criptografia** - Confidencialidade

### Principais contribuições

- Protocolo STSP v1.0 completo
- Simulação realista de telemetria
- Pipeline de validação multicamadas
- Sistema de provisionamento seguro de certificados
- Demonstração de defesa contra MitM, DoS, tampering

---

## Glossário

- **CA (Certificate Authority):** Autoridade Certificadora, entidade que emite certificados
- **DoS (Denial of Service):** Ataque de negação de serviço
- **HIDS (Host-based IDS):** Sistema de detecção de intrusão baseado em host
- **IDS (Intrusion Detection System):** Sistema de detecção de intrusão
- **IoT (Internet of Things):** Internet das Coisas
- **MitM (Man-in-the-Middle):** Ataque onde atacante intercepta comunicação
- **MQTT:** Protocolo de mensagens para IoT
- **NGFW (Next-Generation Firewall):** Firewall de próxima geração
- **NIDS (Network-based IDS):** Sistema de detecção de intrusão baseado em rede
- **PSK (Pre-Shared Key):** Chave compartilhada previamente
- **SIEM (Security Information and Event Management):** Sistema de gerenciamento de eventos de segurança
- **Smart City:** Cidade inteligente
- **STSP:** SmartTraffic Secure Protocol
- **TLS (Transport Layer Security):** Protocolo de segurança de transporte
- **X.509:** Padrão de certificados digitais

---

## Dúvidas Frequentes

### Por que usar AES-128 e não AES-256?

AES-128 é:
- Suficientemente seguro para IoT
- Mais rápido em dispositivos com poucos recursos
- Padrão amplamente adotado
- Ainda não foi quebrado na prática

### Por que RSA 2048 bits e não 4096?

RSA 2048 bits é:
- Suficientemente seguro até 2030+
- Mais rápido para assinar/verificar
- Padrão em certificados X.509
- Adequado para dispositivos IoT

### Por que MQTT e não HTTP?

MQTT é:
- Mais leve (header menor)
- Pub/sub (melhor para IoT)
- QoS configurável
- Padrão em IoT

### Por que não usar TLS no broker local?

TLS é usado em produção (porta 8883). No simulador local:
- Facilita testes e debugging
- STSP já cifra o payload
- Em produção, STSP roda sobre MQTT/TLS

### Como adicionar novo semáforo?

1. Adicionar Device ID à whitelist em `Seguranca.py`
2. Executar `python scripts/provisionar_rede.py` com novo dispositivo
3. Executar `python src/DispositivoSemaforo.py NOVO_DISPOSITIVO`

---

## Contato e Suporte

Para dúvidas sobre o projeto, consulte:
- Documentação em `docs/`
- Comentários nos arquivos fonte
- README.md para início rápido

---

**Fim da Documentação Completa**
