/* 시연 ④ v3 — 좌측 14건 목록 + 우측 단일 카드.
 * 흐름:
 *  - 진입 → GET /eval-set → 좌측 목록 채움 (정답 정보만)
 *  - 좌측 클릭 → 우측에 그 건의 정답 carded 표시 (LLM 영역은 "실행 대기" 표시)
 *  - "▶ 선택 1건 실행" → POST /run-one → 우측 LLM 영역 채워짐 + 좌측 행 색 라벨
 *  - "⏵ 14건 전체 실행" → SSE /run → 모든 행 차례로 채움 */

(() => {
  "use strict";

  const VERDICT_LABEL = {
    pass:    { txt: "✓", cls: "pass",    big: "✓ 키워드 통과" },
    partial: { txt: "⚠", cls: "partial", big: "⚠ 부분 일치" },
    fail:    { txt: "✗", cls: "fail",    big: "✗ 실패" },
  };
  const EXEC_LABEL = {
    first_try: "✓ 1회 성공",
    retry:     "🔁 자가 수정",
    fallback:  "🔄 Fallback",
    failure:   "❌ 거절·실패",
  };

  const state = {
    cases: [],
    results: {},   // id → case_done 데이터
    selectedId: null,
    inProgress: false,
    es: null,
    counts: { pass: 0, partial: 0, fail: 0, first_try: 0, retry: 0, fallback: 0, failure: 0 },
    done: 0,
  };

  const els = {
    list: document.getElementById("case-list"),
    runOneBtn: document.getElementById("run-one-btn"),
    runAllBtn: document.getElementById("run-all-btn"),
    placeholder: document.getElementById("detail-placeholder"),
    body: document.getElementById("detail-body"),
    sideSummary: document.getElementById("side-summary"),
    kwPass: document.getElementById("kw-pass"),
    kwPartial: document.getElementById("kw-partial"),
    kwFail: document.getElementById("kw-fail"),
    exFirst: document.getElementById("ex-first"),
    exRetry: document.getElementById("ex-retry"),
    exFallback: document.getElementById("ex-fallback"),
    exFailure: document.getElementById("ex-failure"),
    miniFill: document.getElementById("mini-fill"),
    miniLabel: document.getElementById("mini-label"),
    modal: document.getElementById("graph-modal"),
    modalSub: document.getElementById("graph-modal-sub"),
    modalBody: document.getElementById("graph-modal-body"),
  };

  function escapeHTML(s) {
    return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function caseItemHTML(c) {
    return `
      <li class="case-item" data-id="${escapeHTML(c.id)}">
        <span class="case-id">${escapeHTML(c.id)}</span>
        <span class="case-diff">${c.difficulty}</span>
        <span class="case-q" title="${escapeHTML(c.question)}">${escapeHTML(c.question)}</span>
        <span class="case-verdict empty" data-role="verdict">·</span>
      </li>`;
  }

  function renderCaseList() {
    els.list.innerHTML = state.cases.map(caseItemHTML).join("");
    els.list.querySelectorAll(".case-item").forEach((li) => {
      li.addEventListener("click", () => selectCase(li.dataset.id));
    });
  }

  function selectCase(id) {
    state.selectedId = id;
    els.list.querySelectorAll(".case-item").forEach((li) => {
      li.classList.toggle("is-active", li.dataset.id === id);
    });
    els.runOneBtn.disabled = false;
    renderDetail();
  }

  function chipExpected(kw, hits) {
    if (!hits) return `<span class="kw-chip expected">${escapeHTML(kw)}</span>`;
    const cls = hits.includes(kw) ? "hit" : "miss";
    const icon = cls === "hit" ? "✓" : "✗";
    return `<span class="kw-chip ${cls}">${icon} ${escapeHTML(kw)}</span>`;
  }

  function chipForbidden(kw, violations) {
    if (!violations) return `<span class="kw-chip forbidden">${escapeHTML(kw)}</span>`;
    const cls = violations.includes(kw) ? "violation" : "clean";
    const icon = cls === "violation" ? "⚠" : "✓";
    return `<span class="kw-chip ${cls}">${icon} ${escapeHTML(kw)}</span>`;
  }

  function renderFacts(result) {
    if (!result || result.length === 0) return `<div class="facts-empty">조회 결과 없음</div>`;
    return result.slice(0, 5).map((row) => {
      const lines = Object.entries(row).map(
        ([k, v]) => `<div class="facts-row"><span class="fact-k">${escapeHTML(k)}:</span><span class="fact-v">${escapeHTML(typeof v === "number" ? String(v) : String(v))}</span></div>`
      ).join("");
      return `<div style="border-bottom: 1px dashed var(--border); padding: 4px 0;">${lines}</div>`;
    }).join("") + (result.length > 5 ? `<div class="facts-empty">… 외 ${result.length - 5}건</div>` : "");
  }

  function renderDetail() {
    if (!state.selectedId) return;
    const c = state.cases.find((x) => x.id === state.selectedId);
    if (!c) return;
    const r = state.results[c.id];
    els.placeholder.hidden = true;
    els.body.hidden = false;

    // 정답 영역 + (결과 있으면 LLM 영역)
    const expChips = (c.golden.expected_keywords || []).map((k) => chipExpected(k, r?.matches?.expected_hits)).join("");
    const forChips = (c.golden.forbidden_keywords || []).map((k) => chipForbidden(k, r?.matches?.forbidden_violations)).join("");

    const verdictKind = r?.matches?.keyword_verdict;
    const verdictLabel = verdictKind ? VERDICT_LABEL[verdictKind] : null;
    const verdictHTML = verdictLabel
      ? `<span class="compare-verdict ${verdictLabel.cls}">${verdictLabel.big}</span>`
      : state.inProgress
        ? `<span class="compare-verdict running">⏳ 실행 중</span>`
        : `<span class="compare-verdict pending">대기</span>`;

    let genHTML;
    if (r) {
      const g = r.generated || {};
      const x = r.execution || {};
      const advisoryChips = (g.advisory || []).map((a) => {
        let ac = "alert";
        if (a.includes("MOCK")) ac = "mock";
        else if (a.includes("안전") || a.includes("⛔")) ac = "hazard";
        return `<span class="advisory-chip ${ac}">${escapeHTML(a)}</span>`;
      }).join("");
      const attemptLabel = g.attempt === "fallback" ? "예비 답안 (golden)" : `시도 ${g.attempt ?? "—"}`;
      const hasGraph = (g.result_count ?? 0) > 0;
      const graphBtnHTML = hasGraph
        ? `<button type="button" class="btn-graph-view" data-role="open-graph">🔎 그래프에서 보기</button>`
        : "";
      genHTML = `
        <div class="compare-label">LLM 생성 TypeQL (${escapeHTML(attemptLabel)})</div>
        <div class="typeql-mini">${escapeHTML(g.typeql || "(생성 실패)")}</div>

        <div class="compare-label compare-label-row">
          <span>그래프에서 조회된 사실 (${g.result_count ?? 0}건)</span>
          ${graphBtnHTML}
        </div>
        <div class="facts-list">${renderFacts(g.result || [])}</div>

        <div class="compare-label">자연어 답변</div>
        <div class="compare-answer">${escapeHTML(g.answer || "")}</div>
        ${advisoryChips ? `<div class="advisory-row" style="margin-top:6px;">${advisoryChips}</div>` : ""}

        <div class="match-summary">
          <span class="match-line">키워드: <strong>${escapeHTML(r.matches?.keyword_summary || "")}</strong></span>
          <span class="summary-divider">|</span>
          <span class="match-line">실행: <strong>${escapeHTML(EXEC_LABEL[x.outcome] || x.outcome || "")} (${escapeHTML(x.summary || "")})</strong></span>
        </div>
      `;
    } else {
      genHTML = `<div style="color: var(--text-muted); font-size: 14px; padding: 24px 0;">▶ 실행 버튼을 누르면 AI가 그래프에 질의하고 답변까지 만들어 비교 결과를 표시합니다.</div>`;
    }

    els.body.innerHTML = `
      <header class="compare-head">
        <span class="compare-id">${escapeHTML(c.id)}</span>
        <span class="compare-difficulty">난이도 ${c.difficulty} · ${escapeHTML(c.category)}</span>
        ${verdictHTML}
      </header>
      <div class="compare-question">${escapeHTML(c.question)}</div>
      <div class="compare-cols">
        <div class="compare-col golden">
          <h4>정답 (Golden)</h4>
          <span class="ontology-path">${escapeHTML(c.golden.ontology_path || "(경로 없음)")}</span>
          <div class="compare-label">정답 TypeQL</div>
          <div class="typeql-mini">${escapeHTML(c.golden.typeql || "")}</div>
          <div class="compare-label">기대 키워드</div>
          <div class="keyword-chip-row">${expChips || '<span class="facts-empty">(없음)</span>'}</div>
          <div class="compare-label">금지어</div>
          <div class="keyword-chip-row">${forChips || '<span class="facts-empty">(없음)</span>'}</div>
        </div>
        <div class="compare-col generated">
          <h4>LLM 생성</h4>
          ${genHTML}
        </div>
      </div>
    `;

    const openBtn = els.body.querySelector('[data-role="open-graph"]');
    if (openBtn) {
      openBtn.addEventListener("click", () => openGraphModal(c, r));
    }
  }

  // === 그래프 시각화 모달 (B안) ===
  // result row의 dict에서 entity 식별자 후보를 뽑아 노드 헤더로 사용
  const ID_KEYS = ["id", "segment-id", "segment_id", "source-id", "source_id"];
  const NAME_KEYS = ["name", "segment-name", "segment_name", "source-name", "source_name"];

  function pickRowHeader(row, index) {
    for (const k of ID_KEYS) {
      if (row[k] !== undefined && row[k] !== null && row[k] !== "") return { key: k, value: row[k] };
    }
    for (const k of NAME_KEYS) {
      if (row[k] !== undefined && row[k] !== null && row[k] !== "") return { key: k, value: row[k] };
    }
    return { key: "row", value: `#${index + 1}` };
  }

  function inferEntityType(ontologyPath, headerKey) {
    const path = (ontologyPath || "").toLowerCase();
    const key = (headerKey || "").toLowerCase();
    if (key.startsWith("source") || path.startsWith("source")) return "Source";
    if (key.startsWith("segment") || path.startsWith("segment")) return "Segment";
    if (path.startsWith("runcontext") || path.startsWith("run-context")) return "RunContext";
    if (path.startsWith("threshold") || path.startsWith("weight")) return "ConfigSet";
    if (path.startsWith("decision")) return "Decision";
    return "Entity";
  }

  // expected keyword 중 attribute 값을 강조해야 하는 것 골라내기 ('A|B' → ['A','B'])
  function expandExpected(expected) {
    const out = [];
    for (const kw of expected || []) {
      const parts = String(kw).includes("|") ? String(kw).split("|") : [String(kw)];
      for (const p of parts) if (p) out.push(p);
    }
    return out;
  }

  function attrIsHighlighted(value, expectedFlat) {
    const v = String(value ?? "");
    if (!v) return false;
    return expectedFlat.some((kw) => v.includes(kw));
  }

  function buildAttributeChip(key, value, expectedFlat) {
    const highlight = attrIsHighlighted(value, expectedFlat);
    const cls = highlight ? "attr-chip is-match" : "attr-chip";
    const star = highlight ? `<span class="attr-mark" title="기대 키워드와 일치">✦</span>` : "";
    return `
      <li class="${cls}">
        <span class="attr-key">${escapeHTML(key)}</span>
        <span class="attr-arrow">→</span>
        <span class="attr-val">${escapeHTML(String(value ?? ""))}</span>
        ${star}
      </li>`;
  }

  function buildRowNode(row, index, expectedFlat, ontologyPath) {
    const header = pickRowHeader(row, index);
    const entityType = inferEntityType(ontologyPath, header.key);
    const attrEntries = Object.entries(row);
    const attrItems = attrEntries
      .map(([k, v]) => buildAttributeChip(k, v, expectedFlat))
      .join("");
    const headerValDisplay = header.key === "row" ? "" : ` <span class="row-node-id">${escapeHTML(String(header.value))}</span>`;
    return `
      <div class="row-node">
        <div class="row-node-head">
          <span class="row-node-badge">${escapeHTML(entityType)}</span>
          <span class="row-node-label">row ${index + 1}${headerValDisplay}</span>
        </div>
        <div class="row-node-trunk" aria-hidden="true"></div>
        <ul class="row-node-attrs">
          ${attrItems || '<li class="attr-chip is-empty">(attribute 없음)</li>'}
        </ul>
      </div>`;
  }

  function openGraphModal(c, r) {
    const g = r?.generated || {};
    const rows = Array.isArray(g.result) ? g.result : [];
    const ontologyPath = c.golden?.ontology_path || "(경로 미정)";
    const expectedFlat = expandExpected(c.golden?.expected_keywords || []);
    const hits = r?.matches?.expected_hits || [];

    const hitsHTML = (c.golden?.expected_keywords || [])
      .map((kw) => {
        const cls = hits.includes(kw) ? "kw-chip hit" : "kw-chip miss";
        const icon = hits.includes(kw) ? "✓" : "✗";
        return `<span class="${cls}">${icon} ${escapeHTML(kw)}</span>`;
      })
      .join("");

    const rowsHTML = rows.length
      ? rows.map((row, i) => buildRowNode(row, i, expectedFlat, ontologyPath)).join("")
      : `<div class="graph-empty">조회 결과가 없습니다.</div>`;

    els.modalSub.textContent = `${c.id} · ${c.question}`;
    els.modalBody.innerHTML = `
      <section class="graph-section">
        <h3 class="graph-section-title">온톨로지 경로</h3>
        <div class="ontology-path-big">${escapeHTML(ontologyPath)}</div>
      </section>

      <section class="graph-section">
        <h3 class="graph-section-title">기대 키워드 ↔ 답변 매칭</h3>
        <div class="keyword-chip-row">${hitsHTML || '<span class="facts-empty">(없음)</span>'}</div>
        <p class="graph-hint">아래 노드 중 <span class="attr-mark inline">✦</span> 마크는 기대 키워드와 일치한 attribute입니다.</p>
      </section>

      <section class="graph-section">
        <h3 class="graph-section-title">그래프 조회 결과 (${rows.length}건)</h3>
        <div class="row-nodes">${rowsHTML}</div>
      </section>
    `;

    els.modal.hidden = false;
    document.body.classList.add("modal-open");
    // 닫기 버튼/배경 바인딩 (이미 있는 요소라 한 번만)
    if (!els.modal.dataset.bound) {
      els.modal.querySelectorAll('[data-role="modal-close"]').forEach((el) => {
        el.addEventListener("click", closeGraphModal);
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !els.modal.hidden) closeGraphModal();
      });
      els.modal.dataset.bound = "1";
    }
  }

  function closeGraphModal() {
    els.modal.hidden = true;
    document.body.classList.remove("modal-open");
  }

  function applyVerdictToListRow(id, verdictKind) {
    const li = els.list.querySelector(`.case-item[data-id="${id}"]`);
    if (!li) return;
    li.classList.remove("is-done-pass", "is-done-partial", "is-done-fail", "is-running");
    if (verdictKind) {
      li.classList.add(`is-done-${verdictKind}`);
      const verdict = li.querySelector('[data-role="verdict"]');
      const v = VERDICT_LABEL[verdictKind];
      verdict.className = `case-verdict ${v.cls}`;
      verdict.textContent = v.txt;
    }
  }

  function setRunningRow(id) {
    const li = els.list.querySelector(`.case-item[data-id="${id}"]`);
    if (!li) return;
    li.classList.add("is-running");
    const verdict = li.querySelector('[data-role="verdict"]');
    verdict.className = "case-verdict running";
    verdict.textContent = "⏳";
  }

  function clearRunningRow(id) {
    const li = els.list.querySelector(`.case-item[data-id="${id}"]`);
    if (li) li.classList.remove("is-running");
  }

  // === API ===
  async function loadEvalSet() {
    const res = await fetch("/api/demo4/eval-set");
    const data = await res.json();
    state.cases = data.cases || [];
    renderCaseList();
  }

  async function runOne() {
    if (!state.selectedId) return;
    state.inProgress = true;
    els.runOneBtn.disabled = true;
    els.runAllBtn.disabled = true;
    setRunningRow(state.selectedId);
    renderDetail();

    try {
      const res = await fetch("/api/demo4/run-one", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: state.selectedId }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      const result = await res.json();
      const wasNew = !state.results[state.selectedId];
      state.results[state.selectedId] = result;
      // 카운트 갱신 — 이미 결과 있는 건은 카운트에 미반영 (덮어쓰기만)
      if (wasNew) {
        state.counts[result.matches.keyword_verdict] += 1;
        state.counts[result.execution.outcome] += 1;
        state.done += 1;
        updateSummary();
      }
      applyVerdictToListRow(state.selectedId, result.matches.keyword_verdict);
      clearRunningRow(state.selectedId);
    } catch (err) {
      clearRunningRow(state.selectedId);
      alert(`실행 실패: ${err.message}`);
    } finally {
      state.inProgress = false;
      els.runOneBtn.disabled = !state.selectedId;
      els.runAllBtn.disabled = false;
      renderDetail();
    }
  }

  function runAll() {
    state.inProgress = true;
    els.runOneBtn.disabled = true;
    els.runAllBtn.disabled = true;
    els.runAllBtn.textContent = "평가 중…";
    // 결과·카운트 리셋
    state.results = {};
    state.counts = { pass: 0, partial: 0, fail: 0, first_try: 0, retry: 0, fallback: 0, failure: 0 };
    state.done = 0;
    updateSummary();
    els.list.querySelectorAll(".case-item").forEach((li) => {
      li.classList.remove("is-done-pass", "is-done-partial", "is-done-fail", "is-running");
      const verdict = li.querySelector('[data-role="verdict"]');
      verdict.className = "case-verdict empty";
      verdict.textContent = "·";
    });

    const es = new EventSource("/api/demo4/run");
    state.es = es;
    es.onmessage = (e) => {
      let ev;
      try { ev = JSON.parse(e.data); } catch { return; }
      if (ev.type === "case_start") {
        setRunningRow(ev.id);
      } else if (ev.type === "case_done") {
        clearRunningRow(ev.id);
        state.results[ev.id] = ev;
        const v = ev.matches?.keyword_verdict;
        const x = ev.execution?.outcome;
        if (v) state.counts[v] = (state.counts[v] || 0) + 1;
        if (x) state.counts[x] = (state.counts[x] || 0) + 1;
        state.done += 1;
        applyVerdictToListRow(ev.id, v);
        updateSummary();
        if (state.selectedId === ev.id) renderDetail();
      } else if (ev.type === "finished") {
        es.close();
        state.es = null;
        state.inProgress = false;
        els.runOneBtn.disabled = !state.selectedId;
        els.runAllBtn.disabled = false;
        els.runAllBtn.textContent = "⏵ 14건 전체 실행";
        if (ev.keyword_stats) {
          state.counts.pass = ev.keyword_stats.pass || 0;
          state.counts.partial = ev.keyword_stats.partial || 0;
          state.counts.fail = ev.keyword_stats.fail || 0;
        }
        if (ev.execution_stats) {
          Object.assign(state.counts, ev.execution_stats);
        }
        updateSummary();
      } else if (ev.type === "error") {
        es.close();
        state.es = null;
        state.inProgress = false;
        els.runOneBtn.disabled = !state.selectedId;
        els.runAllBtn.disabled = false;
        els.runAllBtn.textContent = "⏵ 14건 전체 실행";
        alert("평가 중단: " + (ev.message || "오류"));
      }
    };
    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) {
        es.close();
        state.es = null;
        if (state.inProgress) {
          state.inProgress = false;
          els.runAllBtn.disabled = false;
          els.runAllBtn.textContent = "⏵ 14건 전체 실행";
        }
      }
    };
  }

  function updateSummary() {
    els.sideSummary.hidden = state.done === 0;
    els.kwPass.textContent = state.counts.pass;
    els.kwPartial.textContent = state.counts.partial;
    els.kwFail.textContent = state.counts.fail;
    els.exFirst.textContent = state.counts.first_try;
    els.exRetry.textContent = state.counts.retry;
    els.exFallback.textContent = state.counts.fallback;
    els.exFailure.textContent = state.counts.failure;
    const total = state.cases.length;
    const pct = total > 0 ? (state.done / total) * 100 : 0;
    els.miniFill.style.width = `${pct}%`;
    els.miniLabel.textContent = `${state.done}/${total}`;
  }

  els.runOneBtn.addEventListener("click", runOne);
  els.runAllBtn.addEventListener("click", runAll);

  loadEvalSet().catch((err) => {
    els.list.innerHTML = `<li><div class="error-box"><strong>로드 실패</strong>${escapeHTML(err.message)}</div></li>`;
  });
})();
