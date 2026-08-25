<div align="center">
  <img src="frontend/logo.png" width="120" />
  <h1>KAIRUS</h1>
  <p>Plataforma de inteligencia artificial construida do zero com Python, FastAPI e JavaScript puro.</p>

  ![Versao](https://img.shields.io/badge/versão-0.4.0-e0343f)
  ![Python](https://img.shields.io/badge/Python-3.13-3776ab)
  ![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)
  ![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange)
</div>

---

## 📌 Sobre

KAIRUS e um assistente de IA conversacional com identidade propria, desenvolvido como um projeto full-stack completo. Ele usa um **modelo hibrido**: um motor de regras por intencao para interacoes conhecidas (saudacoes, identidade, ferramentas) e um **LLM real via OpenRouter** para perguntas abertas — com **failover automatico entre 5 modelos gratuitos**.

## ✨ Funcionalidades

- 🔐 **Autenticacao JWT** com senhas hasheadas em bcrypt
- 👥 **Multiusuario**: cada usuario com historico isolado
- 💬 **Streaming em tempo real** (Server-Sent Events) com efeito de digitacao
- 🤖 **Failover automatico**: se um modelo de IA cair, o proximo assume
- 🧠 **Memoria de conversa**: lembra nome, sentimento e contexto
- 🎯 **Motor hibrido**: regras por intencao + LLM
- 🛠️ **Ferramentas internas** extensiveis
- 🛡️ **Seguranca**: rate limiting, sanizacao de input e isolamento por usuario
- 🎨 **Interface premium**: tema preto/vermelho, animacoes e sidebar colapsavel
- 💾 **Persistencia em SQLite**

## 🧱 Stack Tecnologica

| Camada    | Tecnologia                          |
|-----------|-------------------------------------|
| Backend   | Python 3.13 + FastAPI               |
| Server    | Uvicorn (ASGI)                      |
| IA        | OpenRouter (LLM) com failover       |
| Auth      | PyJWT + bcrypt                      |
| Banco     | SQLite                              |
| Frontend  | HTML, CSS e JavaScript (vanilla)    |
| Testes    | pytest                              |

## 🚀 Como executar

### Pre-requisitos

- Python 3.13+
- Chave de API gratuita do OpenRouter → https://openrouter.ai

### Instalacao

```bash
git clone https://github.com/GB-H/KAIRUS.git
cd KAIRUS
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuracao

```bash
copy .env.example .env
```

Edite o `.env` com a sua chave do OpenRouter.

### Iniciar

```bash
uvicorn backend.main:app --reload
```

Acesse **http://127.0.0.1:8000**

## 📁 Estrutura do projeto

```text
KAIRUS/
├── ai/                  # Motor de inteligencia
│   ├── engine.py        # Orquestrador hibrido (regras + LLM)
│   ├── intents.py       # Classificacao de intencao
│   ├── llm.py           # Cliente LLM com failover
│   ├── memory.py        # Memoria de conversa
│   ├── context.py       # Nome, sentimento, repeticao
│   ├── tools.py         # Ferramentas internas
│   ├── responses.py     # Banco de respostas
│   └── personality.py   # Identidade e versao
├── backend/
│   ├── main.py          # Aplicacao FastAPI
│   ├── auth.py          # JWT + bcrypt
│   ├── middleware.py    # Rate limit e sanizacao
│   ├── database/db.py   # Persistencia SQLite
│   └── routes/          # Endpoints da API
├── frontend/            # Interface (HTML/CSS/JS)
├── tests/               # Testes automatizados
└── .env                 # Segredos (nunca commitado)
```

## 🔌 API principal

| Metodo | Endpoint                   | Descricao                        | Auth |
|--------|----------------------------|----------------------------------|------|
| POST   | /api/auth/register         | Cria usuario                     | ❌   |
| POST   | /api/auth/login            | Login, retorna JWT               | ❌   |
| POST   | /api/chat/stream           | Resposta via SSE (streaming)     | ✅   |
| POST   | /api/chat                  | Resposta via JSON                | ✅   |
| GET    | /api/conversations         | Lista conversas do usuario       | ✅   |
| DELETE | /api/conversations/{id}    | Exclui conversa                  | ✅   |
| GET    | /api/health                | Saude do servidor                | ❌   |

## 🧠 Como o motor de IA funciona

```text
Entrada do usuario
   │
   ▼
Sanizacao + rate limit (middleware)
   │
   ▼
Classificacao de intencao
   ├─ Intencao conhecida → motor de regras (resposta imediata)
   └─ Desconhecida ──────→ LLM via OpenRouter
                             ├─ Failover entre 5 modelos
                             ├─ Extracao <thinking> / <answer>
                             └─ Streaming SSE com digitacao
```

## 🔐 Seguranca

- Senhas hasheadas com **bcrypt** (nunca em texto puro)
- Tokens **JWT** com expiracao de 7 dias
- **Rate limiting** contra abuso
- **Sanizacao de input** contra injecao
- **Isolamento por usuario**: acessar conversa alheia retorna 403
- Segredos em `.env`, fora do repositorio

## 🗺️ Roadmap

- [x] Motor de conversa com memoria
- [x] Integracao LLM com failover
- [x] Streaming em tempo real
- [x] Autenticacao JWT
- [ ] Responsivo / mobile
- [ ] Deploy em producao

## 👨💻 Autor

**Gabriel** — [github.com/GB-H](https://github.com/GB-H)

---

<div align="center">KAIRUS v0.4.0 — construido com Python e determinacao.</div>