/** Base URL for the TrackFlow incidents FastAPI service. */
export const incidentsApiBase = (
  process.env.NEXT_PUBLIC_INCIDENTS_API_URL || "http://localhost:8001"
).replace(/\/$/, "");

export const incidentsUrl = (path: string): string => {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${incidentsApiBase}${normalized}`;
};
