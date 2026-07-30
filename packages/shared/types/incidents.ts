import incidentDomain from "../incident-domain.json";

export const INCIDENT_STATUSES = incidentDomain.statuses as readonly string[];
export const INCIDENT_ORIGINS = incidentDomain.origins as readonly string[];
export const INCIDENT_CATEGORIES = incidentDomain.categories as readonly string[];
export const INCIDENT_BRANCHES = incidentDomain.branches as readonly string[];
export const INCIDENT_BRANCH_LABELS = incidentDomain.branch_labels as Record<string, string>;

export type IncidentStatus = (typeof INCIDENT_STATUSES)[number];
export type IncidentOrigin = (typeof INCIDENT_ORIGINS)[number];
export type IncidentCategory = (typeof INCIDENT_CATEGORIES)[number];
export type IncidentBranch = (typeof INCIDENT_BRANCHES)[number];

export interface Incident {
  id: string;
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
  created_at: string;
  updated_at: string;
}

export interface IncidentSummary {
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_origin: Record<string, number>;
  by_branch: Record<string, number>;
}

export type IncidentFilters = Partial<{
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
  category: IncidentCategory;
}>;

export type IncidentCreateInput = Omit<Incident, "id" | "created_at" | "updated_at">;

const lifecycle = incidentDomain.lifecycle as Record<IncidentStatus, IncidentStatus[]>;

export const isValidLifecycleTransition = (
  currentStatus: IncidentStatus,
  nextStatus: IncidentStatus,
): boolean => {
  return lifecycle[currentStatus]?.includes(nextStatus) ?? false;
};

export const branchLabel = (branch: string): string => {
  return INCIDENT_BRANCH_LABELS[branch] ?? branch;
};
