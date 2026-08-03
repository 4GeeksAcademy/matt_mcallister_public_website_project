
"use client";
import React, { useState } from 'react';
import {
  addNote,
  deleteNote,
  getCandidate,
  getNotes,
} from '../../../candidates';
import Link from 'next/link';
import type { NoteOut, RecordOut } from '../../../types';
import styles from './page.module.css';

export const dynamic = 'force-dynamic';

interface CandidateDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CandidateDetailPage({ params }: CandidateDetailPageProps) {
  const [notes, setNotes] = useState<NoteOut[]>([]);
  const [noteInput, setNoteInput] = useState('');
  const [candidate, setCandidate] = useState<RecordOut | null>(null);
  const [error, setError] = useState('');

  React.useEffect(() => {
    params.then(({ id }) => {
      Promise.all([getCandidate(id), getNotes(id)])
        .then(([nextCandidate, nextNotes]) => {
          setCandidate(nextCandidate);
          setNotes(nextNotes);
        })
        .catch((e) => setError(String(e)));
    });
  }, [params]);

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    const content = noteInput.trim();
    if (content && candidate) {
      const created = await addNote(candidate.id, { content });
      setNotes((prev) => [created, ...prev]);
      setCandidate((prev) =>
        prev ? { ...prev, notes_count: prev.notes_count + 1 } : prev
      );
      setNoteInput('');
    }
  }

  async function handleDeleteNote(noteId: string) {
    if (!candidate) return;
    await deleteNote(candidate.id, noteId);
    setNotes((prev) => prev.filter((note) => note.id !== noteId));
    setCandidate((prev) =>
      prev ? { ...prev, notes_count: Math.max(0, prev.notes_count - 1) } : prev
    );
  }

  if (error) {
    return <main className={styles.shell}>Error loading candidate: {error}</main>;
  }
  if (!candidate) {
    return <main className={styles.shell}>Loading...</main>;
  }

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <p className={styles.kicker}>Talent Pipeline</p>
        <h1>{candidate.full_name}</h1>
        <p className={styles.subtitle}>Candidate profile and application details</p>
      </section>

      <section className={styles.stats}>
        <article>
          <span>Status</span>
          <strong>{candidate.status.replace('_', ' ')}</strong>
        </article>
        <article>
          <span>Stage</span>
          <strong>{candidate.stage.replace('_', ' ')}</strong>
        </article>
        <article>
          <span>Experience</span>
          <strong>{candidate.experience_years} years</strong>
        </article>
      </section>

      <section className={styles.profileBlock}>
        <div className={styles.blockHeader}>
          <h2>Contact & Role Info</h2>
          <p>Key details for this applicant</p>
        </div>
        <div className={styles.details}>
          <div className={styles.detailItem}>
            <span className={styles.label}>Email</span>
            <span className={styles.value}>{candidate.email}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.label}>Phone</span>
            <span className={styles.value}>{candidate.phone}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.label}>Position</span>
            <span className={styles.value}>{candidate.position}</span>
          </div>
        </div>
        <div className={styles.actions}>
          <Link href="/candidates" className={styles.secondaryCta}>
            Back to Directory
          </Link>
        </div>
      </section>

      <section className={styles.profileBlock}>
        <div className={styles.blockHeader}>
          <h2>Internal Notes</h2>
          <p>Add private notes for this candidate. Only visible to your team.</p>
        </div>
        <form onSubmit={handleAddNote} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <input
            type="text"
            placeholder="Add a note..."
            value={noteInput}
            onChange={e => setNoteInput(e.target.value)}
            style={{ flex: 1, borderRadius: 8, border: '1px solid #d1d5db', padding: '0.5rem' }}
          />
          <button type="submit" className={styles.primaryCta} style={{ minWidth: 90 }}>
            Add
          </button>
        </form>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {notes.length === 0 && <li style={{ color: '#64748b' }}>No notes yet.</li>}
          {notes.map((note) => (
            <li key={note.id} style={{ display: 'flex', alignItems: 'center', marginBottom: 8, background: '#f8fafc', borderRadius: 8, padding: '0.5rem 0.8rem' }}>
              <span style={{ flex: 1 }}>{note.content}</span>
              <button
                type="button"
                onClick={() => void handleDeleteNote(note.id)}
                style={{ marginLeft: 8, background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 6, padding: '0.2rem 0.7rem', cursor: 'pointer' }}
                aria-label="Delete note"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
