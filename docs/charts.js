/* VigiView — tiny dependency-free SVG charts.
   Just enough to draw labelled horizontal bars and a donut. No libraries. */

"use strict";

const Charts = (() => {
  const esc = (s) =>
    String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const PALETTE = ["#0d9488", "#0ea5e9", "#6366f1", "#f59e0b", "#ef4444",
                   "#8b5cf6", "#14b8a6", "#ec4899", "#84cc16", "#64748b"];

  /* Horizontal bars — handles long labels (drug names, education levels). */
  function hbar(labels, values, opts = {}) {
    const max = Math.max(1, ...values);
    const color = opts.color || "#0d9488";
    const rowH = 30, labelW = opts.labelW || 150, barW = 240, pad = 8;
    const w = labelW + barW + 60;
    const h = labels.length * rowH + pad * 2;
    let s = `<svg viewBox="0 0 ${w} ${h}" class="chart" role="img">`;
    labels.forEach((lab, i) => {
      const y = pad + i * rowH;
      const len = (values[i] / max) * barW;
      s += `<text x="${labelW - 6}" y="${y + 19}" text-anchor="end" class="c-lab">${esc(lab)}</text>`;
      s += `<rect x="${labelW}" y="${y + 6}" width="${len.toFixed(1)}" height="16" rx="4" fill="${color}"/>`;
      s += `<text x="${labelW + len + 6}" y="${y + 19}" class="c-val">${values[i]}</text>`;
    });
    return s + "</svg>";
  }

  /* Vertical bars — used for the age histogram. */
  function vbar(labels, values, opts = {}) {
    const max = Math.max(1, ...values);
    const color = opts.color || "#0ea5e9";
    const n = labels.length, bw = 38, gap = 10, padL = 8, padB = 38, padT = 16;
    const w = padL + n * (bw + gap), h = 200;
    const chartH = h - padB - padT;
    let s = `<svg viewBox="0 0 ${w} ${h}" class="chart" role="img">`;
    labels.forEach((lab, i) => {
      const x = padL + i * (bw + gap);
      const bh = (values[i] / max) * chartH;
      const y = padT + chartH - bh;
      s += `<rect x="${x}" y="${y.toFixed(1)}" width="${bw}" height="${bh.toFixed(1)}" rx="4" fill="${color}"/>`;
      if (values[i]) s += `<text x="${x + bw / 2}" y="${y - 4}" text-anchor="middle" class="c-val">${values[i]}</text>`;
      s += `<text x="${x + bw / 2}" y="${h - 14}" text-anchor="middle" class="c-axis">${esc(lab)}</text>`;
    });
    return s + "</svg>";
  }

  /* Donut with legend — used for gender split. */
  function donut(labels, values) {
    const total = values.reduce((a, b) => a + b, 0) || 1;
    const cx = 80, cy = 80, r = 60, sw = 26;
    const circ = 2 * Math.PI * r;
    let offset = 0;
    let ring = "";
    labels.forEach((_, i) => {
      const frac = values[i] / total;
      const dash = frac * circ;
      ring += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${PALETTE[i % PALETTE.length]}"
        stroke-width="${sw}" stroke-dasharray="${dash.toFixed(2)} ${(circ - dash).toFixed(2)}"
        stroke-dashoffset="${(-offset).toFixed(2)}" transform="rotate(-90 ${cx} ${cy})"/>`;
      offset += dash;
    });
    let legend = '<div class="legend">';
    labels.forEach((lab, i) => {
      const pct = Math.round((values[i] / total) * 100);
      legend += `<div><span class="dot" style="background:${PALETTE[i % PALETTE.length]}"></span>${esc(lab)} — ${values[i]} (${pct}%)</div>`;
    });
    legend += "</div>";
    return `<div class="donut-wrap"><svg viewBox="0 0 160 160" class="donut">${ring}
      <text x="${cx}" y="${cy - 2}" text-anchor="middle" class="d-num">${total}</text>
      <text x="${cx}" y="${cy + 16}" text-anchor="middle" class="d-cap">cases</text></svg>${legend}</div>`;
  }

  return { hbar, vbar, donut, PALETTE };
})();
