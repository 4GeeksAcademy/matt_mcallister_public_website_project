
"use client";
import React, { useState } from 'react';
import {
  addNote,
  deleteNote,
  getCandidate,
  getNotes,
  patchCandidate,
} from '@/lib/candidates';
import Link from 'next/link';
import type {
  CandidateStage,
  CandidateStatus,
  NoteOut,
  RecordOut,
} from '@/types';
import styles from './page.module.css';

interface CandidateDetailPageProps {
  params: Promise<{ id: string }>;
}

const statuses: CandidateStatus[] = ['received', 'in_progress', 'selected', 'discarded'];
const stages: CandidateStage[] = [
  'pending',
  'review',
  'personal_interview',
  'technical_interview',
  'offer_presented',
];

function label(value: string): string {
  return value.replaceAll('_', ' ');
}

export default function CandidateDetailPage({ params }: CandidateDetailPageProps) {
  const [notes, setNotes] = useState<NoteOut[]>([]);
  const [noteInput, setNoteInput] = useState('');
  const [candidate, setCandidate] = useState<RecordOut | null>(null);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');
  const [saving, setSaving] = useState(false);

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
      try {
        const created = await addNote(candidate.id, { content });
        setNotes((prev) => [created, ...prev]);
        setCandidate((prev) =>
          prev ? { ...prev, notes_count: prev.notes_count + 1 } : prev
        );
        setNoteInput('');
      } catch (reason) {
        setFeedback(reason instanceof Error ? reason.message : String(reason));
      }
    }
  }

  async function handleDeleteNote(noteId: string) {
    if (!candidate) return;
    try {
      await deleteNote(candidate.id, noteId);
      setNotes((prev) => prev.filter((note) => note.id !== noteId));
      setCandidate((prev) =>
        prev ? { ...prev, notes_count: Math.max(0, prev.notes_count - 1) } : prev
      );
    } catch (reason) {
      setFeedback(reason instanceof Error ? reason.message : String(reason));
    }
  }

  async function updatePipeline(change: {
    status?: CandidateStatus;
    stage?: CandidateStage;
  }) {
    if (!candidate) return;
    setSaving(true);
    setFeedback('');
    try {
      const updated = await patchCandidate(candidate.id, change);
      setCandidate(updated);
      setFeedback('Candidate pipeline updated.');
    } catch (reason) {
      setFeedback(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setSaving(false);
    }
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
          <select
            aria-label="Update candidate status"
            value={candidate.status}
            disabled={saving}
            onChange={(event) =>
              void updatePipeline({ status: event.target.value as CandidateStatus })
            }
          >
            {statuses.map((status) => <option key={status} value={status}>{label(status)}</option>)}
          </select>
        </article>
        <article>
          <span>Stage</span>
          <select
            aria-label="Update candidate stage"
            value={candidate.stage}
            disabled={saving}
            onChange={(event) =>
              void updatePipeline({ stage: event.target.value as CandidateStage })
            }
          >
            {stages.map((stage) => <option key={stage} value={stage}>{label(stage)}</option>)}
          </select>
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
          <div className={styles.detailItem}>
            <span className={styles.label}>Experience</span>
            <span className={styles.value}>{candidate.experience_years} years</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.label}>LinkedIn</span>
            <span className={styles.value}>
              {candidate.linkedin_url ? (
                <a href={candidate.linkedin_url} target="_blank" rel="noreferrer">View profile</a>
              ) : 'Not provided'}
            </span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.label}>CV</span>
            <span className={styles.value}>
              {candidate.cv_url ? (
                <a href={candidate.cv_url} target="_blank" rel="noreferrer">Open CV</a>
              ) : 'Not provided'}
            </span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.label}>Applied</span>
            <span className={styles.value}>
              {new Date(candidate.applied_at).toLocaleDateString()}
            </span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.label}>Notes</span>
            <span className={styles.value}>{candidate.notes_count}</span>
          </div>
        </div>
        <div className={styles.actions}>
          <Link href="/" className={styles.secondaryCta}>
            Back to Directory
          </Link>
          <Link href={`/candidates/${candidate.id}/edit`} className={styles.primaryCta}>
            Edit Candidate
          </Link>
        </div>
        {feedback ? <p className={styles.feedback} role="status">{feedback}</p> : null}
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
