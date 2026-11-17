/* Gráficos SVG propios: línea principal con ejes/crosshair y sparklines. */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var uid = 0;

  function make(tag, attrs, parent) {
    var node = document.createElementNS(NS, tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(node);
    return node;
  }

  function clear(svg) { while (svg.firstChild) svg.removeChild(svg.firstChild); }

  function fmtPrice(v) {
    if (v == null) return "—";
    return v.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtDate(s) {
    if (!s) return "";
    var p = s.split("-");
    return p.length === 3 ? p[2] + "/" + p[1] : s;
  }

  function path(points, x, y) {
    return points.map(function (p, i) {
      return (i ? "L" : "M") + x(i).toFixed(2) + " " + y(p.close).toFixed(2);
    }).join(" ");
  }

  function renderLine(svg, points, options) {
    options = options || {};
    clear(svg);
    var W = svg.clientWidth || 640;
    var H = svg.clientHeight || 260;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);

    if (!points || !points.length) {
      make("text", { x: W / 2, y: H / 2, fill: "#657488", "text-anchor": "middle", "font-size": "13" }, svg)
        .textContent = "Sin datos históricos todavía";
      return null;
    }

    var showGrid = options.showGrid !== false;
    var color = options.color || "#e3b341";
    var left = 8, right = showGrid ? 54 : 8, top = 12, bottom = 24;
    var plotW = Math.max(1, W - left - right);
    var plotH = Math.max(1, H - top - bottom);
    var vals = points.map(function (p) { return p.close; });
    var min = Math.min.apply(null, vals);
    var max = Math.max.apply(null, vals);
    var span = max - min || Math.abs(max) * 0.01 || 1;
    min -= span * 0.12;
    max += span * 0.12;

    var n = points.length;
    var x = function (i) { return n === 1 ? left + plotW / 2 : left + (i * plotW) / (n - 1); };
    var y = function (v) { return top + ((max - v) / (max - min)) * plotH; };

    if (showGrid) {
      for (var g = 0; g <= 4; g++) {
        var val = min + ((max - min) * g) / 4;
        var gy = top + plotH - (g * plotH) / 4;
        make("line", { x1: left, y1: gy, x2: left + plotW, y2: gy, stroke: "#2a3644", "stroke-width": "1" }, svg);
        make("text", { x: W - 2, y: gy + 3.5, fill: "#657488", "font-size": "11", "text-anchor": "end", "font-family": "ui-monospace, monospace" }, svg)
          .textContent = fmtPrice(val);
      }
    }

    var id = "grad" + (++uid);
    var defs = make("defs", null, svg);
    var grad = make("linearGradient", { id: id, x1: "0", y1: "0", x2: "0", y2: "1" }, defs);
    make("stop", { offset: "0%", "stop-color": color, "stop-opacity": "0.26" }, grad);
    make("stop", { offset: "100%", "stop-color": color, "stop-opacity": "0" }, grad);

    var line = path(points, x, y);
    make("path", { d: line + " L" + x(n - 1).toFixed(2) + " " + (top + plotH) + " L" + x(0).toFixed(2) + " " + (top + plotH) + " Z", fill: "url(#" + id + ")" }, svg);
    make("path", { d: line, fill: "none", stroke: color, "stroke-width": "2", "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);

    var last = points[n - 1];
    make("circle", { cx: x(n - 1), cy: y(last.close), r: "3.5", fill: color, stroke: "#0f151d", "stroke-width": "2" }, svg);

    if (showGrid) {
      make("text", { x: left, y: H - 5, fill: "#657488", "font-size": "11", "font-family": "ui-monospace, monospace" }, svg).textContent = fmtDate(points[0].date);
      var lastLabel = make("text", { x: left + plotW, y: H - 5, fill: "#657488", "font-size": "11", "text-anchor": "end", "font-family": "ui-monospace, monospace" }, svg);
      lastLabel.textContent = fmtDate(last.date);
      if (n > 2) {
        var mid = Math.floor(n / 2);
        make("text", { x: x(mid), y: H - 5, fill: "#657488", "font-size": "11", "text-anchor": "middle", "font-family": "ui-monospace, monospace" }, svg).textContent = fmtDate(points[mid].date);
      }
    }

    var cross = make("line", { x1: 0, y1: top, x2: 0, y2: top + plotH, stroke: "#93a1b1", "stroke-width": "1", "stroke-dasharray": "3 3", opacity: "0" }, svg);
    var dot = make("circle", { cx: 0, cy: 0, r: "4", fill: color, stroke: "#0f151d", "stroke-width": "2", opacity: "0" }, svg);
    var overlay = make("rect", { x: left, y: top, width: plotW, height: plotH, fill: "transparent" }, svg);

    overlay.addEventListener("pointermove", function (ev) {
      var box = svg.getBoundingClientRect();
      var px = ((ev.clientX - box.left) / box.width) * W;
      var i = Math.round(((px - left) / plotW) * (n - 1));
      i = Math.max(0, Math.min(n - 1, i));
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("opacity", "1");
      dot.setAttribute("cx", x(i)); dot.setAttribute("cy", y(points[i].close)); dot.setAttribute("opacity", "1");
      if (options.onHover) options.onHover(points[i], (x(i) / W) * box.width, (y(points[i].close) / H) * box.height);
    });
    overlay.addEventListener("pointerleave", function () {
      cross.setAttribute("opacity", "0"); dot.setAttribute("opacity", "0");
      if (options.onLeave) options.onLeave();
    });
    return { x: x, y: y };
  }

  function renderSpark(svg, points) {
    clear(svg);
    var W = svg.clientWidth || 62, H = svg.clientHeight || 26;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    if (!points || points.length < 2) return;
    var vals = points.map(function (p) { return p.close; });
    var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
    var span = max - min || 1;
    var up = vals[vals.length - 1] >= vals[0];
    var color = up ? "#3fd08a" : "#f0756b";
    var pad = 3;
    var x = function (i) { return pad + (i * (W - 2 * pad)) / (vals.length - 1); };
    var y = function (v) { return pad + ((max - v) / span) * (H - 2 * pad); };
    var d = vals.map(function (v, i) { return (i ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); }).join(" ");
    make("path", { d: d, fill: "none", stroke: color, "stroke-width": "1.6", "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
  }

  window.Charts = { renderLine: renderLine, renderSpark: renderSpark, fmtPrice: fmtPrice };
})();
