// API client for TrackFlow Talent Tracker
import type { RecordOut, RecordCreate, RecordPatch, Note, NoteCreate } from '../types';

const BASE_URL = 'http://localhost:5000/tracker/api/v1'; // Updated to full URL for backend

export async function fetchCandidates(params?: Record<string, string | number>) {
  const url = new URL(`${BASE_URL}/records`, window.location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, String(v)));
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch candidates');
  return res.json() as Promise<RecordOut[]>;
}

export async function fetchCandidate(id: string) {
  const res = await fetch(`${BASE_URL}/records/${id}`);
  if (!res.ok) throw new Error('Failed to fetch candidate');
  return res.json() as Promise<RecordOut>;
}

export async function createCandidate(data: RecordCreate) {
  const res = await fetch(`${BASE_URL}/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create candidate');
  return res.json() as Promise<RecordOut>;
}

export async function updateCandidate(id: string, data: RecordCreate) {
  const res = await fetch(`${BASE_URL}/records/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update candidate');
  return res.json() as Promise<RecordOut>;
}

export async function patchCandidate(id: string, data: RecordPatch) {
  const res = await fetch(`${BASE_URL}/records/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to patch candidate');
  return res.json() as Promise<RecordOut>;
}

export async function deleteCandidate(id: string) {
  const res = await fetch(`${BASE_URL}/records/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete candidate');
}

export async function fetchNotes(candidateId: string) {
  const res = await fetch(`${BASE_URL}/records/${candidateId}/notes`);
  if (!res.ok) throw new Error('Failed to fetch notes');
  return res.json() as Promise<Note[]>;
}

export async function addNote(candidateId: string, data: NoteCreate) {
  const res = await fetch(`${BASE_URL}/records/${candidateId}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to add note');
  return res.json() as Promise<Note>;
}

export async function deleteNote(candidateId: string, noteId: string) {
  const res = await fetch(`${BASE_URL}/records/${candidateId}/notes/${noteId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete note');
}
