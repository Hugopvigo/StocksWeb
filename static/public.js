(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var state = { assets: [], selected: null, days: 365 };
  var chartSvg = $("chart");
  var tooltip = $("tt");

  function text(tag, cls, value) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (value != null) n.textContent = value;
    return n;
  }

  function money(v, cur) {
    if (v == null) return "—";
    var symbol = { USD: "$", EUR: "€", GBP: "£" }[cur] || "";
    return symbol + Charts.fmtPrice(v);
  }

  function changeNode(pct, cls) {
    if (pct == null) return text("div", cls || "w-chg flat", "—");
    var sign = pct > 0 ? "+" : "";
    var tone = pct > 0 ? "up" : pct < 0 ? "down" : "flat";
    return text("div", "w-chg " + tone, sign + Charts.fmtPrice(pct) + " %");
  }

  function formatUpdated(iso) {
    if (!iso) return "—";
    var d = new Date(iso);
    if (isNaN(d)) return "—";
    return d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  }

  function sliceByRange(history, days) {
    if (!days || !history.length) return history;
    var last = new Date(history[history.length - 1].date + "T00:00:00");
    var from = new Date(last.getTime() - days * 86400000);
    return history.filter(function (p) { return new Date(p.date + "T00:00:00") >= from; });
  }

  function renderSummary(data) {
    $("s-count").textContent = data.assets.length;
    $("s-mix").textContent = (data.by_kind.stock || 0) + " / " + (data.by_kind.etf || 0);
    $("s-updated").textContent = formatUpdated(data.updated_at);
  }

  function renderDist(data) {
    var box = $("dist");
    box.textContent = "";
    var stocks = data.by_kind.stock || 0;
    var etfs = data.by_kind.etf || 0;
    var total = stocks + etfs;
    if (!total) { box.appendChild(text("div", "empty", "Sin activos")); return; }

    var bar = text("div", "dist-bar");
    var a = text("span", "dist-stock"); a.style.width = (stocks / total * 100) + "%";
    var b = text("span", "dist-etf"); b.style.width = (etfs / total * 100) + "%";
    bar.appendChild(a); bar.appendChild(b); box.appendChild(bar);

    var legend = text("div", "dist-legend");
    var l1 = text("span"); l1.appendChild(text("i", "dot dist-stock")); l1.appendChild(document.createTextNode("Acciones · " + stocks));
    var l2 = text("span"); l2.appendChild(text("i", "dot dist-etf")); l2.appendChild(document.createTextNode("ETFs · " + etfs));
    legend.appendChild(l1); legend.appendChild(l2); box.appendChild(legend);
  }

  function renderWatchlist() {
    var box = $("watchlist");
    box.textContent = "";
    if (!state.assets.length) {
      box.appendChild(text("div", "empty", "Todavía no hay activos. Añádelos desde Administrar."));
      return;
    }
    state.assets.forEach(function (asset) {
      var row = document.createElement("button");
      row.type = "button";
      row.className = "w-row";
      row.setAttribute("aria-current", asset.ticker === state.selected ? "true" : "false");

      var left = text("div");
      left.appendChild(text("div", "w-name", asset.name || asset.ticker));
      left.appendChild(text("div", "w-tick", asset.ticker.toUpperCase() + " · " + (asset.kind === "etf" ? "ETF" : "Acción")));

      var right = text("div", "w-right");
      var sparkWrap = text("div", "w-spark");
      var spark = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      sparkWrap.appendChild(spark);
      var figs = text("div", "w-figs");
      figs.appendChild(text("div", "w-price", money(asset.price, asset.currency)));
      figs.appendChild(changeNode(asset.change_pct));
      right.appendChild(sparkWrap); right.appendChild(figs);

      row.appendChild(left); row.appendChild(right);
      row.addEventListener("click", function () { select(asset.ticker); });
      box.appendChild(row);
      Charts.renderSpark(spark, asset.history.slice(-40));
    });
  }

  function selectedAsset() {
    return state.assets.find(function (a) { return a.ticker === state.selected; }) || state.assets[0] || null;
  }

  function renderChart() {
    var asset = selectedAsset();
    if (!asset) {
      $("c-name").textContent = "—";
      $("c-tick").textContent = "";
      $("c-price").textContent = "—";
      $("c-chg").textContent = "";
      Charts.renderLine(chartSvg, []);
      return;
    }
    $("c-name").textContent = asset.name || asset.ticker;
    $("c-tick").textContent = asset.ticker.toUpperCase();
    $("c-price").textContent = money(asset.price, asset.currency);
    var chg = $("c-chg");
    chg.textContent = asset.change_pct == null ? "" : (asset.change_pct > 0 ? "+" : "") + Charts.fmtPrice(asset.change_pct) + " % hoy";
    chg.className = "chg " + (asset.change_pct > 0 ? "up" : asset.change_pct < 0 ? "down" : "flat");

    var points = sliceByRange(asset.history, state.days);
    Charts.renderLine(chartSvg, points, {
      onHover: function (p, x, y) {
        tooltip.textContent = "";
        tooltip.appendChild(text("span", "d", p.date));
        tooltip.appendChild(document.createTextNode(money(p.close, asset.currency)));
        tooltip.style.left = Math.max(0, x - 60) + "px";
        tooltip.style.top = Math.max(0, y - 46) + "px";
        tooltip.classList.add("show");
      },
      onLeave: function () { tooltip.classList.remove("show"); }
    });
  }

  function select(ticker) {
    state.selected = ticker;
    renderWatchlist();
    renderChart();
  }

  document.querySelectorAll(".range").forEach(function (btn) {
    btn.addEventListener("click", function () {
      state.days = parseInt(btn.dataset.days, 10);
      document.querySelectorAll(".range").forEach(function (b) { b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
      $("range-hint").textContent = state.days === 365 ? "Último año" : state.days === 0 ? "Todo el histórico" : "Últimos " + state.days + " días";
      renderChart();
    });
  });

  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderChart, 120);
  });

  fetch("/api/public/dashboard")
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      state.assets = data.assets || [];
      state.selected = state.assets.length ? state.assets[0].ticker : null;
      renderSummary(data);
      renderDist(data);
      renderWatchlist();
      renderChart();
    })
    .catch(function () {
      $("watchlist").appendChild(text("div", "empty", "No se pudieron cargar los datos. Inténtalo de nuevo en unos momentos."));
    });
})();
