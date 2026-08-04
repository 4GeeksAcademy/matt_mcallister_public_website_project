import { apiFetch } from './api';
import type {
  RecordOut,
  RecordCreate,
  RecordPatch,
  NoteCreate,
  GetRecordsParams,
} from '../types';

// ─── Records ──────────────────────────────────────────────────────────────────

/**
 * GET /records
 * Supports filtering by status, stage, search query, and pagination.
 */
export async function getCandidates(
  params: GetRecordsParams = {}
): Promise<RecordOut[]> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.stage) query.set('stage', params.stage);
  if (params.search) query.set('search', params.search);
  if (params.page) query.set('page', String(params.page));
  if (params.limit) query.set('limit', String(params.limit));

  const qs = query.toString() ? `?${query.toString()}` : '';
  return apiFetch<RecordOut[]>(`/records${qs}`);
}

/**
 * GET /records/:id
 */
export async function getCandidate(id: string): Promise<RecordOut> {
  return apiFetch<RecordOut>(`/records/${id}`);
}

/**
 * POST /records
 * Required fields: full_name, email, phone, position, experience_years
 */
export async function createCandidate(body: RecordCreate): Promise<RecordOut> {
  return apiFetch<RecordOut>('/records', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * PUT /records/:id
 * Full replacement — send all fields.
 */
export async function replaceCandidate(
  id: string,
  body: RecordCreate
): Promise<RecordOut> {
  return apiFetch<RecordOut>(`/records/${id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

/**
 * PATCH /records/:id
 * Partial update — only status and/or stage.
 */
export async function patchCandidate(
  id: string,
  body: RecordPatch
): Promise<RecordOut> {
  return apiFetch<RecordOut>(`/records/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

/**
 * DELETE /records/:id
 * Returns 204 No Content on success.
 */
export async function deleteCandidate(id: string): Promise<void> {
  return apiFetch<void>(`/records/${id}`, { method: 'DELETE' });
}

// ─── Notes ────────────────────────────────────────────────────────────────────

/**
 * GET /records/:id/notes
 */
export async function getNotes(candidateId: string): Promise<unknown[]> {
  return apiFetch<unknown[]>(`/records/${candidateId}/notes`);
}

/**
 * POST /records/:id/notes
 * Body: { content: string } — minLength 1
 */
export async function addNote(
  candidateId: string,
  body: NoteCreate
): Promise<unknown> {
  return apiFetch<unknown>(`/records/${candidateId}/notes`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * DELETE /records/:id/notes/:note_id
 * Returns 204 No Content on success.
 */
export async function deleteNote(
  candidateId: string,
  noteId: string
): Promise<void> {
  return apiFetch<void>(`/records/${candidateId}/notes/${noteId}`, {
    method: 'DELETE',
  });
}
