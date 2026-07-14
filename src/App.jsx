import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  BarChart3,
  Bot,
  Download,
  ExternalLink,
  FileText,
  Gauge,
  MapPinned,
  Network,
  RefreshCw,
  Send,
  Shield,
  Table2,
  User,
  Wifi,
  WifiOff,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const WS_URL = "ws://127.0.0.1:8000/ws/chat";
const API_BASE = "http://127.0.0.1:8000";
const CHART_COLORS = ["#2563eb", "#0f9f6e", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"];

const suggestions = [
  "Who are the accused in FIR KSP/2023/0042?",
  "Build a network around Ravi Kumar",
  "Show monthly crime trends",
  "Which district has the highest crime count?",
  "Generate a case report for FIR KSP/2023/0042",
];

function stableId(prefix) {
  const existing = localStorage.getItem(prefix);
  if (existing) return existing;
  const value = `${prefix}-${crypto.randomUUID()}`;
  localStorage.setItem(prefix, value);
  return value;
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
    graphHtmlPaths: artifacts.graph_html_path || [],
    pdfPath: artifacts.summary_report_pdf_path || null,
    chart: parseMaybeJson(artifacts.chart_data),
    map: parseMaybeJson(artifacts.map_data),
    table: parseMaybeJson(artifacts.table_data) || [],
  };
}

function chartRows(chart) {
  if (!chart || typeof chart !== "object") return [];
  if (Array.isArray(chart.x) && Array.isArray(chart.y)) {
    return chart.x.map((name, index) => ({ name, value: chart.y[index] ?? 0 }));
  }
  if (Array.isArray(chart.labels) && Array.isArray(chart.values)) {
    return chart.labels.map((name, index) => ({ name, value: chart.values[index] ?? 0 }));
  }
  return [];
}

function tableRows(table) {
  if (!Array.isArray(table)) return [];
  return table;
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

function App() {
  const [userId] = useState(() => stableId("cluvo-user"));
  const [sessionId] = useState(() => stableId("cluvo-session"));
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Cluvo is ready. Ask about FIRs, people, networks, trends, hotspots, or case reports.",
    },
  ]);
  const [input, setInput] = useState("");
  const [connection, setConnection] = useState("connecting");
  const [status, setStatus] = useState("Connecting to Cluvo...");
  const [artifacts, setArtifacts] = useState(normalizeArtifacts({}));
  const [activePanel, setActivePanel] = useState("report");
  const socketRef = useRef(null);
  const transcriptRef = useRef(null);

  const connect = () => {
    if (socketRef.current) socketRef.current.close();
    setConnection("connecting");
    setStatus("Connecting to Cluvo...");

    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnection("online");
      setStatus("Connected");
    };

    socket.onclose = () => {
      setConnection("offline");
      setStatus("Disconnected");
    };

    socket.onerror = () => {
      setConnection("offline");
      setStatus("Connection error");
    };

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.type === "status") {
        setStatus(payload.message || "Cluvo is thinking...");
        return;
      }

      if (payload.type === "error") {
        setMessages((prev) => [...prev, { role: "assistant", content: payload.message }]);
        setStatus("Error");
        return;
      }

      if (payload.type === "assistant_message") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: payload.message || "Done." },
        ]);
        setArtifacts(normalizeArtifacts(payload.artifacts));
        setStatus("Ready");
      }
    };
  };

  useEffect(() => {
    connect();
    return () => socketRef.current?.close();
  }, []);

  useEffect(() => {
    transcriptRef.current?.scrollTo({
      top: transcriptRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const sendMessage = (text = input) => {
    const clean = text.trim();
    if (!clean || socketRef.current?.readyState !== WebSocket.OPEN) return;

    socketRef.current.send(
      JSON.stringify({
        user_id: userId,
        session_id: sessionId,
        message: clean,
      })
    );

    setMessages((prev) => [...prev, { role: "user", content: clean }]);
    setInput("");
    setStatus("Sending...");
  };

  const latestGraphUrl = useMemo(() => {
    const first = artifacts.graphHtmlPaths?.[0];
    return artifactUrl(first);
  }, [artifacts.graphHtmlPaths]);

  const pdfUrl = useMemo(() => artifactUrl(artifacts.pdfPath), [artifacts.pdfPath]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <Shield size={28} />
          </div>
          <div>
            <h1>Cluvo</h1>
            <p>KSP crime intelligence assistant</p>
          </div>
        </div>

        <div className={`connection ${connection}`}>
          {connection === "online" ? <Wifi size={18} /> : <WifiOff size={18} />}
          <span>{status}</span>
        </div>

        <div className="identity-block">
          <div>
            <span>User</span>
            <strong>{userId.replace("cluvo-user-", "").slice(0, 8)}</strong>
          </div>
          <div>
            <span>Session</span>
            <strong>{sessionId.replace("cluvo-session-", "").slice(0, 8)}</strong>
          </div>
        </div>

        <div className="prompt-stack">
          <div className="section-label">Try These</div>
          {suggestions.map((suggestion) => (
            <button key={suggestion} type="button" onClick={() => sendMessage(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>
      </aside>

      <main className="chat-area">
        <header className="topbar">
          <div>
            <p>Live assistant workspace</p>
            <h2>Ask Cluvo</h2>
          </div>
          <button className="icon-button" type="button" onClick={connect} title="Reconnect">
            <RefreshCw size={18} />
          </button>
        </header>

        <section className="transcript" ref={transcriptRef}>
          {messages.map((message, index) => (
            <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <div className="avatar">{message.role === "assistant" ? <Bot size={18} /> : <User size={18} />}</div>
              <div className="bubble">
                {String(message.content)
                  .split("\n")
                  .map((line, lineIndex) => (
                    <p key={`${line}-${lineIndex}`}>{line || "\u00a0"}</p>
                  ))}
              </div>
            </article>
          ))}
        </section>

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            sendMessage();
          }}
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about FIRs, suspects, networks, trends, hotspots, or reports..."
          />
          <button type="submit" title="Send message" disabled={connection !== "online"}>
            <Send size={18} />
          </button>
        </form>
      </main>

      <aside className="artifact-area">
        <div className="artifact-header">
          <div>
            <p>Outputs</p>
            <h2>Intelligence Board</h2>
          </div>
          <Gauge size={22} />
        </div>

        <nav className="panel-tabs" aria-label="Artifact panels">
          <button className={activePanel === "report" ? "active" : ""} onClick={() => setActivePanel("report")} title="Reports">
            <FileText size={17} />
          </button>
          <button className={activePanel === "graph" ? "active" : ""} onClick={() => setActivePanel("graph")} title="Graphs">
            <Network size={17} />
          </button>
          <button className={activePanel === "chart" ? "active" : ""} onClick={() => setActivePanel("chart")} title="Charts">
            <BarChart3 size={17} />
          </button>
          <button className={activePanel === "map" ? "active" : ""} onClick={() => setActivePanel("map")} title="Map">
            <MapPinned size={17} />
          </button>
          <button className={activePanel === "table" ? "active" : ""} onClick={() => setActivePanel("table")} title="Table">
            <Table2 size={17} />
          </button>
        </nav>

        {activePanel === "report" && <ReportPanel pdfUrl={pdfUrl} pdfPath={artifacts.pdfPath} />}
        {activePanel === "graph" && <GraphPanel graphUrl={latestGraphUrl} graphPaths={artifacts.graphHtmlPaths} />}
        {activePanel === "chart" && <ChartPanel chart={artifacts.chart} />}
        {activePanel === "map" && <MapPanel map={artifacts.map} />}
        {activePanel === "table" && <TablePanel table={artifacts.table} />}
      </aside>
    </div>
  );
}

function EmptyPanel({ icon: Icon, title, text }) {
  return (
    <div className="empty-panel">
      <Icon size={30} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function ReportPanel({ pdfUrl, pdfPath }) {
  if (!pdfPath) {
    return <EmptyPanel icon={FileText} title="No report yet" text="Ask Cluvo to generate an FIR case report." />;
  }

  return (
    <section className="panel-content">
      <div className="artifact-tile">
        <FileText size={22} />
        <div>
          <h3>FIR Summary PDF</h3>
          <p>{pdfPath}</p>
        </div>
      </div>
      <a className="action-link" href={pdfUrl} target="_blank" rel="noreferrer">
        <Download size={17} />
        Open PDF
      </a>
    </section>
  );
}

function GraphPanel({ graphUrl, graphPaths }) {
  if (!graphPaths?.length) {
    return <EmptyPanel icon={Network} title="No graph yet" text="Ask for a network around a named person." />;
  }

  return (
    <section className="panel-content graph-panel">
      <div className="graph-actions">
        {graphPaths.map((path, index) => (
          <a key={path} className="small-link" href={artifactUrl(path)} target="_blank" rel="noreferrer">
            <ExternalLink size={15} />
            Graph {index + 1}
          </a>
        ))}
      </div>
      {graphUrl ? <iframe title="Cluvo graph" src={graphUrl} /> : null}
    </section>
  );
}

function ChartPanel({ chart }) {
  const rows = chartRows(chart);
  if (!rows.length) {
    return <EmptyPanel icon={BarChart3} title="No chart yet" text="Ask Cluvo for trends, counts, or breakdowns." />;
  }

  const type = chart?.type || "bar";

  return (
    <section className="panel-content chart-panel">
      <div className="panel-title">
        <Activity size={18} />
        <h3>{chart?.title || "Analytics"}</h3>
      </div>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height="100%">
          {type === "line" ? (
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          ) : type === "pie" ? (
            <PieChart>
              <Tooltip />
              <Pie data={rows} dataKey="value" nameKey="name" innerRadius={46} outerRadius={82}>
                {rows.map((_, index) => (
                  <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f9f6e" radius={[6, 6, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function MapPanel({ map }) {
  const points = map?.points || [];
  if (!points.length) {
    return <EmptyPanel icon={MapPinned} title="No map data yet" text="Ask Cluvo for hotspots or high-crime locations." />;
  }

  const maxCount = Math.max(...points.map((point) => Number(point.incident_count || 1)));

  return (
    <section className="panel-content map-panel">
      <div className="map-canvas">
        {points.slice(0, 18).map((point, index) => {
          const size = 18 + (Number(point.incident_count || 1) / maxCount) * 34;
          return (
            <div
              key={`${point.location_name}-${index}`}
              className="map-point"
              style={{
                width: size,
                height: size,
                left: `${12 + ((index * 19) % 74)}%`,
                top: `${16 + ((index * 31) % 62)}%`,
              }}
              title={`${point.location_name || point.district}: ${point.incident_count} incidents`}
            />
          );
        })}
      </div>
      <div className="point-list">
        {points.slice(0, 6).map((point, index) => (
          <div key={`${point.location_name}-${index}`}>
            <strong>{point.location_name || point.district || "Location"}</strong>
            <span>{point.incident_count} incidents</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function TablePanel({ table }) {
  const rows = tableRows(table);
  const columns = rowColumns(rows);

  if (!rows.length) {
    return <EmptyPanel icon={Table2} title="No table yet" text="Ask Cluvo for counts, lists, or analytics." />;
  }

  return (
    <section className="panel-content table-panel">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((row, rowIndex) => (
              <tr key={rowIndex}>
                {columns.map((column, columnIndex) => (
                  <td key={column}>{String(getCell(row, column, columnIndex) ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default App;
