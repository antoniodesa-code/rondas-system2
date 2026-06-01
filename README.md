# 🏥 Sistema de Ronda Hospitalar

Sistema web desenvolvido para digitalizar o processo de ronda hospitalar, substituindo formulários em papel por uma solução moderna, rápida e auditável.

## Objetivo

O sistema permite que técnicos realizem rondas nos setores do hospital registrando informações operacionais e coletando uma confirmação simples do setor através de QR Code.

Principais objetivos:

- Eliminar uso de papel
- Aumentar rastreabilidade
- Registrar auditorias operacionais
- Reduzir fraudes
- Simplificar o fluxo para os usuários do hospital
- Centralizar informações para futuras análises e relatórios

---

# Arquitetura

## Frontend

Tecnologias utilizadas:

- React
- Vite
- TailwindCSS

Objetivos:

- Interface rápida
- Responsividade para dispositivos móveis
- Preparação para PWA
- Experiência simples para o usuário

---

## Backend

Tecnologias utilizadas:

- Python
- FastAPI

Objetivos:

- API REST moderna
- Alta performance
- Fácil manutenção
- Documentação automática via Swagger

---

## Banco de Dados

### PostgreSQL

Responsável por armazenar:

- Técnicos
- Setores
- Rondas
- Observações
- Auditorias
- Histórico permanente

---

## Cache e Sessões Temporárias

### Redis

Utilizado para:

- Armazenamento temporário de QR Codes
- Controle de expiração de sessões
- Tokens temporários
- Redução de carga no banco principal

---

# Estrutura do Projeto

```text
ronda-system/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── ...
│
├── backend/
│   ├── app/
│   ├── alembic/
│   └── ...
│
├── database/
│
├── docker-compose.yml
│
└── README.md
```

---

# Fluxo do Sistema

## 1. Login do Técnico

O técnico acessa o sistema utilizando suas credenciais.

Apenas técnicos possuem acesso autenticado.

---

## 2. Tela Principal

O técnico visualiza uma lista de setores disponíveis para ronda.

Cada setor possui:

- Situação do sistema
- Situação do usuário
- Observações
- Geração de QR Code

Exemplo:

| Setor | Sistema | Usuário | Observação | QR |
|---------|---------|---------|---------|---------|
| SAME | Sim/Não | Sim/Não | Texto | Gerar |
| Ambulatório | Sim/Não | Sim/Não | Texto | Gerar |
| Oncologia | Sim/Não | Sim/Não | Texto | Gerar |

---

## 3. Observações

O técnico pode registrar observações específicas para cada setor.

Essas informações ficam armazenadas para auditoria futura.

---

## 4. Geração do QR Code

Ao finalizar a validação do setor:

- Um QR Code temporário é gerado
- Possui validade limitada
- Não contém dados sensíveis
- Contém apenas um identificador temporário

Exemplo:

```text
https://dominio.com/confirm/uuid
```

---

## 5. Confirmação do Setor

Ao escanear o QR Code, o usuário do setor visualiza apenas uma tela simples:

```text
Técnico compareceu ao setor?

[ SIM ]

[ NÃO ]
```

Sem:

- Login
- Senha
- Cadastro
- Assinatura digital

---

## 6. Registro da Confirmação

Após selecionar uma opção:

O sistema:

- Valida o QR Code
- Verifica expiração
- Registra a resposta
- Atualiza o status da ronda
- Armazena dados de auditoria

---

# Auditoria

O sistema registra automaticamente:

- Endereço IP
- User-Agent
- Idioma
- Plataforma
- Timezone
- Resolução da tela
- Hardware Concurrency
- Device Memory
- Fingerprint do dispositivo

Essas informações são utilizadas apenas internamente para rastreabilidade e auditoria.

---

# Segurança

## Fingerprint

O frontend coleta dados do dispositivo e envia ao backend.

O backend gera:

```text
SHA256(device_data)
```

Objetivo:

- Identificação indireta de dispositivos
- Detecção de padrões suspeitos
- Rastreabilidade

---

## Assinatura de Sessões

Os tokens temporários utilizam:

```text
HMAC + SHA256
```

Exemplo conceitual:

```python
payload = setor + timestamp + tecnico_id

token = HMAC_SHA256(secret_key, payload)
```

A `SECRET_KEY` permanece exclusivamente no backend.

---

# Modelo de Banco de Dados

## Tecnicos

```text
id
nome
login
senha_hash
```

## Setores

```text
id
nome
```

## Rondas

```text
id
setor_id
tecnico_id
sistema_operante
usuario_utilizando
observacao
status
confirmado
criado_em
```

## Auditoria Confirmacao

```text
id
ronda_id
ip
user_agent
fingerprint_hash
device_data
confirmado_em
resposta
```

---

# MVP Atual

Funcionalidades previstas para a primeira versão:

- Login de técnico
- Cadastro de setores
- Cadastro de técnicos
- Registro de ronda
- Observações
- QR Code temporário
- Confirmação via QR
- Auditoria básica
- Persistência em PostgreSQL

---

# Funcionalidades Futuras

Planejadas para versões posteriores:

- Dashboard gerencial
- Relatórios avançados
- Indicadores operacionais
- Score antifraude
- Análise de fingerprints
- Notificações
- PWA
- Analytics

---

# Executando o Projeto

## Docker

```bash
docker compose up -d
```

---

## Backend

```bash
cd backend

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Aplicação:

```text
http://localhost:5173
```

---

# Status do Projeto

🚧 Em desenvolvimento

Atualmente sendo construída a estrutura inicial do backend, autenticação, integração com PostgreSQL, geração de QR Codes e fluxo de confirmação de rondas.
