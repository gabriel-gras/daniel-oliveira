# Plano de Execução 03: Frontend (Interface do Usuário)

## Objetivo
Criar uma interface web simples e estática que consuma a API FastAPI existente, permitindo que o usuário busque um jogo, veja a tabela de comparação de preços e um gráfico com o histórico.

## Contexto Necessário para a IA
- Arquivo de leitura obrigatória: `docs/specs/04-frontend-ux.md`.
- A API responde nos endpoints locais: `http://localhost:8000/api/search?q=...` e `http://localhost:8000/api/prices/{id_jogo}`.

## Checklist de Implementação (Passo a Passo)

- [ ] **Passo 1: Estrutura Base (`src/static/index.html`)**
  - O FastAPI deve ser configurado no `main.py` para servir arquivos estáticos de uma pasta `src/static/`.
  - Criar o `index.html` consumindo o Tailwind CSS via CDN (sem Node.js/NPM, para manter minimalista).
  - Incluir a biblioteca `Chart.js` via CDN para o gráfico.

- [ ] **Passo 2: Layout da Home**
  - Barra superior de busca (título "GamePrice Comparator" e um campo de input).
  - Área central dividida em duas colunas (ou responsiva):
    1. Tabela de Lojas vs Preços (ordenada do menor para o maior, com link de compra).
    2. Área para o Gráfico de Histórico de Preços.

- [ ] **Passo 3: Lógica JS (`src/static/app.js`)**
  - Criar função que dispara ao dar "Enter" na busca, chamando o endpoint `/api/search`.
  - Com o ID do jogo retornado, chamar `/api/prices` para popular a tabela e renderizar o gráfico do Chart.js.