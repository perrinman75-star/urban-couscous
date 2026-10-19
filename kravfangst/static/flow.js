// Live-förhandsvisning av triage och prioscore. Servern räknar alltid om vid sparning.
(function () {
  const names = {
    A: "Tjänst A – Större initiativ",
    B: "Tjänst B – Mindre vidareutveckling",
  };

  const verdict = document.getElementById("verdict");
  if (verdict) {
    const radios = document.querySelectorAll(".question input[type=radio]");
    const update = () => {
      const groups = new Set([...radios].map((r) => r.name));
      const answers = [...groups].map((g) => {
        const checked = document.querySelector(`input[name="${g}"]:checked`);
        return checked ? checked.value : null;
      });
      let service = null;
      if (answers.every((a) => a)) service = answers.includes("ja") ? "A" : "B";
      verdict.classList.toggle("A", service === "A");
      document.getElementById("verdict-service").textContent = service ? `Tjänst ${service}` : "–";
      document.getElementById("verdict-name").textContent = service ? names[service] : "Besvara alla frågor";
    };
    radios.forEach((r) => r.addEventListener("change", update));
    update();
  }

  const tiles = document.getElementById("score-tiles");
  if (tiles) {
    const out = (k, v) => { tiles.querySelector(`[data-out="${k}"]`).textContent = v; };
    const fmt = (v) => (v === null ? "–" : String(Math.round(v * 100) / 100).replace(".", ","));
    const weighted = (group, lo, hi) => {
      const inputs = document.querySelectorAll(`input[data-group="${group}"]`);
      let sum = 0;
      for (const i of inputs) {
        const v = parseFloat(i.value);
        if (Number.isNaN(v) || v < lo || v > hi) return null;
        sum += v * parseFloat(i.dataset.weight);
      }
      return inputs.length ? sum : null;
    };
    const update = () => {
      const v = weighted("v", 1, 10);
      const c = weighted("c", 1, 10);
      const s = weighted("s", 0, 100);
      const k = s === null ? null : s / 100;
      const p = v === null || c === null || k === null ? null : (v * k) / c;
      out("v", fmt(v)); out("c", fmt(c)); out("s", fmt(s)); out("k", fmt(k)); out("p", fmt(p));
      let level = "Värde × koeff. ÷ komplexitet";
      if (p !== null) level = p >= 1.5 ? "Hög prioritet" : p >= 1 ? "Prioritera vid kapacitet" : "Utmana eller omforma";
      out("l", level);
    };
    document.querySelectorAll("input[data-group]").forEach((i) => i.addEventListener("input", update));
    update();
  }
})();
