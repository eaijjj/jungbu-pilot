<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>서해 중부 통합 도선 스케줄</title>
  <link rel="manifest" href="manifest.json" />
  <link rel="apple-touch-icon" href="apple-touch-icon.png" />
  <meta name="theme-color" content="#1d4ed8" />
  <style>
    :root {
      --bg-color: #f4f6f9;
      --card-bg: #ffffff;
      --text-main: #111827;
      --text-sub: #4b5563;
      --border-color: #e5e7eb;
      --primary: #1d4ed8;
      --incheon-bg: #fce7f3;
      --incheon-text: #be185d;
      --pyeongtaek-bg: #efe2d2;
      --pyeongtaek-text: #6b3f1d;
      --daesan-bg: #dcfce7;
      --daesan-text: #166534;
      --boryeong-bg: #e0f2fe;
      --boryeong-text: #075985;
      --big-bg: #fee2e2;
      --big-bar: #dc2626;
      --transit-bg: #7c3aed;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Pretendard", sans-serif;
    }

    body {
      background-color: var(--bg-color);
      color: var(--text-main);
      padding: 16px;
    }

    .container {
      max-width: 1100px;
      margin: 0 auto;
    }

    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 8px;
    }

    h1 {
      font-size: 1.25rem;
      font-weight: 700;
    }

    .update-info {
      font-size: 0.85rem;
      color: var(--text-sub);
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .refresh-btn {
      padding: 6px 10px;
      border: 1px solid var(--border-color);
      background: #fff;
      color: var(--primary);
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
    }

    .refresh-btn:disabled {
      opacity: 0.5;
      cursor: default;
    }

    /* 원본 사이트 오류 경고 */
    .error-banner {
      display: none;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-left: 4px solid #dc2626;
      color: #991b1b;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 0.85rem;
      font-weight: 600;
      line-height: 1.5;
      margin-bottom: 12px;
    }

    .error-banner .eb-detail {
      display: block;
      margin-top: 2px;
      font-size: 0.76rem;
      font-weight: 500;
      opacity: 0.85;
    }

    .controls {
      background: var(--card-bg);
      padding: 12px;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .tabs {
      display: flex;
      gap: 6px;
      overflow-x: auto;
    }

    .tab-btn {
      flex: 1;
      padding: 10px 12px;
      border: 1px solid var(--border-color);
      background: #fff;
      border-radius: 8px;
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-sub);
      cursor: pointer;
      transition: all 0.15s;
      white-space: nowrap;
    }

    .tab-btn.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }

    .search-box {
      display: flex;
      gap: 8px;
    }

    .search-box input {
      flex: 1;
      padding: 10px 12px;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      font-size: 0.95rem;
      outline: none;
    }

    .search-box input:focus {
      border-color: var(--primary);
    }

    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 800;
      margin-right: 6px;
      vertical-align: middle;
    }

    .badge-인천 { background: var(--incheon-bg); color: var(--incheon-text); }
    .badge-평택 { background: var(--pyeongtaek-bg); color: var(--pyeongtaek-text); }
    .badge-대산 { background: var(--daesan-bg); color: var(--daesan-text); }
    .badge-보령 { background: var(--boryeong-bg); color: var(--boryeong-text); }

    /* 통과선박 표시 (도선점 위) */
    .transit-badge {
      display: inline-block;
      background: var(--transit-bg);
      color: #fff;
      font-size: 0.72rem;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 6px;
      margin-bottom: 4px;
      white-space: nowrap;
    }

    /* 16만톤 이상 표시 */
    .big-tag {
      display: inline-block;
      background: var(--big-bar);
      color: #fff;
      font-size: 0.66rem;
      font-weight: 800;
      padding: 1px 6px;
      border-radius: 5px;
      margin-right: 4px;
      vertical-align: middle;
      white-space: nowrap;
    }

    /* ===== 상세 목록 (대산 / 보령 / 전체) ===== */
    .detail-wrap {
      display: none;
    }

    .dt-legend {
      font-size: 0.8rem;
      color: var(--text-sub);
      margin-bottom: 8px;
      line-height: 1.6;
    }

    .dt-card {
      background: var(--card-bg);
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
      overflow: clip;
    }

    .dt-title {
      padding: 12px 16px;
      font-size: 1.15rem;
      font-weight: 800;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .dt-title small {
      font-size: 0.9rem;
      font-weight: 700;
      opacity: 0.85;
    }

    .dt-title-daesan { background: var(--daesan-bg); color: var(--daesan-text); }
    .dt-title-boryeong { background: var(--boryeong-bg); color: var(--boryeong-text); }
    .dt-title-all { background: #e2e8f0; color: #1e293b; }

    .dt {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    .dt thead th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #1e293b;
      color: #fff;
      font-size: 0.85rem;
      font-weight: 700;
      padding: 10px 10px;
      white-space: nowrap;
    }

    .dt th.num,
    .dt td.num {
      text-align: right;
    }

    .dt td {
      padding: 12px 10px;
      font-size: 1rem;
      border-top: 1px solid var(--border-color);
      vertical-align: middle;
    }

    .dt tr.date-row td {
      background: #eef2ff;
      color: #3730a3;
      font-weight: 800;
      font-size: 0.9rem;
      padding: 8px 14px;
    }

    .c-pilot {
      font-weight: 700;
      white-space: nowrap;
    }

    .c-vessel {
      font-size: 1.1rem;
      font-weight: 800;
      line-height: 1.3;
      word-break: break-word;
    }

    .c-time {
      font-size: 1.3rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    .c-route {
      font-weight: 700;
      color: #1f2937;
    }

    .rt-from,
    .rt-to {
      display: inline;
    }

    .c-call {
      font-family: monospace;
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-sub);
    }

    .c-agent {
      font-size: 0.92rem;
      color: #1f2937;
    }

    .c-ton {
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    .dt tr.row.past td {
      opacity: 0.5;
      background: #f3f4f6;
    }

    .dt tr.row.soon td {
      background: #fef9c3;
    }

    .dt tr.row.big td {
      background: var(--big-bg);
    }

    .dt tr.row.soon .c-time {
      background: #fde047;
      border-radius: 6px;
      padding: 0 6px;
      display: inline-block;
    }

    .dt tr.row.big .c-ton {
      color: var(--big-bar);
    }

    .p-인천 { --bar: var(--incheon-text); }
    .p-평택 { --bar: var(--pyeongtaek-text); }
    .p-대산 { --bar: var(--daesan-text); }
    .dt tr.row.big { --bar: var(--big-bar); }

    @media (min-width: 701px) {
      .dt tr.row td:first-child {
        border-left: 6px solid var(--bar);
      }
    }

    /* 누르면 상세정보가 뜨는 항목 (대산만) */
    [data-ref] {
      cursor: pointer;
    }

    .dt tr.row[data-ref]:hover td {
      filter: brightness(0.97);
    }

    .dt-empty {
      padding: 32px 16px;
      text-align: center;
      font-size: 0.95rem;
      color: var(--text-sub);
    }

    /* ===== 요약 보기 (컴퓨터: 3칸 나란히) ===== */
    .summary-note {
      display: none;
      font-size: 0.78rem;
      color: var(--text-sub);
      margin-bottom: 8px;
      line-height: 1.5;
    }

    .summary-grid {
      display: none;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      align-items: start;
    }

    .sum-col {
      background: var(--card-bg);
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      overflow: hidden;
    }

    .sum-head {
      padding: 10px 12px;
      font-size: 0.95rem;
      font-weight: 700;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .sum-head small {
      font-size: 0.75rem;
      font-weight: 600;
      opacity: 0.8;
    }

    .sum-head-인천 { background: var(--incheon-bg); color: var(--incheon-text); }
    .sum-head-평택 { background: var(--pyeongtaek-bg); color: var(--pyeongtaek-text); }
    .sum-head-대산 { background: var(--daesan-bg); color: var(--daesan-text); }

    .sum-item {
      padding: 8px 12px;
      border-top: 1px solid var(--border-color);
    }

    .sum-item.big {
      background: var(--big-bg);
      border-left: 4px solid var(--big-bar);
    }

    .sum-line1 {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 8px;
    }

    .sum-vessel {
      font-weight: 700;
      font-size: 0.9rem;
      word-break: break-word;
    }

    .sum-time {
      font-weight: 600;
      font-size: 0.85rem;
      white-space: nowrap;
    }

    .sum-station {
      font-size: 0.78rem;
      color: var(--text-sub);
      margin-top: 2px;
      word-break: break-word;
    }

    .sum-empty {
      padding: 16px 12px;
      font-size: 0.85rem;
      color: var(--text-sub);
    }

    .sum-item .transit-badge,
    .tl-item .transit-badge {
      font-size: 0.64rem;
      padding: 1px 6px;
      margin-bottom: 2px;
    }

    /* ===== 요약 보기 (폰: 시간대별 표) ===== */
    .tl-grid {
      display: grid;
      grid-template-columns: 38px 1fr 1fr 1fr;
      background: var(--card-bg);
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      overflow: clip;
    }

    .tl-head {
      position: sticky;
      top: 0;
      z-index: 2;
      padding: 8px 2px;
      font-size: 0.8rem;
      font-weight: 700;
      text-align: center;
    }

    .tl-head small {
      display: block;
      font-size: 0.65rem;
      font-weight: 600;
      opacity: 0.8;
    }

    .tl-head-time {
      background: #f3f4f6;
      color: var(--text-sub);
    }

    .tl-date {
      grid-column: 1 / -1;
      padding: 4px 10px;
      background: #eef2ff;
      color: #3730a3;
      font-size: 0.75rem;
      font-weight: 700;
      border-top: 1px solid var(--border-color);
    }

    .tl-hour {
      padding: 6px 2px;
      font-size: 0.75rem;
      font-weight: 700;
      text-align: center;
      color: var(--text-sub);
      background: #f9fafb;
      border-top: 1px solid var(--border-color);
    }

    .tl-cell {
      padding: 5px 5px;
      border-top: 1px solid var(--border-color);
      border-left: 1px solid var(--border-color);
      min-width: 0;
    }

    .tl-item + .tl-item {
      margin-top: 5px;
      padding-top: 5px;
      border-top: 1px dashed var(--border-color);
    }

    .tl-item.big {
      background: var(--big-bg);
      border-left: 3px solid var(--big-bar);
      padding-left: 3px;
      border-radius: 4px;
    }

    .tl-min {
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--text-sub);
    }

    .tl-name {
      font-size: 0.74rem;
      font-weight: 700;
      line-height: 1.25;
      word-break: break-word;
    }

    .tl-st {
      font-size: 0.64rem;
      color: var(--text-sub);
      line-height: 1.25;
      word-break: break-word;
    }

    .tl-empty {
      grid-column: 1 / -1;
      padding: 24px 12px;
      text-align: center;
      font-size: 0.85rem;
      color: var(--text-sub);
    }

    /* ===== 상세정보 창 ===== */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.5);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }

    .modal-overlay.open {
      display: flex;
    }

    .modal-sheet {
      background: #fff;
      width: 100%;
      max-width: 520px;
      max-height: 88vh;
      overflow: auto;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    }

    .dm-head {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #fff;
      padding: 16px 16px 10px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }

    .dm-title {
      font-size: 1.3rem;
      font-weight: 800;
      line-height: 1.25;
      word-break: break-word;
    }

    .dm-tags {
      margin-top: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      align-items: center;
    }

    .dm-tags .transit-badge {
      margin-bottom: 0;
    }

    .dm-close {
      border: 0;
      background: #f3f4f6;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      font-size: 1.2rem;
      cursor: pointer;
      flex: none;
    }

    .dm-key {
      padding: 14px 16px;
      background: #f8fafc;
      border-bottom: 1px solid var(--border-color);
    }

    .dm-time {
      font-size: 1.9rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
    }

    .dm-date {
      font-size: 0.85rem;
      color: var(--text-sub);
      font-weight: 700;
    }

    .dm-route {
      margin-top: 4px;
      font-size: 1.15rem;
      font-weight: 800;
      word-break: break-word;
    }

    .dm-body {
      padding: 4px 16px 18px;
    }

    .dm-row {
      display: grid;
      grid-template-columns: 96px 1fr;
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid var(--border-color);
    }

    .dm-row:last-child {
      border-bottom: 0;
    }

    .dm-l {
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--text-sub);
    }

    .dm-v {
      font-size: 1rem;
      font-weight: 700;
      word-break: break-word;
    }

    @media (max-width: 700px) {
      .summary-grid {
        grid-template-columns: 1fr;
      }

      .modal-overlay {
        align-items: flex-end;
        padding: 0;
      }

      .modal-sheet {
        max-width: none;
        max-height: 90vh;
        border-radius: 16px 16px 0 0;
      }

      /* 상세 목록: 폰에서는 카드형 (왼쪽: 시간 + 도선점) */
      .dt thead {
        display: none;
      }

      .dt,
      .dt tbody {
        display: block;
      }

      .dt tr.date-row {
        display: block;
      }

      .dt tr.date-row td {
        display: block;
      }

      .dt tr.row {
        display: grid;
        grid-template-columns: 104px 1fr 1fr;
        grid-template-areas:
          "time vessel vessel"
          "route pilot call"
          "route agent ton";
        gap: 6px 10px;
        padding: 12px 12px 12px 10px;
        border-top: 1px solid var(--border-color);
        border-left: 6px solid var(--bar);
      }

      .dt tr.row td {
        display: block;
        padding: 0;
        border: 0;
        background: transparent;
        min-width: 0;
      }

      .dt tr.row.past {
        opacity: 0.5;
        background: #f3f4f6;
      }

      .dt tr.row.soon {
        background: #fef9c3;
      }

      .dt tr.row.big {
        background: var(--big-bg);
      }

      .dt tr.row.past td,
      .dt tr.row.soon td,
      .dt tr.row.big td {
        opacity: 1;
        background: transparent;
      }

      .c-time { grid-area: time; font-size: 1.45rem; }
      .c-vessel { grid-area: vessel; font-size: 1.1rem; }
      .c-route { grid-area: route; font-size: 0.95rem; line-height: 1.3; }
      .c-pilot { grid-area: pilot; }
      .c-call { grid-area: call; }
      .c-agent { grid-area: agent; }
      .c-ton { grid-area: ton; text-align: left; }

      .rt-from,
      .rt-to {
        display: block;
      }

      .dt td[data-l]::before {
        content: attr(data-l);
        display: block;
        font-size: 0.66rem;
        font-weight: 700;
        color: #6b7280;
        font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Pretendard", sans-serif;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>⚓ 통합 도선 스케줄</h1>
      <div class="header-right">
        <span class="update-info" id="lastUpdated">업데이트: 불러오는 중...</span>
        <button class="refresh-btn" id="refreshBtn" type="button">🔄 새로고침</button>
      </div>
    </header>

    <div class="error-banner" id="errorBanner"></div>

    <div class="controls">
      <div class="tabs" id="portTabs">
        <button class="tab-btn active" data-port="SUMMARY">요약</button>
        <button class="tab-btn" data-port="DAESAN">대산</button>
        <button class="tab-btn" data-port="BORYEONG">보령</button>
        <button class="tab-btn" data-port="ALL">전체</button>
      </div>
      <div class="search-box">
        <input
          type="text"
          id="searchInput"
          placeholder="선명, 콜사인, 도선점, 도선사, 대리점 검색..."
        />
      </div>
    </div>

    <!-- 대산 / 보령 / 전체 -->
    <div class="detail-wrap" id="detailWrap"></div>

    <!-- 요약 -->
    <div class="summary-note" id="summaryNote">
      대산은 전체 표시 / 평택은 JANG→, IPA→ 로 시작 / 인천은 JANG, PAL, NPPS 로 시작하는 도선점만 표시합니다.
      <br>빨간색: 대산 16만톤 이상 / 보라색 표시: 통과선박 / 대산 선박을 누르면 상세정보가 나옵니다.
    </div>
    <div class="summary-grid" id="summaryWrap"></div>
  </div>

  <!-- 상세정보 창 -->
  <div class="modal-overlay" id="modalOverlay">
    <div class="modal-sheet" id="modalSheet"></div>
  </div>

  <script>
    // ===== 요약 화면 표시 규칙 =====
    // 항구별로 도선점이 아래 글자로 "시작"하는 선박만 요약에 표시합니다.
    // 규칙이 없는 항구(대산)는 전부 표시합니다. 영문 대소문자와 띄어쓰기는 무시합니다.
    const SUMMARY_RULES = {
      "평택": ["JANG→", "IPA→"],
      "인천": ["JANG", "PAL", "NPPS"]
    };

    // ===== 보령 표시 규칙 =====
    // 대산 스케줄 중 도선점의 출발지 또는 도착지가 아래 글자로 시작하면 보령으로 분류합니다.
    const BORYEONG_PREFIXES = ["PS1", "B.", "MDB"];

    // ===== 대산 초대형 선박 기준 (총톤수) =====
    const BIG_TONNAGE = 160000;

    // ===== 상세정보 창에 보여줄 항목 (이 순서대로, 대리점 다음에 표시) =====
    const DETAIL_LABELS = ["흘수", "전장", "접안", "화물", "담당자", "연락처"];

    const TAB_INFO = {
      DAESAN: { label: "대산", cls: "dt-title-daesan", note: "대산 도선예보 전체 (취소 제외)" },
      BORYEONG: { label: "보령", cls: "dt-title-boryeong", note: "대산 스케줄 중 도선점의 출발지나 도착지가 PS1, B., MDB 로 시작하는 선박" },
      ALL: { label: "전체", cls: "dt-title-all", note: "인천·평택·대산 전체 (평택은 도선사, 대리점, 톤수 정보 준비 중)" }
    };

    let currentPort = "SUMMARY";
    let searchKeyword = "";
    let allSchedules = [];
    let rowRefs = [];

    const detailWrap = document.getElementById("detailWrap");
    const summaryWrap = document.getElementById("summaryWrap");
    const summaryNote = document.getElementById("summaryNote");
    const lastUpdatedEl = document.getElementById("lastUpdated");
    const errorBanner = document.getElementById("errorBanner");
    const searchInput = document.getElementById("searchInput");
    const tabButtons = document.querySelectorAll(".tab-btn");
    const modalOverlay = document.getElementById("modalOverlay");
    const modalSheet = document.getElementById("modalSheet");

    function isNarrow() {
      return window.matchMedia("(max-width: 700px)").matches;
    }
    let lastNarrow = isNarrow();

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function val(v) {
      return v && v !== "-" ? esc(v) : "-";
    }

    function pad2(n) {
      return String(n).padStart(2, "0");
    }

    // 대산 선박만 누르면 상세정보가 뜨도록 번호표(data-ref)를 붙임
    function refAttr(item) {
      if (item.port !== "대산") return "";
      rowRefs.push(item);
      return " data-ref='" + (rowRefs.length - 1) + "'";
    }

    function parseScheduleTime(timeStr) {
      const now = new Date();
      const parts = timeStr.trim().split(" ");
      if (parts.length !== 2) return null;
      const md = parts[0];
      const hm = parts[1];
      const mdParts = md.split("-").map(Number);
      const hmParts = hm.split(":").map(Number);
      const month = mdParts[0];
      const day = mdParts[1];
      const hour = hmParts[0];
      const minute = hmParts[1];
      if (!month || !day || isNaN(hour) || isNaN(minute)) return null;

      let year = now.getFullYear();
      if (now.getMonth() === 11 && month === 1) year += 1;
      return new Date(year, month - 1, day, hour, minute, 0);
    }

    // 총톤수 숫자로 바꾸기 ("152,003" -> 152003)
    function tonNum(item) {
      return Number(String(item.tonnage || "").replace(/[^0-9.]/g, "")) || 0;
    }

    // 대산 16만톤 이상인지
    function isBig(item) {
      return item.port === "대산" && tonNum(item) >= BIG_TONNAGE;
    }

    // 대산 통과선박인지
    function isTransit(item) {
      return item.port === "대산" && item.transit === true;
    }

    function transitBadge(item) {
      return isTransit(item) ? "<div class='transit-badge'>통과선박</div>" : "";
    }

    // 도선점 표시 (A → B 는 두 줄로 나눠서 폰에서 보기 편하게)
    function routeHtml(st) {
      const s = String(st || "");
      if (s.indexOf("→") === -1) return esc(s);
      const parts = s.split("→");
      return (
        "<span class='rt-from'>" + esc(parts[0].trim()) + "</span> " +
        "<span class='rt-to'>→ " + esc(parts.slice(1).join("→").trim()) + "</span>"
      );
    }

    // 요약 화면에 보여줄 선박인지 판단
    function matchesSummaryRule(item) {
      const rules = SUMMARY_RULES[item.port];
      if (!rules) return true;
      const st = String(item.station || "").toUpperCase().replace(/\s+/g, "");
      return rules.some(function (prefix) {
        return st.indexOf(prefix.toUpperCase().replace(/\s+/g, "")) === 0;
      });
    }

    // 보령 선박인지 판단 (출발지 또는 도착지가 보령 규칙으로 시작)
    function isBoryeong(item) {
      if (item.port !== "대산") return false;
      const parts = String(item.station || "").split("→");
      return parts.some(function (p) {
        const s = p.trim().toUpperCase();
        return BORYEONG_PREFIXES.some(function (pre) {
          return s.indexOf(pre.toUpperCase()) === 0;
        });
      });
    }

    function matchesTab(item, tab) {
      if (tab === "ALL") return true;
      if (tab === "DAESAN") return item.port === "대산";
      if (tab === "BORYEONG") return isBoryeong(item);
      return item.port === tab;
    }

    function shortTime(timeStr) {
      const parts = String(timeStr).trim().split(" ");
      if (parts.length !== 2) return timeStr;
      const now = new Date();
      const todayMd = pad2(now.getMonth() + 1) + "-" + pad2(now.getDate());
      return parts[0] === todayMd ? parts[1] : parts[0] + " " + parts[1];
    }

    function getFiltered(tab) {
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
      const limit = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      const keyword = searchKeyword.toLowerCase();

      return allSchedules.filter(function (item) {
        const itemDate = parseScheduleTime(item.time);
        if (itemDate && itemDate < oneHourAgo) return false;
        if (itemDate && itemDate > limit) return false;

        if (!matchesTab(item, tab)) return false;

        return (
          !keyword ||
          (item.vessel && item.vessel.toLowerCase().includes(keyword)) ||
          (item.callSign && item.callSign.toLowerCase().includes(keyword)) ||
          (item.station && item.station.toLowerCase().includes(keyword)) ||
          (item.pilot && item.pilot.toLowerCase().includes(keyword)) ||
          (item.agent && item.agent.toLowerCase().includes(keyword))
        );
      });
    }

    // 원본 사이트 수집 실패 표시 (data.errors)
    function renderErrors(errorsMap) {
      const ports = Object.keys(errorsMap || {});
      if (ports.length === 0) {
        errorBanner.style.display = "none";
        errorBanner.innerHTML = "";
        return;
      }

      const names = ports
        .map(function (port) {
          const hasRows = allSchedules.some(function (s) {
            return s.port === port;
          });
          return port + (hasRows ? " (직전 정상 데이터 표시 중)" : "");
        })
        .join(", ");

      const details = ports
        .map(function (port) {
          return port + ": " + esc(errorsMap[port]);
        })
        .join(" · ");

      errorBanner.innerHTML =
        "⚠️ 원본 사이트 오류: " +
        esc(names) +
        "<span class='eb-detail'>" +
        esc(details) +
        "</span>";
      errorBanner.style.display = "block";
    }

    async function init() {
      let errorsMap = {};
      try {
        const res = await fetch("./data.json?t=" + new Date().getTime());
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        allSchedules = data.schedules || [];
        errorsMap = data.errors || {};
        lastUpdatedEl.textContent = "업데이트: " + (data.updatedAt || "-") + " (1시간 전~24시간 후 표시)";
      } catch (e) {
        console.error("데이터 로드 실패:", e);
        lastUpdatedEl.textContent = "업데이트: 데이터 로드 실패";
        allSchedules = [];
      }

      allSchedules.sort(function (a, b) {
        return a.time.localeCompare(b.time);
      });
      renderErrors(errorsMap);
      renderTable();
    }

    // ===== 요약: 컴퓨터용 (3칸 나란히) =====
    function renderSummaryColumns() {
      const ports = ["인천", "평택", "대산"];
      summaryWrap.innerHTML = ports
        .map(function (port) {
          const items = getFiltered(port).filter(matchesSummaryRule);
          let body = "";
          if (items.length === 0) {
            body = "<div class='sum-empty'>표시할 스케줄이 없습니다.</div>";
          } else {
            body = items
              .map(function (item) {
                return (
                  "<div class='sum-item" + (isBig(item) ? " big" : "") + "'" + refAttr(item) + ">" +
                    "<div class='sum-line1'>" +
                      "<span class='sum-vessel'>" + esc(item.vessel) + "</span>" +
                      "<span class='sum-time'>" + esc(shortTime(item.time)) + "</span>" +
                    "</div>" +
                    transitBadge(item) +
                    "<div class='sum-station'>" + esc(item.station) + "</div>" +
                  "</div>"
                );
              })
              .join("");
          }
          return (
            "<div class='sum-col'>" +
              "<div class='sum-head sum-head-" + port + "'>" + port + "<small>" + items.length + "건</small></div>" +
              body +
            "</div>"
          );
        })
        .join("");
    }

    // ===== 요약: 폰용 (시간대별 표, 가로 = 항구) =====
    function renderSummaryTimeline() {
      const ports = ["인천", "평택", "대산"];
      const now = new Date();
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      const todayMd = pad2(now.getMonth() + 1) + "-" + pad2(now.getDate());
      const tomorrowMd = pad2(tomorrow.getMonth() + 1) + "-" + pad2(tomorrow.getDate());

      const counts = {};
      const groups = {};
      const order = [];

      ports.forEach(function (port) {
        const items = getFiltered(port).filter(matchesSummaryRule);
        counts[port] = items.length;
        items.forEach(function (item) {
          const parts = String(item.time).trim().split(" ");
          if (parts.length !== 2) return;
          const hm = parts[1].split(":");
          const key = parts[0] + " " + hm[0];
          if (!groups[key]) {
            groups[key] = { date: parts[0], hour: hm[0], cells: { "인천": [], "평택": [], "대산": [] } };
            order.push(key);
          }
          groups[key].cells[port].push({ item: item, min: hm[1] });
        });
      });

      order.sort();

      let html = "<div class='tl-grid'>";
      html += "<div class='tl-head tl-head-time'>시</div>";
      ports.forEach(function (port) {
        html += "<div class='tl-head sum-head-" + port + "'>" + port + "<small>" + counts[port] + "건</small></div>";
      });

      if (order.length === 0) {
        html += "<div class='tl-empty'>표시할 스케줄이 없습니다.</div>";
      }

      let lastDate = todayMd;
      order.forEach(function (key) {
        const g = groups[key];
        if (g.date !== lastDate) {
          html += "<div class='tl-date'>" + esc(g.date) + (g.date === tomorrowMd ? " (내일)" : "") + "</div>";
          lastDate = g.date;
        }
        html += "<div class='tl-hour'>" + esc(g.hour) + "시</div>";
        ports.forEach(function (port) {
          const list = g.cells[port];
          html += "<div class='tl-cell'>";
          list.forEach(function (c) {
            html +=
              "<div class='tl-item" + (isBig(c.item) ? " big" : "") + "'" + refAttr(c.item) + ">" +
                "<div class='tl-min'>" + esc(c.min) + "분</div>" +
                "<div class='tl-name'>" + esc(c.item.vessel) + "</div>" +
                transitBadge(c.item) +
                "<div class='tl-st'>" + esc(c.item.station) + "</div>" +
              "</div>";
          });
          html += "</div>";
        });
      });

      html += "</div>";
      summaryWrap.innerHTML = html;
    }

    function renderSummary() {
      if (isNarrow()) {
        renderSummaryTimeline();
      } else {
        renderSummaryColumns();
      }
    }

    // ===== 상세 목록 (대산 / 보령 / 전체) =====
    function renderDetail(tab) {
      const info = TAB_INFO[tab];
      const items = getFiltered(tab);
      const now = new Date();
      const soonLimit = new Date(now.getTime() + 60 * 60 * 1000);
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      const todayMd = pad2(now.getMonth() + 1) + "-" + pad2(now.getDate());
      const tomorrowMd = pad2(tomorrow.getMonth() + 1) + "-" + pad2(tomorrow.getDate());

      let html =
        "<div class='dt-legend'>" + esc(info.note) +
        "<br>회색: 이미 지난 시간 / 노란색: 1시간 이내 / 빨간색: 대산 16만톤 이상 / 보라색 표시: 통과선박" +
        "<br>대산 선박을 누르면 상세정보가 나옵니다.</div>";
      html += "<div class='dt-card'>";
      html += "<div class='dt-title " + info.cls + "'>" + info.label + "<small>" + items.length + "건</small></div>";

      if (items.length === 0) {
        html += "<div class='dt-empty'>현재 시각 기준 표시할 스케줄이 없습니다.</div></div>";
        detailWrap.innerHTML = html;
        return;
      }

      html += "<table class='dt'><thead><tr>" +
        "<th>도선사</th><th>선명</th><th>POB</th><th>도선점</th><th>콜사인</th><th>대리점</th><th class='num'>톤수</th>" +
        "</tr></thead><tbody>";

      let lastDate = null;
      items.forEach(function (item) {
        const parts = String(item.time).trim().split(" ");
        const date = parts[0];
        const hm = parts.length === 2 ? parts[1] : item.time;

        if (date !== lastDate) {
          let label = date;
          if (date === todayMd) label += " (오늘)";
          else if (date === tomorrowMd) label += " (내일)";
          html += "<tr class='date-row'><td colspan='7'>" + esc(label) + "</td></tr>";
          lastDate = date;
        }

        const d = parseScheduleTime(item.time);
        const big = isBig(item);
        let cls = "row p-" + item.port;
        if (d && d < now) cls += " past";
        else if (d && d <= soonLimit) cls += " soon";
        if (big) cls += " big";

        let badges = "";
        if (tab === "ALL") {
          badges += "<span class='badge badge-" + item.port + "'>" + esc(item.port) + "</span>";
          if (isBoryeong(item)) badges += "<span class='badge badge-보령'>보령</span>";
        }

        const tonCell = (big ? "<span class='big-tag'>16만↑</span>" : "") + val(item.tonnage);

        html +=
          "<tr class='" + cls + "'" + refAttr(item) + ">" +
            "<td class='c-pilot' data-l='도선사'>" + val(item.pilot) + "</td>" +
            "<td class='c-vessel'>" + badges + esc(item.vessel) + "</td>" +
            "<td class='c-time'>" + esc(hm) + "</td>" +
            "<td class='c-route'>" + transitBadge(item) + routeHtml(item.station) + "</td>" +
            "<td class='c-call' data-l='콜사인'>" + val(item.callSign) + "</td>" +
            "<td class='c-agent' data-l='대리점'>" + val(item.agent) + "</td>" +
            "<td class='c-ton num' data-l='톤수'>" + tonCell + "</td>" +
          "</tr>";
      });

      html += "</tbody></table></div>";
      detailWrap.innerHTML = html;
    }

    function renderTable() {
      rowRefs = [];
      const isSummary = currentPort === "SUMMARY";

      detailWrap.style.display = isSummary ? "none" : "block";
      summaryWrap.style.display = isSummary ? "grid" : "none";
      summaryNote.style.display = isSummary ? "block" : "none";

      if (isSummary) {
        renderSummary();
        return;
      }

      renderDetail(currentPort);
    }

    // ===== 상세정보 창 (대산 전용) =====
    function dmRow(label, html) {
      if (!html || html === "-") return "";
      return (
        "<div class='dm-row'>" +
          "<div class='dm-l'>" + esc(label) + "</div>" +
          "<div class='dm-v'>" + html + "</div>" +
        "</div>"
      );
    }

    function openDetail(item) {
      const now = new Date();
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      const todayMd = pad2(now.getMonth() + 1) + "-" + pad2(now.getDate());
      const tomorrowMd = pad2(tomorrow.getMonth() + 1) + "-" + pad2(tomorrow.getDate());

      const parts = String(item.time).trim().split(" ");
      const date = parts.length === 2 ? parts[0] : "";
      const hm = parts.length === 2 ? parts[1] : item.time;

      let dateLabel = date;
      if (date === todayMd) dateLabel += " (오늘)";
      else if (date === tomorrowMd) dateLabel += " (내일)";

      let tags = "<span class='badge badge-" + item.port + "'>" + esc(item.port) + "</span>";
      if (isBoryeong(item)) tags += "<span class='badge badge-보령'>보령</span>";
      if (isTransit(item)) tags += "<div class='transit-badge'>통과선박</div>";
      if (isBig(item)) tags += "<span class='big-tag'>16만톤 이상</span>";

      // 공통: 대리점만 / 추가: 흘수, 전장, 접안, 화물, 담당자, 연락처
      let rows = dmRow("대리점", val(item.agent));

      const map = {};
      (item.detail || []).forEach(function (pair) {
        if (pair && pair[0]) map[pair[0]] = pair[1];
      });
      DETAIL_LABELS.forEach(function (label) {
        if (map[label] && map[label] !== "-") {
          rows += dmRow(label, esc(map[label]));
        }
      });

      modalSheet.innerHTML =
        "<div class='dm-head'>" +
          "<div>" +
            "<div class='dm-title'>" + esc(item.vessel) + "</div>" +
            "<div class='dm-tags'>" + tags + "</div>" +
          "</div>" +
          "<button class='dm-close' id='dmClose' type='button' aria-label='닫기'>✕</button>" +
        "</div>" +
        "<div class='dm-key'>" +
          "<div class='dm-date'>" + esc(dateLabel) + " 도선시간</div>" +
          "<div class='dm-time'>" + esc(hm) + "</div>" +
          "<div class='dm-route'>" + esc(item.station) + "</div>" +
        "</div>" +
        "<div class='dm-body'>" + rows + "</div>";

      modalOverlay.classList.add("open");
      document.body.style.overflow = "hidden";
      modalSheet.scrollTop = 0;
    }

    function closeDetail() {
      modalOverlay.classList.remove("open");
      document.body.style.overflow = "";
    }

    document.addEventListener("click", function (e) {
      if (e.target.closest("#dmClose")) {
        closeDetail();
        return;
      }
      if (e.target === modalOverlay) {
        closeDetail();
        return;
      }

      const el = e.target.closest("[data-ref]");
      if (el) {
        const it = rowRefs[Number(el.getAttribute("data-ref"))];
        if (it) openDetail(it);
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeDetail();
    });

    tabButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        tabButtons.forEach(function (b) {
          b.classList.remove("active");
        });
        btn.classList.add("active");
        currentPort = btn.dataset.port;
        renderTable();
      });
    });

    searchInput.addEventListener("input", function (e) {
      searchKeyword = e.target.value.trim();
      renderTable();
    });

    // 화면 폭이 좁음/넓음으로 바뀔 때만 다시 그리기 (폰 회전 등)
    window.addEventListener("resize", function () {
      const nowNarrow = isNarrow();
      if (nowNarrow !== lastNarrow) {
        lastNarrow = nowNarrow;
        if (currentPort === "SUMMARY") renderTable();
      }
    });

    const refreshBtn = document.getElementById("refreshBtn");
    refreshBtn.addEventListener("click", async function () {
      refreshBtn.disabled = true;
      lastUpdatedEl.textContent = "업데이트: 불러오는 중...";
      await init();
      refreshBtn.disabled = false;
    });

    init();
  </script>
</body>
</html>
