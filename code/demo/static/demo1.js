/* 시연 ① 9단계 인터랙티브 로직.
 * 모든 단계는 demo1 API를 호출하여 결과를 받고, 클라이언트가 상태를 누적 보관.
 * 같은 segment를 다시 선택하면 캐시에서 즉시 복원, "다시 호출" 버튼만 실제 API 재호출. */

(() => {
  "use strict";

  // === 단계 정의 ===
  const STEPS = [
    {
      key: "select",
      badge: "Step 0",
      title: "동네 선택",
      caption: "좌측에서 5개 동네 중 하나를 골라주세요. 6개 입력값이 표시됩니다.",
      action: null,
    },
    {
      key: "weights",
      badge: "Step 1",
      title: "그래프에서 가중치 가져오기",
      caption: "Python이 가지고 있는 게 아니라 graph DB의 weight-set 노드에서 직접 읽어옵니다.",
      action: { label: "그래프에서 가중치 가져오기", api: "load-weights" },
    },
    {
      key: "thresholds",
      badge: "Step 2",
      title: "그래프에서 임계값 가져오기",
      caption: "임계값도 마찬가지로 graph DB의 threshold-set 노드에서. 5단계 매핑은 색 막대로.",
      action: { label: "그래프에서 임계값 가져오기", api: "load-thresholds" },
    },
    {
      key: "signals",
      badge: "Step 3",
      title: "신호 5개 점수 계산",
      caption: "Python이 수치 연산을 담당합니다. 등급·특보·인구·숲거리·풍속이 5개 신호 점수로 바뀝니다.",
      action: { label: "신호 5개 계산", api: "compute-signals" },
    },
    {
      key: "aggregate",
      badge: "Step 4",
      title: "S_priority 가중평균 합산",
      caption: "신호 5개에 가중치를 곱해 더하면 종합 위험도 점수가 됩니다.",
      action: { label: "S_priority 합산", api: "aggregate" },
    },
    {
      key: "basestate",
      badge: "Step 5+6",
      title: "기본 단계 매핑 → 오버라이드 적용",
      caption: "점수가 5단계 중 어디에 떨어졌나(상단) → 안전/특보 격상 규칙 적용(하단). 한 번 클릭으로 두 단계 순차 진행.",
      action: { label: "단계 결정 + 오버라이드 적용", api: "basestate_then_override" },
    },
    {
      key: "writeback",
      badge: "Step 7",
      title: "그래프에 저장 (write-back)",
      caption: "계산 결과 6개를 그래프에 INSERT 합니다. 추론 결과가 다시 데이터가 됩니다.",
      action: { label: "그래프에 저장", api: "write-back" },
    },
    {
      key: "verify",
      badge: "Step 8",
      title: "다시 읽어와서 검증",
      caption: "방금 저장한 값이 정말 그래프에 들어갔는지 직접 select로 다시 읽어옵니다.",
      action: { label: "그래프에서 다시 읽기", api: "verify" },
    },
  ];

  // === 상태 ===
  const state = {
    segment: null,                  // 카탈로그의 segment 객체
    completed: new Set(),           // 완료된 step.key 집합
    current: null,                  // 현재 활성화된 step.key (다음에 실행할)
    cache: {},                      // segmentId → { weights, thresholds, signals, factors, breakdown, s_priority, contributions, base_state, band_index, position_in_band, base_explain, final_state, override_reason, rules_evaluated, rule_source, typeql, committed_at, verify }
  };

  // === DOM 참조 ===
  const els = {
    segmentList: document.getElementById("segment-list"),
    attrPanel: document.getElementById("segment-attrs"),
    attrRows: document.getElementById("attr-rows"),
    progressTrack: document.getElementById("progress-track"),
    progressLabel: document.getElementById("progress-label"),
    stepsContainer: document.getElementById("steps-container"),
  };

  // === 진행 비드 렌더 ===
  function renderProgress() {
    els.progressTrack.innerHTML = "";
    STEPS.forEach((s, idx) => {
      const bead = document.createElement("div");
      bead.className = "bead";
      bead.dataset.step = s.key;
      const dot = document.createElement("span");
      dot.className = "bead-dot";
      bead.appendChild(dot);
      if (state.completed.has(s.key) || (s.key === "select" && state.segment)) {
        bead.classList.add("is-done");
      } else if (s.key === state.current) {
        bead.classList.add("is-current");
      }
      els.progressTrack.appendChild(bead);
    });

    if (!state.segment) {
      els.progressLabel.textContent = "동네 선택 대기 중";
    } else if (state.completed.size + 1 >= STEPS.length) {
      els.progressLabel.textContent = "9단계 완료 ✓";
    } else {
      const nextIdx = STEPS.findIndex((s) => s.key === state.current);
      els.progressLabel.textContent = `Step ${nextIdx} / 8 진행`;
    }
  }

  // === 단계 카드 렌더 ===
  function renderSteps() {
    els.stepsContainer.innerHTML = "";
    STEPS.forEach((step, idx) => {
      if (step.key === "select") return; // 좌측 패널이 담당
      const card = document.createElement("article");
      card.className = "step-card";
      card.dataset.step = step.key;

      if (state.completed.has(step.key)) {
        card.classList.add("is-done");
      } else if (step.key === state.current) {
        card.classList.add("is-current");
      } else {
        card.classList.add("is-pending");
      }

      card.innerHTML = `
        <header class="step-head">
          <span class="step-badge">${step.badge}</span>
          <h3>${step.title}</h3>
        </header>
        <p class="step-caption">${step.caption}</p>
        <div class="step-result" data-result></div>
        <div class="step-action" data-action></div>
      `;
      els.stepsContainer.appendChild(card);

      const actionEl = card.querySelector("[data-action]");
      const resultEl = card.querySelector("[data-result]");

      if (state.completed.has(step.key)) {
        renderResultFor(step.key, resultEl);
        const retry = document.createElement("button");
        retry.type = "button";
        retry.className = "btn-secondary";
        retry.textContent = "다시 호출";
        retry.addEventListener("click", () => runStep(step));
        actionEl.appendChild(retry);
      } else if (step.key === state.current) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn-primary";
        btn.textContent = step.action.label;
        btn.addEventListener("click", () => runStep(step));
        actionEl.appendChild(btn);
      } else {
        const note = document.createElement("span");
        note.style.color = "var(--text-muted)";
        note.style.fontSize = "13px";
        note.textContent = "이전 단계를 먼저 완료해주세요.";
        actionEl.appendChild(note);
      }
    });
    renderProgress();
  }

  // === 단계별 결과 렌더 ===
  function renderResultFor(stepKey, el) {
    const data = state.cache[state.segment.id];
    if (!data) return;

    if (stepKey === "weights") el.innerHTML = renderWeights(data);
    else if (stepKey === "thresholds") el.innerHTML = renderThresholds(data);
    else if (stepKey === "signals") el.innerHTML = renderSignals(data);
    else if (stepKey === "aggregate") el.innerHTML = renderAggregate(data);
    else if (stepKey === "basestate") el.innerHTML = renderBaseStateOverride(data);
    else if (stepKey === "writeback") el.innerHTML = renderWriteBack(data);
    else if (stepKey === "verify") el.innerHTML = renderVerify(data);
  }

  const SIGNAL_META = [
    { key: "official", label: "공식성", cls: "sig-official" },
    { key: "exposure", label: "노출",   cls: "sig-exposure" },
    { key: "spread",   label: "확산",   cls: "sig-spread" },
    { key: "action",   label: "대응",   cls: "sig-action" },
    { key: "time",     label: "시점",   cls: "sig-time" },
  ];

  function fmt(n, digits = 4) {
    if (typeof n !== "number") return String(n);
    return n.toFixed(digits).replace(/0+$/, "").replace(/\.$/, "");
  }

  function renderWeights(data) {
    if (!data.weights) return "";
    const boxes = SIGNAL_META.map((m) => `
      <div class="weight-box ${m.cls}">
        <span class="weight-box-name">${m.label}</span>
        <span class="weight-box-value">${data.weights[m.key].toFixed(2)}</span>
      </div>`).join("");
    return `<div class="weight-grid">${boxes}</div>
      <p class="source-line">← ${data.weights_source || "graph://weight-set[config-version=v1]"}</p>`;
  }

  function renderThresholds(data) {
    if (!data.thresholds) return "";
    const t = data.thresholds;
    const tBoxes = [
      ["low", "낮음", t.low], ["mid_low", "중하", t.mid_low],
      ["mid_high", "중상", t.mid_high], ["high", "높음", t.high],
    ];
    return `
      <div class="threshold-row">
        ${tBoxes.map(([k, lbl, v]) => `
          <div class="threshold-box">
            <div class="threshold-box-name">${lbl} (${k})</div>
            <div class="threshold-box-value">${v.toFixed(2)}</div>
          </div>`).join("")}
      </div>
      ${renderColorbar(t, null)}
      <p class="source-line">← graph://threshold-set[config-version=v1, metric-name=S_priority_to_state]</p>
    `;
  }

  function renderColorbar(thresholds, markerSp) {
    const t = thresholds;
    const widths = [t.low, t.mid_low - t.low, t.mid_high - t.mid_low, t.high - t.mid_high, 1.0 - t.high];
    const styleW = `--w1:${widths[0]}; --w2:${widths[1]}; --w3:${widths[2]}; --w4:${widths[3]}; --w5:${widths[4]};`;
    const labels = ["일반", "감시", "검토", "우선", "즉시"];

    let markerHTML = "";
    if (markerSp !== null && markerSp !== undefined) {
      const pct = (markerSp * 100).toFixed(2);
      markerHTML = `
        <span class="colorbar-marker" style="left: ${pct}%;"></span>
        <span class="colorbar-marker-label" style="left: ${pct}%;">S = ${markerSp.toFixed(4)}</span>
      `;
    }

    return `
      <div class="colorbar-wrap">
        <div class="colorbar" style="${styleW}">
          ${labels.map((l, i) => `<span class="colorbar-band band-${i + 1}">${l}</span>`).join("")}
        </div>
        ${markerHTML}
      </div>
    `;
  }

  function renderSignals(data) {
    if (!data.signals) return "";
    const rows = SIGNAL_META.map((m) => {
      const f = (data.breakdown && data.breakdown[m.key]) || {};
      const inputs = f.inputs || {};
      const inputsStr = Object.entries(inputs)
        .map(([k, v]) => `${k}=${typeof v === "number" ? v.toFixed(3).replace(/0+$/, "").replace(/\.$/, "") : v}`)
        .join(", ");
      return `
        <div class="formula-row ${m.cls}">
          <span class="formula-name">${m.label}</span>
          <span class="formula-expr">${f.formula || ""} ${inputsStr ? `<small>[${inputsStr}]</small>` : ""}</span>
          <span class="formula-eq">=</span>
          <span class="formula-value">${data.signals[m.key].toFixed(3)}</span>
        </div>`;
    }).join("");
    return `<div class="formula-list">${rows}</div>`;
  }

  function renderAggregate(data) {
    if (!data.contributions) return "";
    const rows = data.contributions.map((c) => {
      const meta = SIGNAL_META.find((m) => m.key === c.name);
      return `
        <tr>
          <td><span class="agg-name"><span class="agg-dot ${meta.cls}"></span>${meta.label}</span></td>
          <td>${c.score.toFixed(3)}</td>
          <td>× ${c.weight.toFixed(2)}</td>
          <td>${c.product.toFixed(4)}</td>
        </tr>`;
    }).join("");
    return `
      <table class="agg-table">
        <thead>
          <tr><th>신호</th><th>점수</th><th>× 가중치</th><th>= 기여</th></tr>
        </thead>
        <tbody>
          ${rows}
          <tr class="agg-total-row"><td colspan="3">S_priority 합계</td><td>${data.s_priority.toFixed(4)}</td></tr>
        </tbody>
      </table>
    `;
  }

  function bandIndexOfState(stateKey) {
    const order = ["GeneralManagement", "EnhancedMonitoring", "ReviewPreWatering", "PriorityPreWatering", "ImmediatePreWatering"];
    return order.indexOf(stateKey);
  }

  function stateLabelKo(stateKey) {
    const m = {
      "GeneralManagement": "일반 관리",
      "EnhancedMonitoring": "감시 강화",
      "ReviewPreWatering": "검토 예비",
      "PriorityPreWatering": "우선 예비",
      "ImmediatePreWatering": "즉시 예비",
      "NotActionable": "작업 불가",
    };
    return m[stateKey] || stateKey;
  }

  function pillClassFor(stateKey) {
    if (stateKey === "NotActionable") return "notactionable";
    const bi = bandIndexOfState(stateKey);
    return bi >= 0 ? `band-${bi + 1}` : "";
  }

  function renderBaseStateOverride(data) {
    if (!data.base_state) return "";
    const baseHTML = `
      <div class="split-section">
        <h4>Step 5 — 기본 단계 매핑</h4>
        ${renderColorbar(data.thresholds, data.s_priority)}
        <div style="margin-top:14px;">
          <span class="state-pill ${pillClassFor(data.base_state)}">${stateLabelKo(data.base_state)} (${data.base_state})</span>
        </div>
        <p class="override-explain">${data.base_explain || ""}</p>
      </div>
    `;
    const rulesHTML = (data.rules_evaluated || []).map((r) => `
      <li class="rule-row ${r.matched ? "is-matched" : ""}">
        <span class="rule-check">${r.matched ? "✓" : ""}</span>
        <span>
          <span class="rule-name">${r.rule}</span><br/>
          <span class="rule-cond">${r.condition}</span>
        </span>
        ${r.matched && r.effect ? `<span class="rule-effect">${r.effect}</span>` : ""}
      </li>`).join("");
    const overrideHTML = `
      <div class="split-section">
        <h4>Step 6 — 격상 규칙 평가</h4>
        <ul class="rule-list">${rulesHTML}</ul>
        <div style="margin-top:14px;">
          최종: <span class="state-pill ${pillClassFor(data.final_state)}">${stateLabelKo(data.final_state)} (${data.final_state})</span>
          ${data.override_reason ? `<span style="margin-left:10px; font-size:13px; color: var(--text-muted);">사유: <code>${data.override_reason}</code></span>` : ""}
        </div>
        <p class="rule-source-note">${data.rule_source || ""}</p>
      </div>
    `;
    return `<div class="split-card">${baseHTML}${overrideHTML}</div>`;
  }

  function renderWriteBack(data) {
    if (!data.typeql) return "";
    return `
      <div class="typeql-block">${escapeHTML(data.typeql)}</div>
      <p class="committed-line">✓ 저장 완료 <span style="color: var(--text-muted); margin-left: 6px;">(committed_at: ${data.committed_at})</span></p>
    `;
  }

  function renderVerify(data) {
    if (!data.verify || !data.verify.stored) return "";
    const s = data.verify.stored;
    const rows = [
      ["risk-grade-score", s["risk-grade-score"]],
      ["alert-score", s["alert-score"]],
      ["s-priority", s["s-priority"]],
      ["base-state", s["base-state"]],
      ["state", s["state"]],
      ["state-override-reason", s["state-override-reason"]],
    ].map(([k, v]) => `
      <div class="verify-row">
        <span class="verify-attr">${k}</span>
        <span class="verify-value">${typeof v === "number" ? v.toFixed(4).replace(/0+$/, "").replace(/\.$/, "") : v}</span>
      </div>`).join("");
    return `<div class="verify-grid">${rows}</div>
      <p class="committed-line" style="color: var(--ok);">✓ 그래프에서 6개 attribute 모두 회수됨. 다음 시연 ②에서 이 값들을 그대로 사용합니다.</p>`;
  }

  function escapeHTML(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderError(stepKey, message, hint) {
    const card = els.stepsContainer.querySelector(`[data-step="${stepKey}"]`);
    if (!card) return;
    const resultEl = card.querySelector("[data-result]");
    resultEl.innerHTML = `
      <div class="error-box">
        <strong>실행 실패</strong>${escapeHTML(message || "알 수 없는 오류")}
        ${hint ? `<span class="error-hint">힌트: ${escapeHTML(hint)}</span>` : ""}
      </div>`;
    card.classList.remove("is-current");
    card.classList.add("is-fail");
    const actionEl = card.querySelector("[data-action]");
    actionEl.innerHTML = "";
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "btn-primary";
    retry.textContent = "다시 시도";
    retry.addEventListener("click", () => {
      card.classList.remove("is-fail");
      const step = STEPS.find((s) => s.key === stepKey);
      runStep(step);
    });
    actionEl.appendChild(retry);
  }

  // === API 호출 ===
  async function callApi(path, body) {
    const opts = body
      ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      : { method: "POST" };
    const res = await fetch(`/api/demo1/${path}`, opts);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const detail = data.detail || {};
      const err = new Error(detail.message || `HTTP ${res.status}`);
      err.hint = detail.hint_for_presenter;
      throw err;
    }
    return res.json();
  }

  // === 단계 실행 ===
  async function runStep(step) {
    if (!state.segment) return;
    const segId = state.segment.id;
    const cache = state.cache[segId] = state.cache[segId] || {};

    try {
      if (step.action.api === "load-weights") {
        const r = await callApi("load-weights");
        cache.weights = r.weights;
        cache.weights_source = r.source;
      } else if (step.action.api === "load-thresholds") {
        const r = await callApi("load-thresholds");
        cache.thresholds = r.thresholds;
        cache.state_labels = r.state_labels;
      } else if (step.action.api === "compute-signals") {
        const r = await callApi("compute-signals", { segment_id: segId });
        cache.signals = r.signals;
        cache.factors = r.factors;
        cache.breakdown = r.breakdown;
      } else if (step.action.api === "aggregate") {
        const r = await callApi("aggregate", { weights: cache.weights, signals: cache.signals });
        cache.s_priority = r.s_priority;
        cache.contributions = r.contributions;
      } else if (step.action.api === "basestate_then_override") {
        // 두 API 순차 호출
        const r1 = await callApi("base-state", { s_priority: cache.s_priority, thresholds: cache.thresholds });
        cache.base_state = r1.base_state;
        cache.band_index = r1.band_index;
        cache.position_in_band = r1.position_in_band;
        cache.base_explain = r1.explain;
        const r2 = await callApi("override", { segment_id: segId, base_state: cache.base_state });
        cache.final_state = r2.final_state;
        cache.override_reason = r2.reason;
        cache.rules_evaluated = r2.rules_evaluated;
        cache.rule_source = r2.rule_source;
      } else if (step.action.api === "write-back") {
        const r = await callApi("write-back", {
          segment_id: segId,
          f_grade: cache.factors.f_grade,
          f_alert: cache.factors.f_alert,
          s_priority: cache.s_priority,
          base_state: cache.base_state,
          state: cache.final_state,
          reason: cache.override_reason,
        });
        cache.typeql = r.typeql;
        cache.committed_at = r.committed_at;
      } else if (step.action.api === "verify") {
        const r = await callApi("verify", { segment_id: segId });
        cache.verify = r;
      }

      state.completed.add(step.key);
      // 다음 단계 활성화
      const idx = STEPS.findIndex((s) => s.key === step.key);
      const next = STEPS.slice(idx + 1).find((s) => !state.completed.has(s.key));
      state.current = next ? next.key : null;
      renderSteps();
    } catch (err) {
      renderError(step.key, err.message, err.hint);
    }
  }

  // === 동네 선택 ===
  function selectSegment(seg) {
    state.segment = seg;
    // 모든 단계 초기화 (캐시에서 복원)
    state.completed = new Set();
    state.current = "weights";
    const cache = state.cache[seg.id] || {};
    if (cache.weights) state.completed.add("weights");
    if (cache.thresholds) state.completed.add("thresholds");
    if (cache.signals) state.completed.add("signals");
    if (cache.contributions) state.completed.add("aggregate");
    if (cache.base_state && cache.final_state) state.completed.add("basestate");
    if (cache.typeql) state.completed.add("writeback");
    if (cache.verify) state.completed.add("verify");
    // 다음 진행 step 갱신
    const next = STEPS.slice(1).find((s) => !state.completed.has(s.key));
    state.current = next ? next.key : null;

    // 선택 UI 갱신
    document.querySelectorAll(".segment-radio").forEach((r) => {
      r.classList.toggle("is-active", r.dataset.id === seg.id);
    });

    // attribute 표시
    els.attrPanel.hidden = false;
    els.attrRows.innerHTML = `
      <div class="attr-row"><span class="attr-label">위험 등급</span><span class="attr-value ${seg.input.risk_grade === "매우높음" ? "is-warn" : ""}">${seg.input.risk_grade}</span></div>
      <div class="attr-row"><span class="attr-label">기상특보</span><span class="attr-value ${seg.input.alert_level === "경보" ? "is-warn" : ""}">${seg.input.alert_level}</span></div>
      <div class="attr-row"><span class="attr-label">주거 인구</span><span class="attr-value">${seg.input.population.toLocaleString()} 명</span></div>
      <div class="attr-row"><span class="attr-label">숲 거리</span><span class="attr-value">${seg.input.forest_dist} m</span></div>
      <div class="attr-row"><span class="attr-label">풍속</span><span class="attr-value">${seg.input.wind} m/s</span></div>
      <div class="attr-row"><span class="attr-label">안전 상태</span><span class="attr-value ${seg.input.safety_class === "작업 불가" ? "is-fail" : ""}">${seg.input.safety_class}</span></div>
    `;
    renderSteps();
  }

  function renderSegmentList(segments) {
    els.segmentList.innerHTML = "";
    segments.forEach((seg) => {
      const label = document.createElement("label");
      label.className = "segment-radio";
      label.dataset.id = seg.id;
      const star = seg.highlight && seg.highlight.includes("본방") ? `<span class="segment-radio-star">★</span>` : "";
      label.innerHTML = `
        <input type="radio" name="segment" value="${seg.id}" />
        <span class="segment-radio-name">${star}${seg.label}</span>
        <span class="segment-radio-highlight">${seg.highlight || ""}</span>
      `;
      label.addEventListener("click", (e) => {
        e.preventDefault();
        selectSegment(seg);
      });
      els.segmentList.appendChild(label);
    });
  }

  async function init() {
    renderProgress();
    renderSteps();
    try {
      const res = await fetch("/api/demo1/segments");
      const data = await res.json();
      renderSegmentList(data.segments);
    } catch (err) {
      els.segmentList.innerHTML = `<div class="error-box">동네 목록을 불러오지 못했습니다: ${escapeHTML(err.message)}</div>`;
    }
  }

  init();
})();
