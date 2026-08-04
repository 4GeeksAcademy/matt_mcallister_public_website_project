# Talent Tracker — Frontend Project Specification

## Overview

Build a frontend application for a company's **People & Talent Agency**. The interface allows recruiters to manage candidate pipelines end-to-end: browsing candidates, filtering and searching, viewing full profiles, updating statuses and stages, managing internal notes, and registering or editing candidate data — all without full page reloads and with robust async handling throughout.

---

## REST API

**Base URL:** `/tracker/api/v1`

### Records

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/records` | List all candidates (supports filtering & pagination) |
| `POST` | `/records` | Create a new candidate record |
| `GET` | `/records/:id` | Get a single candidate by ID |
| `PUT` | `/records/:id` | Replace (full update) a candidate record |
| `PATCH` | `/records/:id` | Partial update — status and/or stage only |
| `DELETE` | `/records/:id` | Delete a candidate record |

#### `GET /records` — Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `status` | `string` | Filter by: `received`, `in_progress`, `selected`, `discarded` |
| `stage` | `string` | Filter by: `pending`, `review`, `personal_interview`, `technical_interview`, `offer_presented` |
| `search` | `string` | Search by `full_name` or `email` |
| `page` | `integer` | Page number (default: `1`, min: `1`) |
| `limit` | `integer` | Results per page (default: `20`, min: `1`, max: `100`) |

### Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/records/:id/notes` | Get all notes for a candidate |
| `POST` | `/records/:id/notes` | Add a new note to a candidate |
| `DELETE` | `/records/:id/notes/:note_id` | Delete a specific note |

---

## Data Schemas

### `RecordCreate` (POST / PUT body)

```ts
{
  full_name: string;        // required
  email: string;            // required, email format
  phone: string;            // required
  position: string;         // required
  experience_years: number; // required
  linkedin_url?: string | null;
  cv_url?: string | null;
}
```

### `RecordOut` (API response)

```ts
{
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url: string | null;
  cv_url: string | null;
  status: string;
  stage: string;
  experience_years: number;
  notes_count: number;
  applied_at: string;
  updated_at: string;
}
```

### `RecordPatch` (PATCH body)

```ts
{
  status?: string | null;
  stage?: string | null;
}
```

### `NoteCreate` (POST body)

```ts
{
  content: string; // required, minLength: 1
}
```

---

## Views & Routing

### `/` — Candidate List Page

- Fetches all candidates from `GET /records`
- Displays each candidate's: **full name**, **position**, **status**, **stage**
- Filters by **status** and **stage** via `useSearchParams` (query parameters — no page reload)
- **Search input** filtering by name or email — no reload
- Loading state while fetching; error message if request fails

### `/candidates/[id]` — Candidate Detail Page

- Fetches candidate from `GET /records/:id`
- Displays all fields: name, email, phone, position, LinkedIn, CV link, experience years, status, stage, application date
- Control to **update status** via `PATCH /records/:id`
- Control to **update stage** via `PATCH /records/:id`
- Notes section fetched from `GET /records/:id/notes`
  - Add a new note via `POST /records/:id/notes`
  - Delete a note via `DELETE /records/:id/notes/:note_id`

Navigation between list and detail uses **Next.js routing** — no full page reloads.

---

## Candidate Management

### New Candidate Form

- Accessible from the candidate list view
- Submits via `POST /records`
- Required field validation before submission
- Success and error feedback after submission

### Edit Candidate Form

- Accessible from the candidate detail view
- Submits via `PUT /records/:id`
- Pre-populated with existing candidate data
- Required field validation before submission
- Success and error feedback after submission

---

## State & Async Handling

- All API calls use `async/await`
- Every data-fetching operation exposes **three UI states**: `loading`, `success`, `error`
- After a `PATCH`, `PUT`, or `POST`, update the UI to reflect changes **without a full page reload**

---

## Code Structure

```
/components      # Reusable UI components
/hooks           # Custom React hooks (e.g., useCandidates, useNotes)
/types           # TypeScript types for all API data structures
/lib             # or /services — API client functions, fetch wrappers
```

### TypeScript Types

Define TypeScript interfaces for all data structures received from the API. Minimum required types:

```ts
// types/index.ts

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
```

---

## Acceptance Criteria Checklist

### Views and Routing
- [ ] Candidate list page (`/`) displays all candidates from `GET /records`
- [ ] Candidate detail page (`/candidates/[id]`) fetches from `GET /records/:id`
- [ ] Navigation uses Next.js routing — no full page reloads

### Candidate List
- [ ] Displays full name, position, current status, current stage
- [ ] Filter by status and stage via `useSearchParams`
- [ ] Search input filters by name or email without reloading
- [ ] Loading state shown while fetching
- [ ] Error message shown if request fails

### Candidate Detail
- [ ] Displays all fields: name, email, phone, position, LinkedIn, CV, experience, status, stage, application date
- [ ] Control to update status via `PATCH /records/:id`
- [ ] Control to update stage via `PATCH /records/:id`
- [ ] Notes list fetched from `GET /records/:id/notes`
- [ ] Add note via `POST /records/:id/notes`
- [ ] Delete note via `DELETE /records/:id/notes/:note_id`

### Candidate Management
- [ ] Form to register a new candidate (`POST /records`)
- [ ] Form to edit candidate data (`PUT /records/:id`)
- [ ] Both forms validate required fields before submission
- [ ] Success and error feedback shown after each submission

### State & Async Handling
- [ ] All API calls use `async/await`
- [ ] Every fetch has loading, success, and error states
- [ ] UI updates after `PATCH`, `PUT`, `POST` without a full page reload

### Code Structure
- [ ] Folder structure: `/components`, `/hooks`, `/types`, `/lib` or `/services`
- [ ] TypeScript types defined for all API data structures
