/* 시연 ② 정책 외부화 — 동적 토글 + CRUD.
 * - 진입 시 GET /threshold-versions로 그래프의 모든 버전을 로드해 토글 동적 생성
 * - 토글 클릭 → 해당 버전 임계값 적용 (슬라이더·매핑 갱신)
 * - 슬라이더 조작 → 즉시 매핑 갱신, "편집 중" 표시 (저장은 별도)
 * - "+ 새 버전 저장" → 이름 입력 → POST save-thresholds → 토글에 추가
 * - 보호 외 버전 옆 × 버튼 → DELETE → 토글에서 제거 */

(() => {
  "use strict";

  const STATE_LABELS = {
    GeneralManagement:    { ko: "일반 관리", color: "#86C99A", textOn: "#1F2937" },
    EnhancedMonitoring:   { ko: "감시 강화", color: "#F4C84A", textOn: "#1F2937" },
    ReviewPreWatering:    { ko: "검토 예비", color: "#F08C3A", textOn: "#FFFFFF" },
    PriorityPreWatering:  { ko: "우선 예비", color: "#D9442C", textOn: "#FFFFFF" },
    ImmediatePreWatering: { ko: "즉시 예비", color: "#8B1E1A", textOn: "#FFFFFF" },
  };
  const STATE_ORDER = [
    "GeneralManagement",
    "EnhancedMonitoring",
    "ReviewPreWatering",
    "PriorityPreWatering",
    "ImmediatePreWatering",
  ];

  const state = {
    segments: [],
    missing: [],
    versions: [],                                                   // [{version, thresholds, is_protected}]
    activeVersion: null,                                            // 현재 선택된 버전 (null이면 편집 중)
    thresholds: { low: 0.2, mid_low: 0.4, mid_high: 0.6, high: 0.8 },
    v1Cache: null,                                                  // {seg_id: stateKey} v1 기준
    isEditing: false,                                               // 슬라이더 편집 중 (토글 어느 것에도 매칭 안 됨)
  };

  const els = {
    toggleRow: document.getElementById("version-toggle-row"),
    sourcePill: document.getElementById("source-pill"),
    editPill: document.getElementById("edit-pill"),
    colorbar: document.getElementById("colorbar"),
    missingBanner: document.getElementById("missing-banner"),
    mappingRows: document.getElementById("mapping-rows"),
    sliders: document.querySelectorAll("input.threshold-slider"),
    sliderValues: document.querySelectorAll("[data-value]"),
    insertHint: document.getElementById("insert-typeql-hint"),
    insertTokens: {
      "set-id": document.querySelector('[data-ins="set-id"]'),
      version: document.querySelector('[data-ins="version"]'),
      low: document.querySelector('[data-ins="low"]'),
      mid_low: document.querySelector('[data-ins="mid_low"]'),
      mid_high: document.querySelector('[data-ins="mid_high"]'),
      high: document.querySelector('[data-ins="high"]'),
    },
  };

  // === 매핑 함수 (graph_inference.s_priority_to_state 미러) ===
  function sPriorityToState(sp, th) {
    if (sp < th.low) return "GeneralManagement";
    if (sp < th.mid_low) return "EnhancedMonitoring";
    if (sp < th.mid_high) return "ReviewPreWatering";
    if (sp < th.high) return "PriorityPreWatering";
    return "ImmediatePreWatering";
  }

  function bandIndex(stateKey) { return STATE_ORDER.indexOf(stateKey); }

  function escapeHTML(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // === API ===
  async function loadSegments() {
    const res = await fetch("/api/demo2/segments-with-priority");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.segments = data.segments || [];
    state.missing = data.missing || [];
  }

  async function loadVersions() {
    const res = await fetch("/api/demo2/threshold-versions");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.versions = data.versions || [];
  }

  async function saveVersion(version, thresholds) {
    const res = await fetch("/api/demo2/save-thresholds", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version, thresholds }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const detail = data.detail || {};
      const err = new Error(detail.message || `HTTP ${res.status}`);
      err.hint = detail.hint_for_presenter;
      throw err;
    }
    return res.json();
  }

  async function deleteVersion(version) {
    const res = await fetch(`/api/demo2/thresholds/${encodeURIComponent(version)}`, { method: "DELETE" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const detail = data.detail || {};
      const err = new Error(detail.message || `HTTP ${res.status}`);
      throw err;
    }
    return res.json();
  }

  // === 토글 동적 생성 ===
  function renderToggleRow() {
    els.toggleRow.innerHTML = "";
    state.versions.forEach((v) => {
      const wrap = document.createElement("span");
      wrap.className = "version-chip-wrap";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "toggle-btn";
      if (v.version === state.activeVersion && !state.isEditing) btn.classList.add("is-active");
      if (v.is_protected) btn.classList.add("protected");
      btn.dataset.version = v.version;
      btn.textContent = v.version + (v.is_protected ? " 🔒" : "");
      btn.addEventListener("click", () => applyVersion(v.version));
      wrap.appendChild(btn);

      if (!v.is_protected) {
        const del = document.createElement("button");
        del.type = "button";
        del.className = "version-delete-btn";
        del.title = `${v.version} 삭제`;
        del.textContent = "×";
        del.addEventListener("click", (e) => {
          e.stopPropagation();
          confirmDelete(v.version);
        });
        wrap.appendChild(del);
      }

      els.toggleRow.appendChild(wrap);
    });

    // "+ 새 버전 저장" 버튼
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "version-add-btn";
    addBtn.textContent = "+ 새 버전 저장";
    addBtn.addEventListener("click", promptSaveNew);
    els.toggleRow.appendChild(addBtn);
  }

  async function applyVersion(version) {
    const v = state.versions.find((x) => x.version === version);
    if (!v) return;
    state.thresholds = { ...v.thresholds };
    state.activeVersion = version;
    state.isEditing = false;
    renderAll();
  }

  async function promptSaveNew() {
    const name = window.prompt(
      "새 버전 이름을 입력하세요 (영숫자·언더스코어·한글, 24자 이내).\n예: v3, v_보수, v_test",
      ""
    );
    if (!name) return;
    const cleaned = name.trim();
    if (!cleaned) return;
    try {
      await saveVersion(cleaned, state.thresholds);
      await loadVersions();
      state.activeVersion = cleaned;
      state.isEditing = false;
      renderAll();
    } catch (err) {
      alert(`저장 실패: ${err.message}\n${err.hint || ""}`);
    }
  }

  async function confirmDelete(version) {
    if (!window.confirm(`${version}을 그래프에서 삭제합니다. 진행할까요?`)) return;
    try {
      await deleteVersion(version);
      await loadVersions();
      if (state.activeVersion === version) {
        // 삭제된 버전이 활성 → v1으로 fallback
        const fallback = state.versions[0];
        if (fallback) await applyVersion(fallback.version);
      } else {
        renderAll();
      }
    } catch (err) {
      alert(`삭제 실패: ${err.message}`);
    }
  }

  // === 렌더 ===
  function renderColorbar() {
    const t = state.thresholds;
    const widths = [t.low, t.mid_low - t.low, t.mid_high - t.mid_low, t.high - t.mid_high, 1.0 - t.high];
    els.colorbar.style.setProperty("--w1", widths[0].toFixed(4));
    els.colorbar.style.setProperty("--w2", widths[1].toFixed(4));
    els.colorbar.style.setProperty("--w3", widths[2].toFixed(4));
    els.colorbar.style.setProperty("--w4", widths[3].toFixed(4));
    els.colorbar.style.setProperty("--w5", widths[4].toFixed(4));
  }

  function renderSliders() {
    els.sliders.forEach((s) => { s.value = state.thresholds[s.dataset.th]; });
    els.sliderValues.forEach((el) => {
      el.textContent = state.thresholds[el.dataset.value].toFixed(2);
    });
  }

  // === INSERT TypeQL 박스 — 슬라이더·버전에 따라 라이브 갱신 ===
  // 변하는 부분만 textContent 갱신해서 화면 깜빡임 없이 숫자만 업데이트.
  function renderInsertSql() {
    const t = state.thresholds;
    const editing = state.isEditing || !state.activeVersion;
    const versionLabel = editing ? "(편집 중 — 저장 시 입력)" : state.activeVersion;
    const setId = editing
      ? "(저장 시 자동 생성)"
      : `TS_S_PRIORITY_${state.activeVersion.toUpperCase()}`;

    els.insertTokens["set-id"].textContent = setId;
    els.insertTokens.version.textContent = versionLabel;
    els.insertTokens.low.textContent = t.low.toFixed(2);
    els.insertTokens.mid_low.textContent = t.mid_low.toFixed(2);
    els.insertTokens.mid_high.textContent = t.mid_high.toFixed(2);
    els.insertTokens.high.textContent = t.high.toFixed(2);

    els.insertTokens["set-id"].classList.toggle("is-pending", editing);
    els.insertTokens.version.classList.toggle("is-pending", editing);
    els.insertHint.textContent = editing
      ? "슬라이더로 임의 값을 시험 중 — '+ 새 버전 저장' 클릭 시 위 TypeQL이 그래프에 실행됩니다"
      : `슬라이더를 움직이면 아래 숫자가 함께 바뀝니다 · 현재 ${state.activeVersion}이 그래프에 저장된 모양`;
  }

  function renderSource() {
    if (state.isEditing) {
      els.sourcePill.textContent = "편집 중 — 저장 안 함 (클라 즉석 재계산)";
      els.editPill.hidden = false;
    } else if (state.activeVersion) {
      els.sourcePill.textContent = `graph://threshold-set[config-version=${state.activeVersion}]`;
      els.editPill.hidden = true;
    } else {
      els.sourcePill.textContent = "버전 미선택";
      els.editPill.hidden = true;
    }
  }

  function statePill(stateKey) {
    const m = STATE_LABELS[stateKey];
    if (!m) return `<span>${stateKey}</span>`;
    return `<span class="state-pill" style="background:${m.color}; color:${m.textOn};">${m.ko}</span>`;
  }

  function diffMarker(currentState, v1State) {
    if (!v1State) return `<span class="diff-marker same">—</span>`;
    if (currentState === v1State) return `<span class="diff-marker same">— 변화 없음</span>`;
    const di = bandIndex(currentState) - bandIndex(v1State);
    const arrow = di > 0 ? "↑" : "↓";
    const cls = di > 0 ? "up" : "down";
    const label = STATE_LABELS[currentState]?.ko || currentState;
    return `<span class="diff-marker ${cls}">${arrow} ${label}</span>`;
  }

  function renderMapping() {
    // v1 캐시 (한 번만)
    if (state.v1Cache === null) {
      const v1 = state.versions.find((x) => x.version === "v1");
      if (v1) {
        state.v1Cache = {};
        state.segments.forEach((seg) => {
          state.v1Cache[seg.id] = sPriorityToState(seg.s_priority, v1.thresholds);
        });
      }
    }

    const sorted = [...state.segments].sort((a, b) => a.s_priority - b.s_priority);
    els.mappingRows.innerHTML = sorted.map((seg) => {
      const cur = sPriorityToState(seg.s_priority, state.thresholds);
      const v1 = state.v1Cache ? state.v1Cache[seg.id] : null;
      const di = v1 ? bandIndex(cur) - bandIndex(v1) : 0;
      let cls = "";
      if (di > 0) cls = "is-up";
      else if (di < 0) cls = "is-down";
      return `
        <tr class="${cls}">
          <td>${escapeHTML(seg.label)}</td>
          <td class="num">${seg.s_priority.toFixed(4)}</td>
          <td>${statePill(cur)}</td>
          <td>${diffMarker(cur, v1)}</td>
        </tr>`;
    }).join("");

    if (state.missing.length > 0) {
      els.missingBanner.hidden = false;
      els.missingBanner.className = "missing-banner";
      const ids = state.missing.map((m) => m.label).join(", ");
      els.missingBanner.innerHTML = `
        <strong>아직 추론 결과가 없는 segment: ${state.missing.length}건</strong>
        ${escapeHTML(ids)} — 시연 ①을 먼저 실행하면 점수와 단계가 채워집니다.
      `;
    } else {
      els.missingBanner.hidden = true;
    }
  }

  function renderAll() {
    renderToggleRow();
    renderColorbar();
    renderSliders();
    renderSource();
    renderInsertSql();
    renderMapping();
  }

  // === 슬라이더 이벤트 ===
  els.sliders.forEach((s) => {
    s.addEventListener("input", () => {
      const v = parseFloat(s.value);
      state.thresholds[s.dataset.th] = v;
      // 단조 보장
      const th = state.thresholds;
      if (th.low > th.mid_low) th.mid_low = th.low;
      if (th.mid_low > th.mid_high) th.mid_high = th.mid_low;
      if (th.mid_high > th.high) th.high = th.mid_high;
      state.isEditing = true;
      state.activeVersion = null;
      renderAll();
    });
  });

  // === 초기화 ===
  async function init() {
    try {
      await Promise.all([loadSegments(), loadVersions()]);
      // 기본: v1 선택
      const v1 = state.versions.find((x) => x.version === "v1") || state.versions[0];
      if (v1) {
        state.thresholds = { ...v1.thresholds };
        state.activeVersion = v1.version;
      }
      state.isEditing = false;
      state.v1Cache = null;
      renderAll();
    } catch (err) {
      els.mappingRows.innerHTML = `
        <tr><td colspan="4">
          <div class="error-box">
            <strong>초기 로드 실패</strong>${escapeHTML(err.message)}
          </div>
        </td></tr>`;
    }
  }

  init();
})();
