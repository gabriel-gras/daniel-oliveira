# Spec 01: Extração de Dados (Scraping de Lojas de PC)

## 1. Objetivo
Criar rotinas simples de extração de dados para buscar os preços dos jogos exclusivamente nas 4 principais lojas de PC do Brasil: Steam, Epic Games, Nuuvem e GOG.

## 2. Abordagem Tecnológica Minimalista
* **Linguagem:** Python
* **Bibliotecas:** `requests` para baixar as páginas/APIs e `BeautifulSoup4` para ler o HTML estático.
* **Complexidade reduzida:** Sem uso de ferramentas pesadas de simulação de navegador (como Playwright ou Selenium) para manter a execução rápida e simples.

## 3. Lojas e Estratégia de Captura
* **Steam:** Utilizar a API oficial pública (`store.steampowered.com/api`).
* **GOG:** Utilizar a API pública da loja.
* **Epic Games:** Realizar requisições diretas no endpoint GraphQL da loja.
* **Nuuvem:** Fazer o parsing direto do HTML da página de busca usando BeautifulSoup.

## 4. Normalização de Dados
Independente da loja, o script de extração deve retornar sempre um formato simples:
`{ "jogo": "Nome", "loja": "Steam", "preco_atual": 199.90, "moeda": "BRL", "link": "url" }`