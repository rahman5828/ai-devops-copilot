import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Activity,
  AlertCircle,
  ArrowRight,
  Bot,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Command,
  Cpu,
  Database,
  FileSearch,
  Gauge,
  History,
  LayoutDashboard,
  Moon,
  Network,
  Play,
  Plus,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  Sparkles,
  Sun,
  Terminal,
  X,
  Zap,
} from "lucide-react";

import {
  analyzeIncident,
  deriveServices,
  getIncidents,
} from "./lib/api";

import type {
  AnalysisResult,
  Incident,
  Severity,
  ServiceSummary,
} from "./types";

type Page =
  | "overview"
  | "analyze"
  | "incidents"
  | "services";

const demoIncidents: Incident[] = [
  {
    id: 42,
    service: "payment-service",
    summary: "Redis connectivity failure",
    severity: "high",
    impact: "high",
    confidence: 95,
    created_at: "2 min ago",
    status: "open",
    root_cause:
      "Redis connectivity failure is preventing the service from starting.",
  },
  {
    id: 41,
    service: "auth-service",
    summary: "Token validation latency regression",
    severity: "medium",
    impact: "medium",
    confidence: 85,
    created_at: "8 min ago",
    status: "monitoring",
  },
  {
    id: 40,
    service: "checkout-api",
    summary: "Database connection pool exhaustion",
    severity: "critical",
    impact: "critical",
    confidence: 92,
    created_at: "46 min ago",
    status: "mitigated",
  },
  {
    id: 39,
    service: "payment-service",
    summary: "Container OOM termination",
    severity: "high",
    impact: "medium",
    confidence: 78,
    created_at: "3 hours ago",
    status: "resolved",
  },
  {
    id: 38,
    service: "notification-worker",
    summary: "Queue consumer backlog",
    severity: "low",
    impact: "low",
    confidence: 64,
    created_at: "7 hours ago",
    status: "resolved",
  },
  {
    id: 37,
    service: "gateway",
    summary: "Upstream TLS handshake failures",
    severity: "medium",
    impact: "high",
    confidence: 81,
    created_at: "1 day ago",
    status: "resolved",
  },
];

const demoServices: ServiceSummary[] = [
  {
    name: "auth-service",
    status: "healthy",
    incidents: 2,
    worstSeverity: "critical",
    lastIncident: "8 min ago",
  },
  {
    name: "checkout-api",
    status: "healthy",
    incidents: 2,
    worstSeverity: "critical",
    lastIncident: "46 min ago",
  },
  {
    name: "gateway",
    status: "healthy",
    incidents: 2,
    worstSeverity: "medium",
    lastIncident: "1 day ago",
  },
  {
    name: "notification-worker",
    status: "healthy",
    incidents: 1,
    worstSeverity: "low",
    lastIncident: "7 hours ago",
  },
  {
    name: "payment-service",
    status: "incident",
    incidents: 2,
    worstSeverity: "high",
    lastIncident: "2 min ago",
  },
  {
    name: "search-indexer",
    status: "healthy",
    incidents: 1,
    worstSeverity: "low",
    lastIncident: "3 days ago",
  },
];

function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  return (
    <span
      className={`badge badge-${severity}`}
    >
      <span className="badge-dot" />
      {severity.toUpperCase()}
    </span>
  );
}

function Confidence({
  value,
}: {
  value: number;
}) {
  const safeValue = Math.max(
    0,
    Math.min(100, Number(value) || 0)
  );

  return (
    <div className="confidence">
      <strong>{Math.round(safeValue)}%</strong>
      <span className="confidence-track">
        <i
          style={{
            width: `${safeValue}%`,
          }}
        />
      </span>
    </div>
  );
}

function App() {
  const [page, setPage] =
    useState<Page>("overview");

  const [incidents, setIncidents] =
    useState<Incident[]>(demoIncidents);

  const [services, setServices] =
    useState<ServiceSummary[]>(demoServices);

  const [loading, setLoading] =
    useState(false);

  const [apiOnline, setApiOnline] =
    useState(false);

  const [dark, setDark] =
    useState(true);

  const [selected, setSelected] =
    useState<Incident | null>(null);

  const [commandOpen, setCommandOpen] =
    useState(false);

  const loadIncidents = async () => {
    try {
      const data = await getIncidents();

      setApiOnline(true);

      if (data.length > 0) {
        setIncidents(data);
        setServices(deriveServices(data));
      }
    } catch {
      setApiOnline(false);
    }
  };

  useEffect(() => {
    void loadIncidents();
  }, []);

  useEffect(() => {
    const onKey = (
      event: KeyboardEvent
    ) => {
      if (
        (event.metaKey ||
          event.ctrlKey) &&
        event.key.toLowerCase() === "k"
      ) {
        event.preventDefault();
        setCommandOpen(true);
      }

      if (event.key === "Escape") {
        setCommandOpen(false);
        setSelected(null);
      }
    };

    window.addEventListener(
      "keydown",
      onKey
    );

    return () =>
      window.removeEventListener(
        "keydown",
        onKey
      );
  }, []);

  const stats = useMemo(
    () => ({
      critical: incidents.filter(
        (i) => i.severity === "critical"
      ).length,

      high: incidents.filter(
        (i) => i.severity === "high"
      ).length,

      medium: incidents.filter(
        (i) => i.severity === "medium"
      ).length,

      confidence: incidents.length
        ? Math.round(
            incidents.reduce(
              (total, incident) =>
                total + incident.confidence,
              0
            ) / incidents.length
          )
        : 0,
    }),
    [incidents]
  );

  const nav = (next: Page) => {
    setPage(next);
    setSelected(null);
  };

  const refresh = async () => {
    setLoading(true);

    try {
      await loadIncidents();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className={
        dark ? "app dark" : "app"
      }
    >
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Terminal size={18} />
          </div>

          <div>
            <strong>
              AI DevOps Copilot
            </strong>
            <small>
              Incident intelligence
            </small>
          </div>
        </div>

        <div className="workspace-pill">
          <span
            className={`status-dot ${
              apiOnline ? "online" : ""
            }`}
          />

          <span>
            {apiOnline
              ? "Live backend"
              : "Demo data"}
          </span>

          <ChevronRight size={14} />
        </div>

        <nav className="nav">
          <button
            className={
              page === "overview"
                ? "active"
                : ""
            }
            onClick={() =>
              nav("overview")
            }
          >
            <LayoutDashboard size={18} />
            Overview
          </button>

          <button
            className={
              page === "analyze"
                ? "active"
                : ""
            }
            onClick={() =>
              nav("analyze")
            }
          >
            <Sparkles size={18} />
            Analyze incident
            <span className="nav-new">
              AI
            </span>
          </button>

          <button
            className={
              page === "incidents"
                ? "active"
                : ""
            }
            onClick={() =>
              nav("incidents")
            }
          >
            <History size={18} />
            Incident history
          </button>

          <button
            className={
              page === "services"
                ? "active"
                : ""
            }
            onClick={() =>
              nav("services")
            }
          >
            <Server size={18} />
            Services
          </button>
        </nav>

        <div className="sidebar-spacer" />

        <div className="sidebar-card">
          <div className="eyebrow">
            <ShieldCheck size={14} />
            EVIDENCE-FIRST
          </div>

          <p>
            Deterministic infrastructure
            signals stay authoritative.
            AI explains — it doesn't invent.
          </p>
        </div>

        <nav className="nav nav-bottom">
          <button>
            <Settings size={18} />
            Settings
          </button>

          <button
            onClick={() => setDark(!dark)}
          >
            {dark ? (
              <Sun size={18} />
            ) : (
              <Moon size={18} />
            )}

            {dark
              ? "Light mode"
              : "Dark mode"}
          </button>
        </nav>

        <div className="user">
          <div className="avatar">
            AR
          </div>

          <div>
            <strong>
              Abdul Rahman
            </strong>
            <small>
              Operator
            </small>
          </div>

          <span className="user-more">
            •••
          </span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="crumb">
            <span>Copilot</span>
            <ChevronRight size={14} />

            <strong>
              {page === "overview"
                ? "Overview"
                : page === "analyze"
                ? "Analyze Incident"
                : page === "incidents"
                ? "Incident History"
                : "Services"}
            </strong>
          </div>

          <div className="top-actions">
            <button
              className="global-search"
              onClick={() =>
                setCommandOpen(true)
              }
            >
              <Search size={17} />
              <span>
                Search incidents,
                services...
              </span>
              <kbd>⌘ K</kbd>
            </button>

            <div className="system-state">
              <span className="status-dot online" />
              {apiOnline
                ? "Backend connected"
                : "Demo mode"}
            </div>

            <button
              className="icon-button"
              onClick={() =>
                setDark(!dark)
              }
            >
              {dark ? (
                <Sun size={18} />
              ) : (
                <Moon size={18} />
              )}
            </button>

            <div className="mini-avatar">
              AR
            </div>
          </div>
        </header>

        {page === "overview" && (
          <Overview
            incidents={incidents}
            stats={stats}
            services={services}
            onAnalyze={() =>
              nav("analyze")
            }
            onSelect={setSelected}
            onRefresh={refresh}
            loading={loading}
          />
        )}

        {page === "analyze" && (
          <Analyze
            onResult={(result) => {
              const item: Incident = {
                id: `new-${Date.now()}`,
                service:
                  result.incident
                    ?.service ||
                  "unknown-service",
                summary:
                  result.root_cause
                    .statement,
                severity:
                  result.severity,
                impact:
                  result.impact,
                confidence:
                  result.confidence <= 1
                    ? result.confidence *
                      100
                    : result.confidence,
                created_at:
                  "just now",
                status: "open",
                root_cause:
                  result.root_cause
                    .statement,
              };

              setIncidents(
                (previous) => [
                  item,
                  ...previous,
                ]
              );

              setServices(
                deriveServices([
                  item,
                  ...incidents,
                ])
              );

              setSelected(item);
            }}
          />
        )}

        {page === "incidents" && (
          <IncidentHistory
            incidents={incidents}
            onSelect={setSelected}
          />
        )}

        {page === "services" && (
          <Services
            services={services}
          />
        )}
      </main>

      {selected && (
        <IncidentDrawer
          incident={selected}
          onClose={() =>
            setSelected(null)
          }
        />
      )}

      {commandOpen && (
        <CommandPalette
          onClose={() =>
            setCommandOpen(false)
          }
          onNavigate={nav}
        />
      )}
    </div>
  );
}

function Overview({
  incidents,
  stats,
  services,
  onAnalyze,
  onSelect,
  onRefresh,
  loading,
}: {
  incidents: Incident[];
  stats: {
    critical: number;
    high: number;
    medium: number;
    confidence: number;
  };
  services: ServiceSummary[];
  onAnalyze: () => void;
  onSelect: (
    incident: Incident
  ) => void;
  onRefresh: () => void;
  loading: boolean;
}) {
  const active = incidents.filter(
    (incident) =>
      incident.status === "open" ||
      incident.status === "monitoring"
  );

  const topIncident =
    incidents[0];

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow blue">
            <Activity size={14} />
            OPERATIONS CENTER
          </div>

          <h1>
            Good evening, Abdul.
          </h1>

          <p>
            Monitor incident activity
            and infrastructure
            intelligence from one place.
          </p>
        </div>

        <div className="heading-actions">
          <button
            className="secondary-button"
            onClick={onRefresh}
          >
            <RefreshCw
              size={16}
              className={
                loading
                  ? "spin"
                  : ""
              }
            />
            Refresh
          </button>

          <button
            className="primary-button"
            onClick={onAnalyze}
          >
            <Plus size={17} />
            New analysis
          </button>
        </div>
      </div>

      {topIncident && (
        <div className="hero-strip">
          <div className="hero-icon">
            <Bot size={23} />
          </div>

          <div>
            <strong>
              AI operational insight
            </strong>

            <p>
              {topIncident.root_cause ||
                topIncident.summary}
            </p>
          </div>

          <div className="hero-meta">
            <span>
              CONFIDENCE{" "}
              <b>
                {Math.round(
                  topIncident.confidence
                )}
                %
              </b>
            </span>

            <span>
              SERVICE{" "}
              <b>
                {topIncident.service}
              </b>
            </span>
          </div>

          <button
            className="ghost-button"
            onClick={() =>
              onSelect(topIncident)
            }
          >
            Investigate
            <ArrowRight size={15} />
          </button>
        </div>
      )}

      <div className="stat-grid">
        <StatCard
          label="Critical incidents"
          value={stats.critical}
          suffix="recorded incidents"
          tone="critical"
          icon={
            <AlertCircle size={17} />
          }
        />

        <StatCard
          label="High incidents"
          value={stats.high}
          suffix="recorded incidents"
          tone="high"
          icon={<Zap size={17} />}
        />

        <StatCard
          label="Medium incidents"
          value={stats.medium}
          suffix="recorded incidents"
          tone="medium"
          icon={<Gauge size={17} />}
        />

        <StatCard
          label="Average confidence"
          value={`${stats.confidence}%`}
          suffix="across analyses"
          icon={
            <ShieldCheck size={17} />
          }
        />
      </div>

      <div className="content-grid">
        <div className="panel incidents-panel">
          <div className="panel-header">
            <div>
              <div className="panel-title">
                Recent incidents
              </div>

              <small>
                Latest signals across
                your services
              </small>
            </div>

            <button
              className="link-button"
              onClick={() =>
                onSelect(incidents[0])
              }
              disabled={!incidents[0]}
            >
              View details
              <ArrowRight size={14} />
            </button>
          </div>

          <div className="table">
            <div className="table-head">
              <span>ID</span>
              <span>SERVICE</span>
              <span>SEVERITY</span>
              <span>IMPACT</span>
              <span>CONFIDENCE</span>
              <span>CREATED</span>
              <span>STATUS</span>
            </div>

            {incidents
              .slice(0, 6)
              .map((incident) => (
                <button
                  className="table-row"
                  key={incident.id}
                  onClick={() =>
                    onSelect(incident)
                  }
                >
                  <span className="mono muted">
                    #{incident.id}
                  </span>

                  <span>
                    <strong>
                      {incident.service}
                    </strong>

                    <small>
                      {incident.summary}
                    </small>
                  </span>

                  <span>
                    <SeverityBadge
                      severity={
                        incident.severity
                      }
                    />
                  </span>

                  <span className="impact">
                    <i
                      className={`impact-line ${incident.impact}`}
                    />
                    {incident.impact.toUpperCase()}
                  </span>

                  <span>
                    <Confidence
                      value={
                        incident.confidence
                      }
                    />
                  </span>

                  <span className="muted">
                    {incident.created_at}
                  </span>

                  <span>
                    <span
                      className={`status-pill ${incident.status}`}
                    >
                      {incident.status}
                    </span>
                  </span>
                </button>
              ))}
          </div>
        </div>

        <div className="side-stack">
          <div className="panel">
            <div className="panel-header">
              <div>
                <div className="panel-title">
                  Service health
                </div>

                <small>
                  Current operational
                  state
                </small>
              </div>

              <button
                className="icon-button"
                onClick={() =>
                  onAnalyze()
                }
              >
                <ArrowRight size={15} />
              </button>
            </div>

            {services
              .slice(0, 5)
              .map((service) => (
                <div
                  className="service-row"
                  key={service.name}
                >
                  <div className="service-name">
                    <span
                      className={`service-dot ${service.status}`}
                    />

                    <div>
                      <strong>
                        {service.name}
                      </strong>

                      <small>
                        {service.incidents}{" "}
                        incidents ·{" "}
                        {service.lastIncident}
                      </small>
                    </div>
                  </div>

                  <SeverityBadge
                    severity={
                      service.worstSeverity
                    }
                  />
                </div>
              ))}
          </div>

          <div className="panel signal-panel">
            <div className="eyebrow">
              <CircleDot size={14} />
              LIVE SIGNALS
            </div>

            <div className="signal-row">
              <span className="signal-icon green">
                <CheckCircle2
                  size={15}
                />
              </span>

              <div>
                <strong>
                  API available
                </strong>

                <small>
                  Evidence pipeline ready
                </small>
              </div>

              <span className="signal-time">
                now
              </span>
            </div>

            <div className="signal-row">
              <span className="signal-icon blue">
                <Bot size={15} />
              </span>

              <div>
                <strong>
                  AI provider
                </strong>

                <small>
                  Analysis engine
                  configured
                </small>
              </div>

              <span className="signal-time">
                ready
              </span>
            </div>

            <div className="signal-row">
              <span className="signal-icon amber">
                <Database
                  size={15}
                />
              </span>

              <div>
                <strong>
                  Incident history
                </strong>

                <small>
                  {incidents.length}{" "}
                  records loaded
                </small>
              </div>

              <span className="signal-time">
                synced
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="active-bar">
        <span className="pulse" />
        <strong>
          {active.length} active
          investigations
        </strong>

        <span>•</span>

        <span>
          Evidence-backed analysis
          enabled
        </span>

        <span className="active-right">
          Last refresh just now
        </span>
      </div>
    </section>
  );
}

function StatCard({
  label,
  value,
  suffix,
  tone,
  icon,
}: {
  label: string;
  value: string | number;
  suffix: string;
  tone?: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      className={`stat-card ${
        tone || ""
      }`}
    >
      <div className="stat-top">
        <span>
          {icon}
          <b>{label}</b>
        </span>

        <span
          className={`stat-dot ${
            tone || ""
          }`}
        />
      </div>

      <div className="stat-value">
        {value}
      </div>

      <div className="stat-suffix">
        {suffix}
      </div>
    </div>
  );
}

function Analyze({
  onResult,
}: {
  onResult: (
    result: AnalysisResult
  ) => void;
}) {
  const [service, setService] =
    useState("payment-service");

  const [cpu, setCpu] =
    useState(85);

  const [memory, setMemory] =
    useState(90);

  const [logs, setLogs] =
    useState(
      "ERROR Redis connection refused\ncontainer restarting...\nconnection refused"
    );

  const [running, setRunning] =
    useState(false);

  const [result, setResult] =
    useState<AnalysisResult | null>(
      null
    );

  const [error, setError] =
    useState("");

  const run = async () => {
    setRunning(true);
    setError("");

    try {
      const data =
        await analyzeIncident({
          service,
          logs,
          cpu,
          memory,
        });

      setResult(data);
      onResult(data);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Analysis failed"
      );

      const fallback: AnalysisResult =
        {
          severity: "high",
          confidence: 0.95,
          impact: "high",

          signals: [
            "error_logs",
            "container_restarting",
          ],

          timeline: [
            "Error-level log evidence was detected.",
            "Container entered a restarting state.",
          ],

          root_cause: {
            statement:
              "Redis connectivity failure is preventing the service from starting.",
            confidence: 0.95,
          },

          evidence: [
            "ERROR Redis connection refused",
            "container restarting...",
          ],

          alternative_hypotheses: [
            "Redis endpoint unavailable",
            "Network policy or DNS issue",
          ],

          recommendations: [
            "Verify Redis availability and endpoint configuration.",
            "Check service-to-Redis network connectivity.",
            "Review recent configuration changes.",
          ],

          incident: {
            service,
          },
        };

      setResult(fallback);
      onResult(fallback);
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow blue">
            <Sparkles size={14} />
            INVESTIGATION
          </div>

          <h1>
            Analyze an incident
          </h1>

          <p>
            Provide observable
            infrastructure evidence.
            The copilot turns it into a
            traceable investigation.
          </p>
        </div>
      </div>

      <div className="analysis-layout">
        <div className="panel analysis-form">
          <div className="form-section">
            <label>SERVICE</label>

            <input
              value={service}
              onChange={(event) =>
                setService(
                  event.target.value
                )
              }
            />
          </div>

          <div className="metric-fields">
            <div>
              <label>CPU %</label>

              <input
                type="number"
                min="0"
                max="100"
                value={cpu}
                onChange={(event) =>
                  setCpu(
                    Number(
                      event.target.value
                    )
                  )
                }
              />
            </div>

            <div>
              <label>MEMORY %</label>

              <input
                type="number"
                min="0"
                max="100"
                value={memory}
                onChange={(event) =>
                  setMemory(
                    Number(
                      event.target.value
                    )
                  )
                }
              />
            </div>
          </div>

          <div className="form-section">
            <label>LOGS</label>

            <textarea
              value={logs}
              onChange={(event) =>
                setLogs(
                  event.target.value
                )
              }
              spellCheck={false}
            />

            <small>
              Paste raw application or
              container output. Monospaced
              input is preserved verbatim.
            </small>
          </div>

          <details className="docker-details">
            <summary>
              <span>
                <Network size={16} />
                Docker evidence
                <em>OPTIONAL</em>
              </span>

              <ChevronRight size={16} />
            </summary>

            <div className="details-body">
              Attach runtime state,
              restart counts, exit code,
              image and OOM evidence
              when available.
            </div>
          </details>

          {error && (
            <div className="error-banner">
              <AlertCircle size={16} />
              Backend analysis failed —
              showing an evidence-safe
              local preview.
            </div>
          )}

          <div className="form-footer">
            <span>
              <ShieldCheck size={15} />
              Evidence is sent to the
              analysis API. Nothing is
              stored locally.
            </span>

            <button
              className="primary-button large"
              onClick={run}
              disabled={running}
            >
              {running ? (
                <>
                  <RefreshCw
                    size={17}
                    className="spin"
                  />
                  Analyzing…
                </>
              ) : (
                <>
                  <Play size={17} />
                  Analyze incident
                </>
              )}
            </button>
          </div>
        </div>

        <div className="panel investigation-panel">
          <div className="panel-header">
            <div>
              <div className="panel-title">
                Investigation flow
              </div>

              <small>
                Every stage is visible and
                auditable
              </small>
            </div>
          </div>

          {[
            "Collecting evidence",
            "Analyzing runtime signals",
            "Evaluating incident severity",
            "Generating root-cause analysis",
            "Validating AI evidence",
          ].map((item, index) => {
            const complete =
              Boolean(result) ||
              (running && index < 3);

            const active =
              running && index === 3;

            return (
              <div
                className={`flow-step ${
                  active
                    ? "running"
                    : complete
                    ? "done"
                    : ""
                }`}
                key={item}
              >
                <span className="flow-node">
                  {active ? (
                    <RefreshCw
                      size={13}
                      className="spin"
                    />
                  ) : complete ? (
                    <CheckCircle2
                      size={14}
                    />
                  ) : (
                    <span />
                  )}
                </span>

                <span>{item}</span>

                {index < 4 && (
                  <ChevronRight
                    size={14}
                    className="flow-arrow"
                  />
                )}
              </div>
            );
          })}

          {result && (
            <div className="result-preview">
              <div className="result-head">
                <span>RESULT</span>

                <SeverityBadge
                  severity={
                    result.severity
                  }
                />
              </div>

              <h3>
                {result.root_cause.statement}
              </h3>

              <Confidence
                value={
                  result.confidence <= 1
                    ? result.confidence *
                      100
                    : result.confidence
                }
              />

              <div className="result-meta">
                <span>
                  Evidence{" "}
                  <strong>
                    {result.evidence
                      ?.length ?? 0}
                  </strong>
                </span>

                <span>
                  Signals{" "}
                  <strong>
                    {result.signals
                      ?.length ?? 0}
                  </strong>
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function IncidentHistory({
  incidents,
  onSelect,
}: {
  incidents: Incident[];
  onSelect: (
    incident: Incident
  ) => void;
}) {
  const [search, setSearch] =
    useState("");

  const [severity, setSeverity] =
    useState("all");

  const filtered =
    incidents.filter((incident) => {
      const matchesSearch =
        `${incident.service} ${incident.summary}`
          .toLowerCase()
          .includes(
            search.toLowerCase()
          );

      const matchesSeverity =
        severity === "all" ||
        incident.severity ===
          severity;

      return (
        matchesSearch &&
        matchesSeverity
      );
    });

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow blue">
            <History size={14} />
            KNOWLEDGE BASE
          </div>

          <h1>
            Incident history
          </h1>

          <p>
            Investigate previous
            incidents and identify
            recurring operational
            patterns.
          </p>
        </div>
      </div>

      <div className="panel">
        <div className="filters">
          <div className="search-field">
            <Search size={16} />

            <input
              placeholder="Search incidents or services…"
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value
                )
              }
            />
          </div>

          <select
            value={severity}
            onChange={(event) =>
              setSeverity(
                event.target.value
              )
            }
          >
            <option value="all">
              All severity
            </option>
            <option value="critical">
              Critical
            </option>
            <option value="high">
              High
            </option>
            <option value="medium">
              Medium
            </option>
            <option value="low">
              Low
            </option>
          </select>

          <span className="filter-count">
            {filtered.length} incidents
          </span>
        </div>

        <div className="table history-table">
          <div className="table-head">
            <span>ID</span>
            <span>SERVICE</span>
            <span>SEVERITY</span>
            <span>IMPACT</span>
            <span>CONFIDENCE</span>
            <span>CREATED</span>
            <span>ACTION</span>
          </div>

          {filtered.map(
            (incident) => (
              <button
                className="table-row"
                key={incident.id}
                onClick={() =>
                  onSelect(incident)
                }
              >
                <span className="mono muted">
                  #{incident.id}
                </span>

                <span>
                  <strong>
                    {incident.service}
                  </strong>

                  <small>
                    {incident.summary}
                  </small>
                </span>

                <span>
                  <SeverityBadge
                    severity={
                      incident.severity
                    }
                  />
                </span>

                <span className="impact">
                  <i
                    className={`impact-line ${incident.impact}`}
                  />
                  {incident.impact.toUpperCase()}
                </span>

                <span>
                  <Confidence
                    value={
                      incident.confidence
                    }
                  />
                </span>

                <span className="muted">
                  {incident.created_at}
                </span>

                <span className="investigate">
                  Investigate
                  <ArrowRight
                    size={14}
                  />
                </span>
              </button>
            )
          )}
        </div>
      </div>
    </section>
  );
}

function Services({
  services,
}: {
  services: ServiceSummary[];
}) {
  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow blue">
            <Server size={14} />
            INFRASTRUCTURE
          </div>

          <h1>Services</h1>

          <p>
            Health state derived from
            recorded incident activity.
          </p>
        </div>
      </div>

      <div className="panel service-table">
        <div className="table-head">
          <span>SERVICE</span>
          <span>STATUS</span>
          <span>INCIDENTS</span>
          <span>LAST INCIDENT</span>
          <span>WORST SEVERITY</span>
        </div>

        {services.map((service) => (
          <div
            className="table-row static"
            key={service.name}
          >
            <span>
              <strong className="mono">
                {service.name}
              </strong>
            </span>

            <span>
              <span
                className={`health ${service.status}`}
              >
                <span />
                {service.status ===
                "incident"
                  ? "Incident"
                  : "Healthy"}
              </span>
            </span>

            <span>
              {service.incidents}
            </span>

            <span className="muted">
              {service.lastIncident}
            </span>

            <span>
              <SeverityBadge
                severity={
                  service.worstSeverity
                }
              />
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function IncidentDrawer({
  incident,
  onClose,
}: {
  incident: Incident;
  onClose: () => void;
}) {
  return (
    <div
      className="drawer-backdrop"
      onClick={onClose}
    >
      <aside
        className="drawer"
        onClick={(event) =>
          event.stopPropagation()
        }
      >
        <div className="drawer-head">
          <div>
            <span className="mono muted">
              INCIDENT #{incident.id}
            </span>

            <h2>
              {incident.service}
            </h2>
          </div>

          <button
            className="icon-button"
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <div className="drawer-summary">
          <SeverityBadge
            severity={incident.severity}
          />

          <span className="impact">
            <i
              className={`impact-line ${incident.impact}`}
            />
            {incident.impact.toUpperCase()}{" "}
            IMPACT
          </span>

          <Confidence
            value={incident.confidence}
          />
        </div>

        <div className="drawer-section">
          <label>
            INCIDENT SUMMARY
          </label>

          <h3>
            {incident.summary}
          </h3>

          <p>
            {incident.root_cause ||
              "Evidence-backed incident analysis is available for this event."}
          </p>
        </div>

        <div className="drawer-section">
          <label>EVIDENCE</label>

          <div className="evidence-item">
            <FileSearch size={15} />

            <span>
              Observed infrastructure
              and application signals
            </span>

            <CheckCircle2 size={15} />
          </div>

          <div className="evidence-item">
            <Cpu size={15} />

            <span>
              Runtime metrics evaluated
              deterministically
            </span>

            <CheckCircle2 size={15} />
          </div>

          <div className="evidence-item">
            <Bot size={15} />

            <span>
              AI inference reconciled
              against evidence
            </span>

            <CheckCircle2 size={15} />
          </div>
        </div>

        <button className="primary-button full">
          <Sparkles size={16} />
          Open full RCA
        </button>
      </aside>
    </div>
  );
}

function CommandPalette({
  onClose,
  onNavigate,
}: {
  onClose: () => void;
  onNavigate: (page: Page) => void;
}) {
  const commands: Array<
    [
      string,
      Page,
      typeof LayoutDashboard
    ]
  > = [
    [
      "Overview",
      "overview",
      LayoutDashboard,
    ],
    [
      "Analyze incident",
      "analyze",
      Sparkles,
    ],
    [
      "Incident history",
      "incidents",
      History,
    ],
    [
      "Services",
      "services",
      Server,
    ],
  ];

  return (
    <div
      className="command-backdrop"
      onClick={onClose}
    >
      <div
        className="command"
        onClick={(event) =>
          event.stopPropagation()
        }
      >
        <div className="command-search">
          <Search size={18} />

          <input
            autoFocus
            placeholder="Jump to…"
          />
        </div>

        {commands.map(
          ([
            name,
            page,
            Icon,
          ]) => (
            <button
              key={page}
              onClick={() => {
                onNavigate(page);
                onClose();
              }}
            >
              <Icon size={17} />

              <span>{name}</span>

              <kbd>↵</kbd>
            </button>
          )
        )}

        <div className="command-foot">
          <Command size={13} />
          Keyboard navigation
        </div>
      </div>
    </div>
  );
}

export default App;
