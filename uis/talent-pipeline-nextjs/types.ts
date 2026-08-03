// ─── Enums ────────────────────────────────────────────────────────────────────

export type CandidateStatus =
  | 'received'
  | 'in_progress'
  | 'selected'
  | 'discarded';

export type CandidateStage =
  | 'pending'
  | 'review'
  | 'personal_interview'
  | 'technical_interview'
  | 'offer_presented';

// ─── API Shapes ───────────────────────────────────────────────────────────────

/** Shape returned by GET /records, GET /records/:id, POST, PUT, PATCH */
export interface RecordOut {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url: string | null;
  cv_url: string | null;
  status: CandidateStatus;
  stage: CandidateStage;
  experience_years: number;
  notes_count: number;
  applied_at: string;
  updated_at: string;
}

/** Body for POST /records and PUT /records/:id */
export interface RecordCreate {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: number;
  linkedin_url?: string | null;
  cv_url?: string | null;
}

/** Body for PATCH /records/:id — only status and/or stage */
export interface RecordPatch {
  status?: CandidateStatus | null;
  stage?: CandidateStage | null;
}

/** Body for POST /records/:id/notes */
export interface NoteCreate {
  content: string;
}

// ─── Query Params ─────────────────────────────────────────────────────────────

export interface GetRecordsParams {
  status?: CandidateStatus;
  stage?: CandidateStage;
  search?: string;
  page?: number;
  limit?: number;
}

// ─── UI State Helper ──────────────────────────────────────────────────────────

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface RecordsPageOut {
  total: number;
  page: number;
  limit: number;
  data: RecordOut[];
}
