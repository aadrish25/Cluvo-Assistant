const WS_URL = "ws://127.0.0.1:8000/ws/chat";
const API_BASE = "http://127.0.0.1:8000";
const CHART_COLORS = ["#2563eb", "#0f9f6e", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"];

const state = {
  socket: null,
  connection: "connecting",
  activePanel: "report",
  statusNode: null,
  streamingNode: null,
  streamingText: "",
  artifacts: {
    graphHtmlPaths: [],
    pdfPath: null,
    chart: null,
    map: null,
    table: [],
  },
};

const els = {
  connection: document.querySelector("#connection"),
  statusText: document.querySelector("#statusText"),
  userIdView: document.querySelector("#userIdView"),
  sessionIdView: document.querySelector("#sessionIdView"),
  transcript: document.querySelector("#transcript"),
  composer: document.querySelector("#composer"),
  messageInput: document.querySelector("#messageInput"),
  sendBtn: document.querySelector("#sendBtn"),
  reconnectBtn: document.querySelector("#reconnectBtn"),
  panelContent: document.querySelector("#panelContent"),
  panelTabs: document.querySelectorAll(".panel-tabs button"),
  promptButtons: document.querySelectorAll("[data-prompt]"),
};

function stableId(key) {
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const value = `${key}-${crypto.randomUUID()}`;
  localStorage.setItem(key, value);
  return value;
}

const userId = stableId("cluvo-user");
const sessionId = stableId("cluvo-session");
els.userIdView.textContent = userId.replace("cluvo-user-", "").slice(0, 8);
els.sessionIdView.textContent = sessionId.replace("cluvo-session-", "").slice(0, 8);

function setConnection(status, label) {
  state.connection = status;
  els.connection.className = `connection ${status}`;
  els.statusText.textContent = label;
  els.sendBtn.disabled = status !== "online";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function addMessage(role, content) {
  const message = document.createElement("article");
  message.className = `message ${role}`;
  const avatarText = role === "assistant" ? "C" : "U";
  const safeLines = String(content || "")
    .split("\n")
    .map((line) => `<p>${escapeHtml(line || " ")}</p>`)
    .join("");
  message.innerHTML = `
    <div class="avatar">${avatarText}</div>
    <div class="bubble">${safeLines}</div>
  `;
  els.transcript.appendChild(message);
  els.transcript.scrollTo({ top: els.transcript.scrollHeight, behavior: "smooth" });
}

function showChatStatus(content) {
  const label = content || "Figuring";

  if (!state.statusNode) {
    const statusNode = document.createElement("article");
    statusNode.className = "chat-status";
    statusNode.innerHTML = `
      <span class="chat-status-dot"></span>
      <span class="chat-status-text"></span>
    `;
    els.transcript.appendChild(statusNode);
    state.statusNode = statusNode;
  }

  state.statusNode.querySelector(".chat-status-text").textContent = label;
  els.transcript.scrollTo({ top: els.transcript.scrollHeight, behavior: "smooth" });
}

function clearChatStatus() {
  if (!state.statusNode) return;
  state.statusNode.remove();
  state.statusNode = null;
}

function ensureStreamingMessage() {
  if (state.streamingNode) return state.streamingNode;

  clearChatStatus(); // stop showing the spinner once real content starts

  const message = document.createElement("article");
  message.className = "message assistant";
  message.innerHTML = `
    <div class="avatar">C</div>
    <div class="bubble"><p></p></div>
  `;
  els.transcript.appendChild(message);
  state.streamingNode = message;
  state.streamingText = "";
  return message;
}

function appendStreamChunk(content) {
  const node = ensureStreamingMessage();
  state.streamingText += content;

  const safeLines = state.streamingText
    .split("\n")
    .map((line) => `<p>${escapeHtml(line || " ")}</p>`)
    .join("");
  node.querySelector(".bubble").innerHTML = safeLines;

  els.transcript.scrollTo({ top: els.transcript.scrollHeight, behavior: "smooth" });
}

function clearStreamingMessage() {
  state.streamingNode = null;
  state.streamingText = "";
}

function parseMaybeJson(value) {
  if (!value) return null;
  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return value;
    }
  }
  return value;
}

function artifactUrl(path) {
  if (!path) return null;
  const normalized = String(path).replaceAll("\\", "/");
  const reportsIndex = normalized.lastIndexOf("reports/");
  if (reportsIndex >= 0) return `${API_BASE}/${normalized.slice(reportsIndex)}`;
  const graphsIndex = normalized.lastIndexOf("graph_artifacts/");
  if (graphsIndex >= 0) return `${API_BASE}/${normalized.slice(graphsIndex)}`;
  if (normalized.startsWith("reports/") || normalized.startsWith("graph_artifacts/")) {
    return `${API_BASE}/${normalized}`;
  }
  return normalized;
}

function normalizeArtifacts(raw) {
  const artifacts = raw || {};
  return {
    graphHtmlPaths: artifacts.graph_html_paths || [],
    pdfPath: artifacts.summary_report_pdf_path || null,
    chart: parseMaybeJson(artifacts.chart_data),
    map: parseMaybeJson(artifacts.map_data),
    table: parseMaybeJson(artifacts.table_data) || [],
  };
}

function statusLabel(payload) {
  return payload.message || payload.status || payload.event || payload.content || "Figuring";
}

function connect() {
  if (state.socket) state.socket.close();
  setConnection("connecting", "Connecting to Cluvo...");

  const socket = new WebSocket(WS_URL);
  state.socket = socket;

  socket.onopen = () => setConnection("online", "Connected");
  socket.onclose = () => setConnection("offline", "Disconnected");
  socket.onerror = () => setConnection("offline", "Connection error");

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);

    if (payload.type == "stream_chunk"){
      appendStreamChunk(payload.content || "");
      return;
    }

    if (payload.type === "status") {
      if(!state.streamingNode) showChatStatus(statusLabel(payload));
      return;
    }

    if (payload.type === "error") {
      clearChatStatus();
      clearStreamingMessage();
      addMessage("assistant", payload.message || "Something went wrong.");
      els.statusText.textContent = "Connected";
      return;
    }

    if (payload.type === "assistant_message") {
      clearChatStatus();
      if (!state.streamingNode) {
      // no chunks arrived (e.g. tool-only run) — add the message normally
      addMessage("assistant", payload.message || "Done.");
      }
      clearStreamingMessage();
      state.artifacts = normalizeArtifacts(payload.artifacts);
      els.statusText.textContent = "Connected";
      renderPanel();
    }
  };
}

function sendMessage(text) {
  const message = String(text ?? els.messageInput.value).trim();
  if (!message || state.socket?.readyState !== WebSocket.OPEN) return;

  state.socket.send(
    JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      message,
    })
  );

  addMessage("user", message);
  showChatStatus("Figuring");
  els.messageInput.value = "";
  els.statusText.textContent = "Connected";
}

function emptyPanel(icon, title, text) {
  els.panelContent.innerHTML = `
    <div class="empty-panel">
      <div class="empty-icon">${icon}</div>
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(text)}</p>
    </div>
  `;
}

function renderReport() {
  const { pdfPath } = state.artifacts;
  if (!pdfPath) {
    emptyPanel("PDF", "No report yet", "Ask Cluvo to generate an FIR case report.");
    return;
  }

  const url = artifactUrl(pdfPath);
  els.panelContent.innerHTML = `
    <div class="artifact-tile">
      <div class="tile-icon">PDF</div>
      <div>
        <h3>FIR Summary PDF</h3>
        <p>${escapeHtml(pdfPath)}</p>
      </div>
    </div>
    <a class="action-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Open PDF</a>
  `;
}

function renderGraph() {
  const paths = state.artifacts.graphHtmlPaths || [];
  if (!paths.length) {
    emptyPanel("NET", "No graph yet", "Ask for a network around a named person.");
    return;
  }

  const links = paths
    .map(
      (path, index) =>
        `<a class="small-link" href="${escapeHtml(artifactUrl(path))}" target="_blank" rel="noreferrer">Graph ${index + 1}</a>`
    )
    .join("");

  els.panelContent.innerHTML = `
    <div class="graph-panel">
      <div class="graph-actions">${links}</div>
      <iframe title="Cluvo graph" src="${escapeHtml(artifactUrl(paths[0]))}"></iframe>
    </div>
  `;
}

function chartRows(chart) {
  if (!chart || typeof chart !== "object") return [];
  if (Array.isArray(chart.x) && Array.isArray(chart.y)) {
    return chart.x.map((name, index) => ({ name, value: Number(chart.y[index] || 0) }));
  }
  if (Array.isArray(chart.labels) && Array.isArray(chart.values)) {
    return chart.labels.map((name, index) => ({ name, value: Number(chart.values[index] || 0) }));
  }
  return [];
}

function renderBarChart(rows) {
  const max = Math.max(...rows.map((row) => row.value), 1);
  return `
    <div class="chart-box">
      ${rows
        .slice(0, 14)
        .map((row) => {
          const height = Math.max(8, (row.value / max) * 100);
          return `<div class="bar-item" style="height:${height}%;" title="${escapeHtml(row.name)}: ${row.value}">
            <span>${escapeHtml(row.name)}</span>
          </div>`;
        })
        .join("")}
    </div>
  `;
}

function renderLineChart(rows) {
  const max = Math.max(...rows.map((row) => row.value), 1);
  const points = rows.slice(0, 20).map((row, index, arr) => {
    const x = 30 + (index / Math.max(arr.length - 1, 1)) * 520;
    const y = 280 - (row.value / max) * 220;
    return { x, y, row };
  });
  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const circles = points
    .map((point) => `<circle cx="${point.x}" cy="${point.y}" r="4"><title>${escapeHtml(point.row.name)}: ${point.row.value}</title></circle>`)
    .join("");
  return `
    <div class="line-chart">
      <svg viewBox="0 0 580 340" role="img">
        <line x1="30" y1="280" x2="550" y2="280" stroke="#d9e1eb" />
        <line x1="30" y1="40" x2="30" y2="280" stroke="#d9e1eb" />
        <polyline points="${polyline}" fill="none" stroke="#2563eb" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
        <g fill="#2563eb">${circles}</g>
      </svg>
    </div>
  `;
}

function renderPieChart(rows) {
  const total = rows.reduce((sum, row) => sum + row.value, 0) || 1;
  let offset = 0;
  const slices = rows.slice(0, 6).map((row, index) => {
    const fraction = row.value / total;
    const dash = `${fraction * 100} ${100 - fraction * 100}`;
    const circle = `<circle r="70" cx="120" cy="120" fill="transparent" stroke="${CHART_COLORS[index % CHART_COLORS.length]}" stroke-width="42" stroke-dasharray="${dash}" stroke-dashoffset="${-offset}" transform="rotate(-90 120 120)">
      <title>${escapeHtml(row.name)}: ${row.value}</title>
    </circle>`;
    offset += fraction * 100;
    return circle;
  });
  const legend = rows
    .slice(0, 6)
    .map((row, index) => `<text x="230" y="${70 + index * 28}" fill="#172033" font-size="14">${escapeHtml(row.name)} (${row.value})</text>`)
    .join("");
  return `
    <div class="pie-chart">
      <svg viewBox="0 0 580 340" role="img">
        ${slices.join("")}
        <circle cx="120" cy="120" r="40" fill="#ffffff" />
        ${legend}
      </svg>
    </div>
  `;
}

function renderChart() {
  const chart = state.artifacts.chart;
  const rows = chartRows(chart);
  if (!rows.length) {
    emptyPanel("CHT", "No chart yet", "Ask Cluvo for trends, counts, or breakdowns.");
    return;
  }

  const type = chart.type || "bar";
  const chartHtml = type === "line" ? renderLineChart(rows) : type === "pie" ? renderPieChart(rows) : renderBarChart(rows);
  els.panelContent.innerHTML = `
    <div class="panel-title">
      <h3>${escapeHtml(chart.title || "Analytics")}</h3>
    </div>
    ${chartHtml}
  `;
}

function renderMap() {
  const points = state.artifacts.map?.points || [];
  if (!points.length) {
    emptyPanel("MAP", "No map data yet", "Ask Cluvo for hotspots or high-crime locations.");
    return;
  }

  const max = Math.max(...points.map((point) => Number(point.incident_count || 1)), 1);
  const markers = points
    .slice(0, 18)
    .map((point, index) => {
      const size = 18 + (Number(point.incident_count || 1) / max) * 34;
      const left = 12 + ((index * 19) % 74);
      const top = 16 + ((index * 31) % 62);
      return `<div class="map-point" style="width:${size}px;height:${size}px;left:${left}%;top:${top}%;" title="${escapeHtml(point.location_name || point.district)}: ${escapeHtml(point.incident_count)} incidents"></div>`;
    })
    .join("");

  const list = points
    .slice(0, 6)
    .map(
      (point) => `<div>
        <strong>${escapeHtml(point.location_name || point.district || "Location")}</strong>
        <span>${escapeHtml(point.incident_count)} incidents</span>
      </div>`
    )
    .join("");

  els.panelContent.innerHTML = `
    <div class="map-canvas">${markers}</div>
    <div class="point-list">${list}</div>
  `;
}

function tableRows(table) {
  return Array.isArray(table) ? table : [];
}

function rowColumns(rows) {
  if (!rows.length) return [];
  const first = rows[0];
  if (Array.isArray(first)) return first.map((_, index) => `Column ${index + 1}`);
  if (first && typeof first === "object") return Object.keys(first);
  return ["Value"];
}

function getCell(row, column, index) {
  if (Array.isArray(row)) return row[index];
  if (row && typeof row === "object") return row[column];
  return row;
}

function renderTable() {
  const rows = tableRows(state.artifacts.table);
  const columns = rowColumns(rows);
  if (!rows.length) {
    emptyPanel("TBL", "No table yet", "Ask Cluvo for counts, lists, or analytics.");
    return;
  }

  els.panelContent.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows
            .slice(0, 50)
            .map(
              (row) => `<tr>${columns
                .map((column, index) => `<td>${escapeHtml(getCell(row, column, index))}</td>`)
                .join("")}</tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderPanel() {
  if (state.activePanel === "report") renderReport();
  if (state.activePanel === "graph") renderGraph();
  if (state.activePanel === "chart") renderChart();
  if (state.activePanel === "map") renderMap();
  if (state.activePanel === "table") renderTable();
}

els.composer.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage();
});

els.reconnectBtn.addEventListener("click", connect);

els.promptButtons.forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

els.panelTabs.forEach((button) => {
  button.addEventListener("click", () => {
    els.panelTabs.forEach((tab) => tab.classList.remove("active"));
    button.classList.add("active");
    state.activePanel = button.dataset.panel;
    renderPanel();
  });
});

addMessage("assistant", "Cluvo is ready. Ask about FIRs, people, networks, trends, hotspots, or case reports.");
renderPanel();
connect();
