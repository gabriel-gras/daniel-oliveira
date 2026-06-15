# Spec 03: API de Comunicação (Backend)

## 1. Objetivo
Criar uma API leve e rápida que leia os dados do arquivo SQLite e entregue para a interface visual de forma padronizada.

## 2. Abordagem Tecnológica Minimalista
* **Framework:** FastAPI (Python)
* **Por que?** É o framework moderno mais rápido e simples de configurar em Python, além de gerar a documentação da API automaticamente, facilitando o teste durante o desenvolvimento com IA.

## 3. Endpoints Necessários
Serão necessários apenas 2 endpoints para o sistema funcionar:
* `GET /api/search?q={nome_do_jogo}`
  * Retorna as informações básicas do jogo pesquisado.
* `GET /api/prices/{id_jogo}`
  * Retorna todas as ofertas atuais (para a tabela comparativa) e o histórico de preços dos últimos meses (para gerar o gráfico da interface).

## 4. Retorno Rápido
Como a API apenas consulta um arquivo SQLite local, a resposta não deve depender de scraping em tempo real, garantindo uma resposta em poucos milissegundos para o usuário.