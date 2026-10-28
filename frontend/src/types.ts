export type Severity = "critical" | "high" | "medium" | "low";
export type Impact = "critical" | "high" | "medium" | "low";

export type Incident = {
  id: number | string;
  service: string;
  summary: string;
  severity: Severity;
  impact: Impact;
  confidence: number;
  created_at?: string;
  status?: string;
  root_cause?: string;
};

export type AnalysisResult = {
  incident?: {
    service?: string;
    container?: string | null;
    image?: string | null;
  };
  severity: Severity;
  confidence: number;
  impact: Impact;
  signals: string[];
  timeline: string[];
  root_cause: { statement: string; confidence: number };
  evidence: Array<Record<string, unknown> | string>;
  alternative_hypotheses: string[];
  recommendations: string[];
};

export type ServiceSummary = {
  name: string;
  status: "healthy" | "incident";
  incidents: number;
  lastIncident: string;
  worstSeverity: Severity;
};
