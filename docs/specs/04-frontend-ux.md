# Spec 04: Interface de Usuário (Frontend)

## 1. Objetivo
Criar uma interface web simples, focada apenas em uma barra de pesquisa central, exibição da comparação de preços e do gráfico de histórico.

## 2. Abordagem Tecnológica Minimalista
* **Framework:** HTML/JS puro ou um framework simplificado como React (Vite) + Tailwind CSS (para facilitar o design responsivo).
* **Gráficos:** Utilização da biblioteca `Recharts` ou `Chart.js` para renderizar o gráfico temporal do Histórico de Preços.

## 3. Comportamento da Interface
1. **Home:** Limpa, com uma grande barra de busca (estilo Google).
2. **Página de Resultados:**
   * Foto e nome do jogo.
   * Lista de lojas ordenadas do menor para o maior preço, com um distintivo (badge) de "Melhor Preço" na primeira opção.
   * Um botão clicável "Comprar" que redireciona o usuário para a página oficial da loja.
   * Abaixo da lista, o gráfico de linha simples mostrando a variação do preço ao longo dos dias.