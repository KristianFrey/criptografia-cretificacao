# Tarefa 4 — Certificados digitais e defesa contra MitM em IoT

## Conceito de certificados digitais

Um **certificado digital** é um documento eletrônico que associa uma **identidade** (ex.: `SEMAFORO_A1`) a uma **chave pública**, assinado por uma **Autoridade Certificadora (CA)** confiável. No cenário de semáforos inteligentes, cada nó da rede IoT possui certificado único emitido pela CA simulada **SmartTraffic IoT CA**.

Metadados obrigatórios no certificado do projeto:

| Metadado | Onde está |
|----------|-----------|
| Device ID | Extensão X.509 OID `1.3.6.1.4.1.37459.1.1` |
| Chave pública | Campo `subjectPublicKeyInfo` do certificado |
| Período de validade | `notBefore` / `notAfter` |
| Autoridade emissora | Campo `issuer` (SmartTraffic IoT CA) |

## Aplicação na autenticação de dispositivos IoT

1. O **dispositivo** assina telemetria com a chave privada vinculada ao certificado.
2. O **servidor central** confia apenas em certificados assinados pela CA SmartTraffic.
3. O servidor verifica validade temporal, cadeia de confiança e correspondência do Device ID.
4. Isso garante que apenas semáforos registrados enviem dados à plataforma de gestão urbana.

## Papel dos certificados na mitigação de ataques Man-in-the-Middle (MitM)

### O problema

Em um ataque **MitM**, um adversário intercepta a comunicação entre o semáforo e o servidor central. Sem certificados, o atacante pode:

- **Personificar o dispositivo** enviando dados falsos (ex.: semáforo sempre verde).
- **Personificar o servidor** e injetar comandos maliciosos.
- **Alterar pacotes** em trânsito (tampering), comprometendo decisões de tráfego.

### Como o certificado mitiga o MitM

```
  Semáforo A1                    Atacante (MitM)              Servidor Central
      |                                |                            |
      |--- pacote + assinatura -------->|                            |
      |    (certificado SEMAFORO_A1)    |--- pacote falsificado --->|
      |                                |    (cert. desconhecido)    |
      |                                |                            X rejeitado
```

1. **Autenticação mútua de identidade**: o certificado prova que o emissor é o dispositivo registrado, não um impostor.
2. **Cadeia de confiança**: o servidor só aceita certificados assinados pela CA SmartTraffic — certificados forjados pelo atacante são rejeitados na verificação de assinatura da CA.
3. **Vinculação chave-identidade**: a chave pública no certificado é usada para verificar assinaturas digitais; sem a chave privada correspondente (guardada no dispositivo), o MitM não consegue assinar pacotes válidos.
4. **Validade temporal**: certificados expirados são rejeitados, limitando janela de exploração caso uma chave vaze.
5. **Distribuição segura (provisionamento)**: no projeto, o certificado é entregue cifrado com PSK de fábrica; a chave privada **nunca** trafega pela rede — apenas é gerada localmente no dispositivo.

### Limitações em IoT

- Dispositivos com pouca memória podem ter dificuldade com cadeias X.509 completas → uso de certificados compactos e CA dedicada.
- Revogação (CRL/OCSP) é desafiadora em redes IoT com conectividade intermitente → whitelist + validade curta.
- PSK de provisionamento deve ser única por dispositivo em produção (no simulador usamos PSK de demonstração).

## Simulação implementada no projeto

| Script | Função |
|--------|--------|
| `GerarCertificado.py` | Cria CA simulada e emite certificado do semáforo |
| `LerCertificado.py` | Exibe metadados obrigatórios |
| `DistribuirCertificado.py` | Simula provisionamento seguro (chave local + canal cifrado PSK) |
| `src/Certificado.py` | Biblioteca de emissão, leitura e verificação |
| `src/Servidor.py` | Valida certificado antes de aceitar pacotes |

## Como executar

```powershell
cd c:\desenv\Criptografia
.\venv\Scripts\python.exe GerarCertificado.py
.\venv\Scripts\python.exe DistribuirCertificado.py
.\venv\Scripts\python.exe LerCertificado.py SEMAFORO_A1
```
