export type RecordStatus = 'received' | 'in_progress' | 'selected' | 'discarded';

export type RecordStage =
  | 'pending'
  | 'review'
  | 'personal_interview'
  | 'technical_interview'
  | 'offer_presented';

export interface RecordOut {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url: string | null;
  cv_url: string | null;
  status: RecordStatus;
  stage: RecordStage;
  experience_years: number;
  notes_count: number;
  applied_at: string;
  updated_at: string;
}

export interface RecordCreate {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: number;
  linkedin_url?: string | null;
  cv_url?: string | null;
}

export interface RecordPatch {
  status?: RecordStatus | null;
  stage?: RecordStage | null;
}

export interface NoteCreate {
  content: string;
}

export interface Note {
  id: string;
  content: string;
  created_at?: string;
}
