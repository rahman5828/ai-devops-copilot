import type { AnalysisResult, Incident, ServiceSummary } from "../types";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function request<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return response.json();
}

function normalizeIncident(raw: any): Incident {
  const rawConfidence = Number(raw.confidence ?? 0);

  return {
    id: raw.id ?? raw.incident_id ?? "—",
    service:
      raw.service ??
      raw.incident?.service ??
      "unknown-service",
    summary:
      raw.summary ??
      raw.title ??
      raw.root_cause?.statement ??
      raw.root_cause ??
      "Incident",
    severity: raw.severity ?? "low",
    impact: raw.impact ?? raw.severity ?? "low",
    confidence:
      rawConfidence <= 1
        ? rawConfidence * 100
        : rawConfidence,
    created_at:
      raw.created_at ??
      raw.createdAt ??
      "recently",
    status: raw.status ?? "open",
    root_cause:
      raw.root_cause?.statement ??
      raw.root_cause,
  };
}

export async function getIncidents(
  params: {
    service?: string;
    severity?: string;
    impact?: string;
  } = {}
): Promise<Incident[]> {
  const query = new URLSearchParams();

  if (params.service) {
    query.set("service", params.service);
  }

  if (params.severity) {
    query.set("severity", params.severity);
  }

  if (params.impact) {
    query.set("impact", params.impact);
  }

  const queryString = query.toString();

  const data = await request<any>(
    `/incidents${queryString ? `?${queryString}` : ""}`
  );

  const items = Array.isArray(data)
    ? data
    : data?.items ??
      data?.incidents ??
      [];

  return items.map(normalizeIncident);
}

export async function getIncident(
  incidentId: number | string
): Promise<Incident> {
  const data = await request<any>(
    `/incidents/${incidentId}`
  );

  return normalizeIncident(data);
}

export async function analyzeIncident(
  payload: {
    service: string;
    logs: string;
    cpu: number;
    memory: number;
  }
): Promise<AnalysisResult> {
  return request<AnalysisResult>(
    "/analyze/incident",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function deriveServices(
  incidents: Incident[]
): ServiceSummary[] {
  const map = new Map<string, ServiceSummary>();

  const rank: Record<string, number> = {
    low: 0,
    medium: 1,
    high: 2,
    critical: 3,
  };

  for (const incident of incidents) {
    const current = map.get(incident.service);

    const active =
      incident.status === "open" ||
      incident.status === "monitoring";

    if (!current) {
      map.set(incident.service, {
        name: incident.service,
        status: active ? "incident" : "healthy",
        incidents: 1,
        lastIncident:
          incident.created_at || "recently",
        worstSeverity: incident.severity,
      });

      continue;
    }

    current.incidents += 1;

    if (active) {
      current.status = "incident";
    }

    if (
      rank[incident.severity] >
      rank[current.worstSeverity]
    ) {
      current.worstSeverity =
        incident.severity;
    }

    if (incident.created_at) {
      current.lastIncident =
        incident.created_at;
    }
  }

  return [...map.values()].sort(
    (a, b) => b.incidents - a.incidents
  );
}
