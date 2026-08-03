import fs from "node:fs";
import path from "node:path";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  Incident,
  IncidentCreateInput,
  IncidentFilters,
  IncidentStatus,
  IncidentSummary,
  isValidLifecycleTransition,
} from "../../../packages/shared/types";

const DATA_DIR = path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "incidents.json");

type ApiFieldError = {
  field: string;
  message: string;
};

type ValidationResult<T> = {
  data?: T;
  errors: ApiFieldError[];
};

const nowIso = (): string => new Date().toISOString();

const ensureStore = (): void => {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(DATA_FILE, "[]\n", "utf8");
  }
};

const readStore = (): Incident[] => {
  ensureStore();

  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    const parsed = JSON.parse(raw);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed as Incident[];
  } catch {
    return [];
  }
};

const writeStore = (incidents: Incident[]): void => {
  ensureStore();
  fs.writeFileSync(DATA_FILE, `${JSON.stringify(incidents, null, 2)}\n`, "utf8");
};

const generateId = (): string => {
  return `inc_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
};

const isEnumValue = (value: string, allowed: readonly string[]): boolean => {
  return allowed.includes(value);
};

const asText = (value: unknown): string => {
  return typeof value === "string" ? value.trim() : "";
};

export const validateCreateInput = (payload: unknown): ValidationResult<IncidentCreateInput> => {
  const errors: ApiFieldError[] = [];

  if (!payload || typeof payload !== "object") {
    return {
      errors: [{ field: "body", message: "Request body must be a JSON object." }],
    };
  }

  const body = payload as Record<string, unknown>;
  const title = asText(body.title);
  const description = asText(body.description);
  const category = asText(body.category);
  const status = asText(body.status);
  const origin = asText(body.origin);
  const branch = asText(body.branch);

  if (!title) {
    errors.push({ field: "title", message: "Title is required." });
  }

  if (!description) {
    errors.push({ field: "description", message: "Description is required." });
  }

  if (!category) {
    errors.push({ field: "category", message: "Category is required." });
  } else if (!isEnumValue(category, INCIDENT_CATEGORIES)) {
    errors.push({ field: "category", message: "Category value is not allowed." });
  }

  if (!status) {
    errors.push({ field: "status", message: "Status is required." });
  } else if (!isEnumValue(status, INCIDENT_STATUSES)) {
    errors.push({ field: "status", message: "Status value is not allowed." });
  }

  if (!origin) {
    errors.push({ field: "origin", message: "Origin is required." });
  } else if (!isEnumValue(origin, INCIDENT_ORIGINS)) {
    errors.push({ field: "origin", message: "Origin value is not allowed." });
  }

  if (!branch) {
    errors.push({ field: "branch", message: "Branch is required." });
  } else if (!isEnumValue(branch, INCIDENT_BRANCHES)) {
    errors.push({ field: "branch", message: "Branch value is not allowed." });
  }

  if (errors.length > 0) {
    return { errors };
  }

  return {
    data: {
      title,
      description,
      category: category as IncidentCreateInput["category"],
      status: status as IncidentCreateInput["status"],
      origin: origin as IncidentCreateInput["origin"],
      branch: branch as IncidentCreateInput["branch"],
    },
    errors,
  };
};

export const validateStatusPatch = (payload: unknown): ValidationResult<{ status: IncidentStatus }> => {
  const errors: ApiFieldError[] = [];

  if (!payload || typeof payload !== "object") {
    return {
      errors: [{ field: "body", message: "Request body must be a JSON object." }],
    };
  }

  const nextStatus = asText((payload as Record<string, unknown>).status);

  if (!nextStatus) {
    errors.push({ field: "status", message: "Status is required." });
  } else if (!isEnumValue(nextStatus, INCIDENT_STATUSES)) {
    errors.push({ field: "status", message: "Status value is not allowed." });
  }

  if (errors.length > 0) {
    return { errors };
  }

  return {
    data: { status: nextStatus as IncidentStatus },
    errors,
  };
};

export const createIncident = (input: IncidentCreateInput): Incident => {
  const incidents = readStore();
  const timestamp = nowIso();

  const incident: Incident = {
    id: generateId(),
    title: input.title,
    description: input.description,
    category: input.category,
    status: input.status,
    origin: input.origin,
    branch: input.branch,
    created_at: timestamp,
    updated_at: timestamp,
  };

  incidents.unshift(incident);
  writeStore(incidents);

  return incident;
};

export const listIncidents = (filters: IncidentFilters = {}): Incident[] => {
  const incidents = readStore();

  return incidents.filter((incident) => {
    if (filters.status && incident.status !== filters.status) {
      return false;
    }

    if (filters.origin && incident.origin !== filters.origin) {
      return false;
    }

    if (filters.branch && incident.branch !== filters.branch) {
      return false;
    }

    if (filters.category && incident.category !== filters.category) {
      return false;
    }

    return true;
  });
};

export const getIncidentById = (id: string): Incident | null => {
  const incidents = readStore();
  return incidents.find((incident) => incident.id === id) ?? null;
};

export const updateIncidentStatus = (
  id: string,
  nextStatus: IncidentStatus,
): { incident?: Incident; error?: ApiFieldError } => {
  const incidents = readStore();
  const targetIndex = incidents.findIndex((incident) => incident.id === id);

  if (targetIndex === -1) {
    return;
  }

  const current = incidents[targetIndex];

  if (!isValidLifecycleTransition(current.status, nextStatus)) {
    return {
      error: {
        field: "status",
        message: `Cannot move incident from ${current.status} to ${nextStatus}.`,
      },
    };
  }

  const updated: Incident = {
    ...current,
    status: nextStatus,
    updated_at: nowIso(),
  };

  incidents[targetIndex] = updated;
  writeStore(incidents);

  return { incident: updated };
};

export const buildIncidentSummary = (): IncidentSummary => {
  const incidents = readStore();

  const by_status: Record<string, number> = Object.fromEntries(
    INCIDENT_STATUSES.map((status) => [status, 0]),
  );
  const by_category: Record<string, number> = Object.fromEntries(
    INCIDENT_CATEGORIES.map((category) => [category, 0]),
  );
  const by_origin: Record<string, number> = Object.fromEntries(
    INCIDENT_ORIGINS.map((origin) => [origin, 0]),
  );
  const by_branch: Record<string, number> = Object.fromEntries(
    INCIDENT_BRANCHES.map((branch) => [branch, 0]),
  );

  for (const incident of incidents) {
    by_status[incident.status] += 1;
    by_category[incident.category] += 1;
    by_origin[incident.origin] += 1;
    by_branch[incident.branch] += 1;
  }

  return {
    by_status,
    by_category,
    by_origin,
    by_branch,
  };
};

export const parseIncidentFilters = (
  searchParams: URLSearchParams,
): { filters?: IncidentFilters; errors: ApiFieldError[] } => {
  const filters: IncidentFilters = {};
  const errors: ApiFieldError[] = [];

  const status = asText(searchParams.get("status"));
  const origin = asText(searchParams.get("origin"));
  const branch = asText(searchParams.get("branch"));
  const category = asText(searchParams.get("category"));

  if (status) {
    if (!isEnumValue(status, INCIDENT_STATUSES)) {
      errors.push({ field: "status", message: "Invalid status filter value." });
    } else {
      filters.status = status as IncidentFilters["status"];
    }
  }

  if (origin) {
    if (!isEnumValue(origin, INCIDENT_ORIGINS)) {
      errors.push({ field: "origin", message: "Invalid origin filter value." });
    } else {
      filters.origin = origin as IncidentFilters["origin"];
    }
  }

  if (branch) {
    if (!isEnumValue(branch, INCIDENT_BRANCHES)) {
      errors.push({ field: "branch", message: "Invalid branch filter value." });
    } else {
      filters.branch = branch as IncidentFilters["branch"];
    }
  }

  if (category) {
    if (!isEnumValue(category, INCIDENT_CATEGORIES)) {
      errors.push({ field: "category", message: "Invalid category filter value." });
    } else {
      filters.category = category as IncidentFilters["category"];
    }
  }

  if (errors.length > 0) {
    return { errors };
  }

  return { filters, errors };
};

export const getApiErrorBody = (error: ApiFieldError, message = "Validation failed") => {
  return {
    message,
    error,
  };
};
