// ---------------------------------------------------------------------------
// GamePrice Comparator — lógica de frontend (sem build step, JS puro)
// ---------------------------------------------------------------------------

const el = {
  viewHome: document.getElementById("view-home"),
  viewResults: document.getElementById("view-results"),
  backBtn: document.getElementById("back-btn"),

  searchForm: document.getElementById("search-form"),
  searchInput: document.getElementById("search-input"),
  homeStatus: document.getElementById("home-status"),
  chips: document.querySelectorAll(".chip"),

  gameCover: document.getElementById("game-cover"),
  gameCoverFallback: document.getElementById("game-cover-fallback"),
  gameTitle: document.getElementById("game-title"),
  priceList: document.getElementById("price-list"),
  chartSection: document.getElementById("chart-section"),
  priceChartCanvas: document.getElementById("price-chart"),
  resultsStatus: document.getElementById("results-status"),
};

let chartInstance = null;

const CORES_LOJAS = ["#F5A623", "#3DD68C", "#5B8DEF", "#E85D75", "#9B7EDE", "#4FD1C5"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatarPreco(valor) {
  if (valor === null || valor === undefined) return "—";
  return Number(valor).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function formatarData(isoString) {
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return isoString;
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

function mostrarView(view) {
  if (view === "home") {
    el.viewHome.classList.remove("hidden");
    el.viewResults.classList.add("hidden");
    el.backBtn.classList.add("hidden");
  } else {
    el.viewHome.classList.add("hidden");
    el.viewResults.classList.remove("hidden");
    el.backBtn.classList.remove("hidden");
  }
}

// ---------------------------------------------------------------------------
// Busca
// ---------------------------------------------------------------------------

async function buscarJogo(termo) {
  el.homeStatus.textContent = "escaneando lojas...";

  try {
    const resBusca = await fetch(`/api/search?q=${encodeURIComponent(termo)}`);
    if (!resBusca.ok) throw new Error(`busca falhou (status ${resBusca.status})`);

    const resultados = await resBusca.json();
    if (!resultados.length) {
      el.homeStatus.textContent = "nenhum jogo encontrado. tente outro termo_";
      return;
    }

    const jogoEncontrado = resultados[0];
    el.homeStatus.textContent = "";

    await carregarPrecos(jogoEncontrado.id);
  } catch (erro) {
    console.error(erro);
    el.homeStatus.textContent = "falha ao conectar à api. verifique se o servidor está rodando_";
  }
}

async function carregarPrecos(idJogo) {
  el.resultsStatus.textContent = "";
  el.priceList.innerHTML = "";
  destruirGrafico();

  mostrarView("results");

  el.resultsStatus.textContent = "carregando ofertas...";

  try {
    const res = await fetch(`/api/prices/${idJogo}`);
    if (!res.ok) throw new Error(`falha ao buscar preços (status ${res.status})`);

    const dados = await res.json();
    el.resultsStatus.textContent = "";

    renderJogo(dados.jogo);
    renderOfertas(dados.ofertas_atuais || []);
    renderGrafico(dados.historico || []);
  } catch (erro) {
    console.error(erro);
    el.resultsStatus.textContent = "não foi possível carregar os preços deste jogo_";
  }
}

// ---------------------------------------------------------------------------
// Renderização
// ---------------------------------------------------------------------------

function renderJogo(jogo) {
  el.gameTitle.textContent = jogo.nome;

  if (jogo.capa_url) {
    el.gameCover.src = jogo.capa_url;
    el.gameCover.alt = `Capa de ${jogo.nome}`;
    el.gameCover.classList.remove("hidden");
    el.gameCoverFallback.classList.add("hidden");
    el.gameCover.onerror = () => {
      el.gameCover.classList.add("hidden");
      el.gameCoverFallback.classList.remove("hidden");
    };
  } else {
    el.gameCover.classList.add("hidden");
    el.gameCoverFallback.classList.remove("hidden");
  }
}

function renderOfertas(ofertas) {
  el.priceList.innerHTML = "";

  if (!ofertas.length) {
    const li = document.createElement("li");
    li.className = "px-5 py-6 font-mono text-xs text-muted text-center";
    li.textContent = "nenhuma oferta encontrada para este jogo ainda_";
    el.priceList.appendChild(li);
    return;
  }

  const ordenadas = [...ofertas].sort((a, b) => a.preco - b.preco);

  ordenadas.forEach((oferta, indice) => {
    const li = document.createElement("li");
    li.className = "relative flex items-center justify-between gap-4 px-5 py-4";
    if (indice === 0) li.classList.add("bg-gold/5");

    const ladoEsquerdo = document.createElement("div");
    ladoEsquerdo.className = "flex items-center gap-3";

    const ponto = document.createElement("span");
    ponto.className = "w-2 h-2 rounded-full";
    ponto.style.backgroundColor = CORES_LOJAS[indice % CORES_LOJAS.length];
    ladoEsquerdo.appendChild(ponto);

    const nomeLoja = document.createElement("span");
    nomeLoja.className = "font-mono text-sm uppercase tracking-wide";
    nomeLoja.textContent = oferta.loja;
    ladoEsquerdo.appendChild(nomeLoja);

    if (indice === 0) {
      const selo = document.createElement("span");
      selo.className =
        "stamp font-mono text-[10px] uppercase tracking-widest text-mint border border-dashed border-mint rounded px-2 py-0.5 ml-2";
      selo.textContent = "melhor preço";
      ladoEsquerdo.appendChild(selo);
    }

    const ladoDireito = document.createElement("div");
    ladoDireito.className = "flex items-center gap-4";

    const preco = document.createElement("span");
    preco.className = `font-mono text-base font-semibold ${indice === 0 ? "text-gold" : "text-ink"}`;
    preco.textContent = formatarPreco(oferta.preco);
    ladoDireito.appendChild(preco);

    const botaoComprar = document.createElement("a");
    botaoComprar.href = oferta.url_compra || "#";
    botaoComprar.target = "_blank";
    botaoComprar.rel = "noopener noreferrer";
    botaoComprar.className =
      "font-mono text-xs uppercase tracking-wide bg-surface border border-line rounded px-3 py-1.5 hover:border-gold hover:text-gold transition-colors";
    botaoComprar.textContent = "comprar →";
    ladoDireito.appendChild(botaoComprar);

    li.appendChild(ladoEsquerdo);
    li.appendChild(ladoDireito);
    el.priceList.appendChild(li);
  });
}

function destruirGrafico() {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

function renderGrafico(historico) {
  destruirGrafico();

  if (!historico.length) {
    el.chartSection.classList.add("hidden");
    return;
  }
  el.chartSection.classList.remove("hidden");

  const lojas = [...new Set(historico.map((h) => h.loja))];
  const datas = [...new Set(historico.map((h) => h.data_captura))].sort();

  const datasets = lojas.map((loja, indice) => {
    const pontosLoja = historico.filter((h) => h.loja === loja);
    const dados = datas.map((data) => {
      const ponto = pontosLoja.find((p) => p.data_captura === data);
      return ponto ? ponto.preco : null;
    });

    const cor = CORES_LOJAS[indice % CORES_LOJAS.length];
    return {
      label: loja,
      data: dados,
      borderColor: cor,
      backgroundColor: `${cor}22`,
      spanGaps: true,
      tension: 0.3,
      pointRadius: 3,
      pointHoverRadius: 5,
    };
  });

  chartInstance = new Chart(el.priceChartCanvas, {
    type: "line",
    data: {
      labels: datas.map(formatarData),
      datasets,
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#8B92A0",
            font: { family: "JetBrains Mono", size: 11 },
            boxWidth: 10,
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatarPreco(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: "#2A2F3855" },
          ticks: { color: "#8B92A0", font: { family: "JetBrains Mono", size: 10 } },
        },
        y: {
          grid: { color: "#2A2F3855" },
          ticks: {
            color: "#8B92A0",
            font: { family: "JetBrains Mono", size: 10 },
            callback: (valor) => formatarPreco(valor),
          },
        },
      },
    },
  });
}

// ---------------------------------------------------------------------------
// Eventos
// ---------------------------------------------------------------------------

el.searchForm.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const termo = el.searchInput.value.trim();
  if (!termo) return;
  buscarJogo(termo);
});

el.chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    const termo = chip.dataset.chip;
    el.searchInput.value = termo;
    buscarJogo(termo);
  });
});

el.backBtn.addEventListener("click", () => {
  mostrarView("home");
  el.searchInput.value = "";
  el.searchInput.focus();
  destruirGrafico();
});