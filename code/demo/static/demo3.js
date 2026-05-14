/* 시연 ③ 자연어 채팅 — 4단계 자동 펼침.
 * 흐름:
 *   1. 사용자 입력 → POST /api/demo3/ask
 *   2. 응답 받기까지 "AI 생각 중..." 인디케이터
 *   3. 응답 받으면 trace 카드를 600ms 간격으로 순차 펼침 */

(() => {
  "use strict";

  const PRESETS = [
    { label: "EMD_여수_상암동 위험도 알려줘", case_id: "1-1" },
    { label: "MOCK 상태인 source 모두 알려줘", case_id: "2-2" },
    { label: "1990년 1월 광주 동구 위험도?", case_id: null },
  ];

  const els = {
    presetRow: document.getElementById("preset-row"),
    form: document.getElementById("ask-form"),
    input: document.getElementById("ask-input"),
    submit: document.getElementById("ask-submit"),
    list: document.getElementById("trace-list"),
  };

  function escapeHTML(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // === 프리셋 칩 ===
  PRESETS.forEach((p) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "preset-chip";
    chip.textContent = p.label;
    chip.dataset.caseId = p.case_id || "";
    chip.addEventListener("click", () => {
      els.input.value = p.label;
      els.input.dataset.caseId = p.case_id || "";
      els.input.focus();
    });
    els.presetRow.appendChild(chip);
  });

  // === API ===
  async function ask(query, caseId) {
    const res = await fetch("/api/demo3/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, case_id: caseId || null }),
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

  // === 카드 렌더 ===
  function thinkingCard() {
    return `
      <div class="trace-card">
        <div class="trace-head">
          <span class="trace-step">AI 생각 중</span>
          <span class="thinking">
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span>TypeQL 생성하고 그래프에 실행하는 중…</span>
          </span>
        </div>
      </div>`;
  }

  function questionCard(question) {
    return `
      <div class="trace-card" style="animation-delay: 0s;">
        <div class="trace-head">
          <span class="trace-step">① 질문</span>
        </div>
        <div class="trace-question">${escapeHTML(question)}</div>
      </div>`;
  }

  function attemptTag(attempt, trail) {
    // 첫 시도 + 성공 + 결과 > 0 → ok
    // 후속 시도 + 성공 → retry (자가 수정)
    // fallback 성공 → fallback
    // 실패 (ok=false) → fail
    // 성공 + 결과 0건 → empty
    if (attempt.attempt === "fallback") {
      return `<span class="trace-tag fallback">🔄 예비 답안 사용</span>`;
    }
    if (!attempt.ok) {
      return `<span class="trace-tag fail">❌ 실행 실패</span>`;
    }
    if (attempt.result_count === 0) {
      return `<span class="trace-tag empty">⚠️ 결과 0건</span>`;
    }
    // 성공 + 결과 1건 이상
    const isFirst = attempt.attempt === 1;
    if (isFirst) {
      return `<span class="trace-tag ok">✓ 1회 성공 · ${attempt.result_count}건</span>`;
    }
    return `<span class="trace-tag retry">🔁 자가 수정 ${attempt.attempt}회 성공 · ${attempt.result_count}건</span>`;
  }

  function attemptCard(attempt, idx, totalAttempts) {
    const label =
      attempt.attempt === "fallback"
        ? "예비 답안 (golden TypeQL)"
        : `시도 ${attempt.attempt}`;
    const stepLabel = totalAttempts === 1 ? "② TypeQL 생성 + 실행" : `② TypeQL — ${label}`;
    let resultHTML = "";
    if (attempt.result === null) {
      resultHTML = `<div class="trace-result error">${escapeHTML(attempt.error || "에러")}</div>`;
    } else if (attempt.result_count === 0) {
      resultHTML = `<div class="trace-result empty">결과 0건 (조건 미일치)</div>`;
    } else {
      resultHTML = `<div class="trace-result">${escapeHTML(JSON.stringify(attempt.result, null, 2))}</div>`;
    }
    return `
      <div class="trace-card" style="animation-delay: ${(idx + 1) * 0.5}s;">
        <div class="trace-head">
          <span class="trace-step">${escapeHTML(stepLabel)}</span>
          ${attemptTag(attempt)}
        </div>
        <div class="trace-typeql">${escapeHTML(attempt.typeql)}</div>
        ${resultHTML}
      </div>`;
  }

  function advisoryChip(text) {
    let cls = "alert";
    if (text.includes("MOCK")) cls = "mock";
    else if (text.includes("안전") || text.includes("⛔")) cls = "hazard";
    return `<span class="advisory-chip ${cls}">${escapeHTML(text)}</span>`;
  }

  function answerCard(answer, advisory, statusKind, idx) {
    const stepName =
      statusKind === "failure"
        ? "③ 답변 (환각 방지)"
        : statusKind === "fallback_success"
          ? "③ 답변 (예비 답안 기반)"
          : "③ 자연어 답변";
    const advisoryHTML =
      advisory && advisory.length > 0
        ? `<div class="advisory-row">${advisory.map(advisoryChip).join("")}</div>`
        : "";
    const tag =
      statusKind === "failure"
        ? `<span class="trace-tag empty">— 답을 만들지 않음</span>`
        : statusKind === "fallback_success"
          ? `<span class="trace-tag fallback">🔄 예비 답안</span>`
          : `<span class="trace-tag ok">✓ 응답 완료</span>`;
    return `
      <div class="trace-card" style="animation-delay: ${(idx + 1) * 0.5}s;">
        <div class="trace-head">
          <span class="trace-step">${escapeHTML(stepName)}</span>
          ${tag}
        </div>
        <div class="trace-answer">${escapeHTML(answer)}</div>
        ${advisoryHTML}
      </div>`;
  }

  // === 메인 흐름 ===
  function setThinking() {
    els.list.innerHTML = thinkingCard();
    els.submit.disabled = true;
  }

  function renderTrace(data) {
    els.submit.disabled = false;
    const cards = [];
    // ① 질문
    cards.push(questionCard(data.question));
    // ② 시도 카드들
    const trail = data.trail || [];
    trail.forEach((a, i) => {
      cards.push(attemptCard(a, i, trail.length));
    });
    // ③ 답변
    cards.push(
      answerCard(
        data.answer || "",
        data.advisory || [],
        data.final_status,
        trail.length
      )
    );
    els.list.innerHTML = cards.join("");
  }

  function renderError(message, hint) {
    els.submit.disabled = false;
    els.list.innerHTML = `
      <div class="error-box">
        <strong>요청 실패</strong>${escapeHTML(message)}
        ${hint ? `<span class="error-hint">힌트: ${escapeHTML(hint)}</span>` : ""}
      </div>`;
  }

  els.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = els.input.value.trim();
    if (!query) return;
    const caseId = els.input.dataset.caseId || "";
    setThinking();
    try {
      const data = await ask(query, caseId);
      renderTrace(data);
    } catch (err) {
      renderError(err.message, err.hint);
    }
  });
})();
