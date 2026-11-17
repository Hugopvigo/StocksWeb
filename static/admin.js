(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var form = $("asset-form");
  var editing = null;

  function text(tag, cls, value) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (value != null) n.textContent = value;
    return n;
  }

  function money(v, cur) {
    if (v == null) return "—";
    var symbol = { USD: "$", EUR: "€", GBP: "£" }[cur] || "";
    return symbol + v.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function cell(row, cls, value) {
    var isNode = value != null && value.nodeType != null;
    var td = text("td", cls || null, isNode ? null : (value == null ? null : String(value)));
    if (isNode) td.appendChild(value);
    row.appendChild(td);
    return td;
  }

  function pnlCell(value, cur) {
    var cls = value > 0 ? "up" : value < 0 ? "down" : "flat";
    return text("span", cls + " num", (value > 0 ? "+" : "") + money(value, cur));
  }

  function renderTotals(data) {
    var t = data.totals || {};
    $("t-value").textContent = money(t.value);
    $("t-cost").textContent = money(t.cost);
    $("t-pnl").textContent = money(t.pnl);
    var pct = $("t-pct");
    pct.textContent = t.pnl_pct == null ? "—" : (t.pnl_pct > 0 ? "+" : "") + t.pnl_pct + " %";
    pct.className = "value num " + (t.pnl_pct > 0 ? "up" : t.pnl_pct < 0 ? "down" : "flat");
  }

  function renderRows(data) {
    var body = $("rows");
    body.textContent = "";
    (data.assets || []).forEach(function (a) {
      var tr = document.createElement("tr");

      var first = cell(tr);
      first.appendChild(text("div", "t-name", a.name || a.ticker.toUpperCase()));
      var tickLine = text("div", "t-tick", a.ticker.toUpperCase() + (a.kind === "etf" ? " · ETF" : ""));
      first.appendChild(tickLine);
      if (a.override_price != null) first.appendChild(text("span", "override-tag", "● manual"));

      cell(tr, "num", a.quantity);
      cell(tr, "num", money(a.avg_buy));
      cell(tr, "num", money(a.price, a.currency));
      var chg = a.change_pct == null ? null : text("span", (a.change_pct > 0 ? "up" : a.change_pct < 0 ? "down" : "flat") + " num", (a.change_pct > 0 ? "+" : "") + a.change_pct.toFixed(2) + " %");
      cell(tr, null, chg);
      cell(tr, "num", money(a.value, a.currency));
      cell(tr, null, pnlCell(a.pnl, a.currency));

      var actions = cell(tr);
      var box = text("div", "row-actions");
      var edit = text("button", "btn btn-sm", "Editar");
      edit.type = "button";
      edit.addEventListener("click", function () { fillForm(a); });
      var del = text("button", "btn btn-danger btn-sm", "Eliminar");
      del.type = "button";
      del.addEventListener("click", function () { remove(a.ticker, a.name || a.ticker); });
      box.appendChild(edit); box.appendChild(del);
      actions.appendChild(box);
      body.appendChild(tr);
    });
    if (!(data.assets || []).length) {
      var trEmpty = document.createElement("tr");
      var td = document.createElement("td");
      td.colSpan = 8;
      td.className = "empty";
      td.textContent = "Todavía no hay activos. Añade el primero con el formulario de arriba.";
      trEmpty.appendChild(td);
      body.appendChild(trEmpty);
    }
  }

  function renderStatus(data) {
    var box = $("status");
    box.textContent = "";
    var updated = data.updated_at ? new Date(data.updated_at).toLocaleString("es-ES") : "nunca";
    box.appendChild(document.createTextNode("Última actualización: " + updated));
    var withErrors = (data.assets || []).filter(function (a) { return a.error; });
    if (withErrors.length) {
      box.appendChild(text("span", "sep", " · "));
      box.appendChild(text("span", "err", withErrors.length + " activo(s) con datos no disponibles: " + withErrors.map(function (a) { return a.ticker; }).join(", ")));
    }
  }

  function fillForm(a) {
    editing = a.ticker;
    $("f-ticker").value = a.ticker;
    $("f-name").value = a.name || "";
    $("f-kind").value = a.kind;
    $("f-qty").value = a.quantity;
    $("f-buy").value = a.avg_buy;
    $("f-override").value = a.override_price == null ? "" : a.override_price;
    $("save-btn").textContent = "Guardar cambios";
    $("cancel-btn").hidden = false;
    $("form-title").textContent = "Editar activo";
    $("form-mode").textContent = a.ticker.toUpperCase();
    form.scrollIntoView({ behavior: "smooth", block: "start" });
    $("f-name").focus();
  }

  function resetForm() {
    editing = null;
    form.reset();
    $("save-btn").textContent = "Guardar activo";
    $("cancel-btn").hidden = true;
    $("form-title").textContent = "Añadir activo";
    $("form-mode").textContent = "Nuevo activo";
  }

  function load() {
    fetch("/api/admin/dashboard")
      .then(function (r) { if (r.status === 401) throw new Error("Sesión caducada, vuelve a introducir la contraseña."); if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        renderTotals(data);
        renderRows(data);
        renderStatus(data);
      })
      .catch(function (e) {
        $("status").textContent = e.message;
      });
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var payload = {
      ticker: $("f-ticker").value.trim().toLowerCase(),
      name: $("f-name").value.trim(),
      kind: $("f-kind").value,
      quantity: $("f-qty").value,
      avg_buy: $("f-buy").value,
      override_price: $("f-override").value
    };
    var btn = $("save-btn");
    btn.disabled = true; btn.textContent = "Guardando…";
    fetch("/api/admin/assets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { if (!r.ok) throw new Error("No se pudo guardar"); return r.json(); })
      .then(function () { resetForm(); load(); })
      .catch(function (e) { btn.textContent = "Error al guardar"; setTimeout(function () { btn.textContent = editing ? "Guardar cambios" : "Guardar activo"; }, 2000); })
      .finally(function () { btn.disabled = false; });
  });

  $("cancel-btn").addEventListener("click", resetForm);

  function remove(ticker, name) {
    if (!window.confirm("¿Eliminar " + name + " (" + ticker.toUpperCase() + ")?")) return;
    fetch("/api/admin/assets/" + encodeURIComponent(ticker), { method: "DELETE" })
      .then(function (r) { if (!r.ok) throw new Error("No se pudo eliminar"); load(); })
      .catch(function (e) { $("status").textContent = e.message; });
  }

  $("refresh-btn").addEventListener("click", function () {
    var btn = $("refresh-btn");
    btn.disabled = true; btn.textContent = "Actualizando…";
    fetch("/api/admin/refresh", { method: "POST" })
      .then(function (r) { if (!r.ok) throw new Error("No se pudo actualizar"); return r.json(); })
      .then(function (result) { load(); btn.textContent = "Actualizado ✓"; setTimeout(function () { btn.textContent = "Actualizar precios"; }, 1800); })
      .catch(function (e) { btn.textContent = "Error"; $("status").textContent = e.message; setTimeout(function () { btn.textContent = "Actualizar precios"; }, 2000); })
      .finally(function () { btn.disabled = false; });
  });

  load();
})();
