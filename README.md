# 🎮 GamePrice Comparator

O **GamePrice Comparator** é uma plataforma focada em ajudar jogadores de PC a encontrarem os melhores preços de jogos nas principais lojas digitais do Brasil (Steam, Epic Games, Nuuvem e GOG).

Este projeto foi desenvolvido aplicando conceitos avançados de **AI Software Engineering** e a metodologia **Spec-Driven Development (SDD)**, onde a arquitetura, o contexto e as especificações técnicas (Specs) ditaram a geração do código.

---

## ⚙️ Como Funciona

O sistema foi arquitetado de forma minimalista, dividindo a responsabilidade em duas frentes principais:

1. **Motor de Scraping (Extração de Dados):** Scripts em Python (`requests` e `BeautifulSoup4`) que buscam os preços de forma direta e sequencial nas lojas, normalizando os resultados.
2. **API e Interface (Frontend):** Uma API rápida em `FastAPI` que serve os dados armazenados para um frontend leve feito em HTML, JavaScript puro, Tailwind CSS e Chart.js.

### 🗄️ O Banco de Dados e o Histórico de Preços

O projeto utiliza **SQLite** para garantir portabilidade e simplicidade. É importante ressaltar como o fluxo de dados funciona:

- A interface web (Frontend) **não faz buscas na internet em tempo real**. Ela apenas consulta os dados que já estão armazenados no banco de dados (`dados.db`).
- Portanto, para que um jogo apareça na busca do site, **ele precisa ter sido pesquisado e salvo no banco previamente**.

**Estratégia de Atualização:**

Em um cenário de produção ideal, o arquivo `src/atualizar_precos.py` deve ser executado de forma automatizada (via *Cron Jobs* do Linux ou *GitHub Actions*) a cada X horas. Assim, o banco se mantém atualizado de forma invisível para o usuário.

> ⚠️ **Nota sobre testes de avaliação:** Para fins de teste e apresentação deste projeto, o banco de dados foi populado manualmente executando o script de atualização para alguns jogos específicos. Por conta disso, o gráfico de "Histórico de Preços" refletirá apenas as capturas recentes, não possuindo uma linha do tempo longa (meses), já que os dados começaram a ser populados agora.

---

## 🚀 Como Rodar o Projeto Localmente

Siga os passos abaixo para configurar o ambiente e rodar o projeto na sua máquina.

### 1. Pré-requisitos

- Python 3.9+ instalado.
- Git instalado.

### 2. Instalação

Clone o repositório e acesse a pasta:

```bash
git clone https://github.com/SEU_USUARIO/nome-do-repositorio.git
cd nome-do-repositorio
```

Crie um ambiente virtual (recomendado) e ative-o:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências listadas:

```bash
pip install -r requirements.txt
```

### 3. Populando o Banco de Dados (Scraping)

Antes de abrir o site, você pode popular o banco de dados com alguns jogos. Execute o motor de scraping informando o nome do jogo desejado:

```bash
python src/atualizar_precos.py "Hollow Knight"
python src/atualizar_precos.py "Cyberpunk 2077"
```

O script irá nas lojas (Steam, Nuuvem, GOG, Epic), extrairá os valores e criará o arquivo `dados.db` automaticamente.

### 4. Iniciando o Servidor Web

Com o banco populado, inicie a API do FastAPI:

```bash
uvicorn src.main:app --reload
```

Acesse a plataforma no seu navegador:

👉 **http://localhost:8000**

---

## 📂 Estrutura do Projeto (AI-First)

Este projeto segue a estrutura baseada em contexto exigida pela disciplina:

- **`/docs/prd/`** — Product Requirements Document (Regras de negócio).
- **`/docs/specs/`** — Especificações técnicas delimitadas por domínio.
- **`/docs/plans/`** — Checklists de execução técnica passo a passo.
- **`/src/`** — Código fonte final (Scrapers, API, HTML/JS estático).
- **`agent.md`** — O "cérebro" das instruções sistêmicas para a IA.
