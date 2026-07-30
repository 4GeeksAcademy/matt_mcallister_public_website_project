import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  Incident,
  IncidentCategory,
  IncidentOrigin,
  IncidentStatus,
  IncidentSummary,
  branchLabel,
} from "../../../packages/shared/types";

export type ApiFieldError = {
  field: string;
  message: string;
};

export type ApiResponse<T> = {
  data?: T;
  message?: string;
  error?: ApiFieldError;
};

export const incidentStatuses = INCIDENT_STATUSES as IncidentStatus[];
export const incidentOrigins = INCIDENT_ORIGINS as IncidentOrigin[];
export const incidentCategories = INCIDENT_CATEGORIES as IncidentCategory[];
export const incidentBranches = INCIDENT_BRANCHES as string[];
export { branchLabel };

export const getFriendlyError = (payload: unknown, fallback: string): string => {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const response = payload as ApiResponse<unknown>;

  if (typeof response.message === "string" && response.message.trim()) {
    return response.message;
  }

  return fallback;
};

export const asIncidentList = (payload: unknown): Incident[] => {
  if (!payload || typeof payload !== "object") {
    return [];
  }

  const response = payload as ApiResponse<Incident[]>;

  if (!response.data || !Array.isArray(response.data)) {
    return [];
  }

  return response.data;
};

export const asIncident = (payload: unknown): Incident | null => {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const response = payload as ApiResponse<Incident>;
  return response.data ?? null;
};

export const asSummary = (payload: unknown): IncidentSummary | null => {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const response = payload as ApiResponse<IncidentSummary>;
  return response.data ?? null;
};
