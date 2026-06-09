/* VigiView client — loads the sample dataset, renders the filterable case
   tables and the dashboards. Filtering + aggregation mirror vigiview/analytics.py
   so the browser shows the same numbers the API would. */

"use strict";

const $ = (s) => document.querySelector(s);
const PAGE_SIZE = 25;

const AGE_BINS = [
  ["0-10", 0, 10], ["11-20", 11, 20], ["21-30", 21, 30], ["31-40", 31, 40],
  ["41-50", 41, 50], ["51-60", 51, 60], ["61-70", 61, 70], ["71-80", 71, 80],
  ["81+", 81, 999],
];

let DATA = null, MAPS = null;
const state = { table: "Person", filters: {}, page: 1 };

/* ----------------------- table configuration ----------------------------- */
function tableConfig() {
  const m = MAPS;
  const sel = (obj) => Object.entries(obj).map(([k, v]) => ({ v: k, t: v }));
  return {
    Person: {
      rows: () => DATA.people,
      columns: [
        ["id", "ID"], ["age", "Age"], ["sex", "Sex", m.sex],
        ["qualification", "Education", m.qualification], ["country", "Country"],
        ["death", "Death", m.yes_no], ["disability", "Disability", m.yes_no],
      ],
      filters: [
        { k: "id", label: "ID", type: "number" },
        { k: "age_min", label: "Min age", type: "number" },
        { k: "age_max", label: "Max age", type: "number" },
        { k: "sex", label: "Sex", type: "select", opts: sel(m.sex) },
        { k: "qualification", label: "Education", type: "select", opts: sel(m.qualification) },
        { k: "country", label: "Country", type: "text" },
        { k: "death", label: "Death", type: "select", opts: sel(m.yes_no) },
        { k: "disability", label: "Disability", type: "select", opts: sel(m.yes_no) },
      ],
    },
    Product: {
      rows: () => DATA.products,
      columns: [["id", "ID"], ["product", "Drug"]],
      filters: [
        { k: "id", label: "ID", type: "number" },
        { k: "product", label: "Drug name", type: "text" },
      ],
    },
    Injection: {
      rows: () => DATA.injections,
      columns: [["id", "ID"], ["drug", "Risk category", m.drug_risk], ["injection", "Formulation", m.injection_type]],
      filters: [
        { k: "id", label: "ID", type: "number" },
        { k: "drug", label: "Risk category", type: "select", opts: sel(m.drug_risk) },
        { k: "injection", label: "Formulation", type: "select", opts: sel(m.injection_type) },
      ],
    },
  };
}

/* ----------------------------- filtering ---------------------------------- */
function applyFilters(rows) {
  const f = state.filters;
  const has = (k) => f[k] !== undefined && f[k] !== "";
  return rows.filter((r) => {
    if (has("id") && r.id !== +f.id) return false;
    if (has("age_min") && (r.age == null || r.age < +f.age_min)) return false;
    if (has("age_max") && (r.age == null || r.age > +f.age_max)) return false;
    if (has("sex") && r.sex !== +f.sex) return false;
    if (has("qualification") && r.qualification !== +f.qualification) return false;
    if (has("country") && !(r.country || "").toLowerCase().includes(f.country.toLowerCase())) return false;
    if (has("death") && r.death !== +f.death) return false;
    if (has("disability") && r.disability !== +f.disability) return false;
    if (has("product") && !r.product.toLowerCase().includes(f.product.toLowerCase())) return false;
    if (has("drug") && r.drug !== +f.drug) return false;
    if (has("injection") && r.injection !== +f.injection) return false;
    return true;
  });
}

/* --------------------------- explore view --------------------------------- */
function renderFilters() {
  const cfg = tableConfig()[state.table];
  $("#filters").innerHTML = cfg.filters
    .map((fl) => {
      const val = state.filters[fl.k] ?? "";
      if (fl.type === "select") {
        const opts = ['<option value="">Any</option>']
          .concat(fl.opts.map((o) => `<option value="${o.v}" ${String(val) === o.v ? "selected" : ""}>${o.t}</option>`))
          .join("");
        return `<label class="f"><span>${fl.label}</span><select data-k="${fl.k}">${opts}</select></label>`;
      }
      return `<label class="f"><span>${fl.label}</span><input data-k="${fl.k}" type="${fl.type}" value="${val}" /></label>`;
    })
    .join("") + '<button id="clearF" class="btn small ghost">Clear</button>';

  $("#filters").querySelectorAll("[data-k]").forEach((el) => {
    el.addEventListener("input", () => {
      state.filters[el.dataset.k] = el.value;
      state.page = 1;
      renderTable();
    });
  });
  $("#clearF").addEventListener("click", () => {
    state.filters = {};
    state.page = 1;
    renderFilters();
    renderTable();
  });
}

function renderTable() {
  const cfg = tableConfig()[state.table];
  const filtered = applyFilters(cfg.rows());
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  state.page = Math.min(state.page, pages);
  const start = (state.page - 1) * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);

  $("#dataTable thead").innerHTML =
    "<tr>" + cfg.columns.map((c) => `<th>${c[1]}</th>`).join("") + "</tr>";
  $("#dataTable tbody").innerHTML = slice
    .map((r) => "<tr>" + cfg.columns.map((c) => {
      const raw = r[c[0]];
      const disp = c[2] ? (c[2][raw] ?? "—") : (raw ?? "—");
      return `<td>${disp}</td>`;
    }).join("") + "</tr>")
    .join("");

  $("#resultCount").textContent = `${filtered.length} record${filtered.length === 1 ? "" : "s"}`;
  $("#pageInfo").textContent = `Page ${state.page} / ${pages}`;
  $("#prev").disabled = state.page <= 1;
  $("#next").disabled = state.page >= pages;
}

/* --------------------------- dashboards ----------------------------------- */
function personStats(people) {
  const ages = people.map((p) => p.age).filter((a) => a != null);
  const age_counts = AGE_BINS.map(([, lo, hi]) => ages.filter((a) => a >= lo && a <= hi).length);
  const count = (key, val) => people.filter((p) => p[key] === val).length;
  const genderKeys = Object.keys(MAPS.sex).map(Number).filter((k) => count("sex", k));
  const qualKeys = Object.keys(MAPS.qualification).map(Number).filter((k) => count("qualification", k));
  const cc = {};
  people.forEach((p) => { if (p.country) cc[p.country] = (cc[p.country] || 0) + 1; });
  const topC = Object.entries(cc).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const n = people.length || 1;
  return {
    age_counts,
    gender_labels: genderKeys.map((k) => MAPS.sex[k]),
    gender_counts: genderKeys.map((k) => count("sex", k)),
    qual_labels: qualKeys.map((k) => MAPS.qualification[k]),
    qual_counts: qualKeys.map((k) => count("qualification", k)),
    country_labels: topC.map((e) => e[0]),
    country_counts: topC.map((e) => e[1]),
    death_rate: Math.round((1000 * count("death", 1)) / n) / 10,
    disability_rate: Math.round((1000 * count("disability", 1)) / n) / 10,
    total: people.length,
  };
}

function productStats(products) {
  const c = {};
  products.forEach((p) => { c[p.product] = (c[p.product] || 0) + 1; });
  const sorted = Object.entries(c).sort((a, b) => b[1] - a[1]);
  const labels = [], counts = [];
  let other = 0;
  sorted.forEach(([name, n]) => (n > 1 ? (labels.push(name), counts.push(n)) : (other += n)));
  if (other) { labels.push("Other"); counts.push(other); }
  return { labels, counts };
}

function injectionStats(injections) {
  const by = (key, map) => {
    const c = {};
    injections.forEach((i) => { if (i[key]) c[i[key]] = (c[i[key]] || 0) + 1; });
    const sorted = Object.entries(c).sort((a, b) => b[1] - a[1]);
    return { labels: sorted.map((e) => map[e[0]]), counts: sorted.map((e) => e[1]) };
  };
  return { risk: by("drug", MAPS.drug_risk), type: by("injection", MAPS.injection_type) };
}

function renderDashboards() {
  const ps = personStats(DATA.people);
  const prod = productStats(DATA.products);
  const inj = injectionStats(DATA.injections);

  $("#kpis").innerHTML = [
    ["Total cases", ps.total, "#0d9488"],
    ["Reported deaths", ps.death_rate + "%", "#ef4444"],
    ["Reported disability", ps.disability_rate + "%", "#f59e0b"],
    ["Distinct drugs", new Set(DATA.products.map((p) => p.product)).size, "#6366f1"],
  ].map(([k, v, c]) => `<div class="kpi"><div class="kpi-v" style="color:${c}">${v}</div><div class="kpi-k">${k}</div></div>`).join("");

  $("#ageChart").innerHTML = Charts.vbar(AGE_BINS.map((b) => b[0]), ps.age_counts, { color: "#0ea5e9" });
  $("#genderChart").innerHTML = Charts.donut(ps.gender_labels, ps.gender_counts);
  $("#qualChart").innerHTML = Charts.hbar(ps.qual_labels, ps.qual_counts, { color: "#6366f1", labelW: 130 });
  $("#countryChart").innerHTML = Charts.hbar(ps.country_labels, ps.country_counts, { color: "#0d9488", labelW: 50 });
  $("#productChart").innerHTML = Charts.hbar(prod.labels, prod.counts, { color: "#14b8a6", labelW: 130 });
  $("#riskChart").innerHTML = Charts.hbar(inj.risk.labels, inj.risk.counts, { color: "#f59e0b", labelW: 220 });
  $("#typeChart").innerHTML = Charts.hbar(inj.type.labels, inj.type.counts, { color: "#8b5cf6", labelW: 220 });
}

/* ------------------------------ wiring ------------------------------------ */
function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
  $("#explore").hidden = tab !== "explore";
  $("#dashboards").hidden = tab !== "dashboards";
  if (tab === "dashboards") renderDashboards();
}

function init() {
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchTab(t.dataset.tab)));
  $("#tableSeg").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => {
      $("#tableSeg").querySelector(".active").classList.remove("active");
      b.classList.add("active");
      state.table = b.dataset.table;
      state.filters = {};
      state.page = 1;
      renderFilters();
      renderTable();
    }));
  $("#prev").addEventListener("click", () => { state.page--; renderTable(); });
  $("#next").addEventListener("click", () => { state.page++; renderTable(); });

  renderFilters();
  renderTable();
}

fetch("data/faers_sample.json")
  .then((r) => r.json())
  .then((d) => { DATA = d; MAPS = d.meta.maps; init(); })
  .catch((e) => { $("#explore").innerHTML = `<p class="err">Could not load dataset: ${e}</p>`; });
