'use client';

import { FormEvent, useState } from 'react';

import type { RecordCreate } from '@/types';
import styles from '@/app/candidates/new/page.module.css';

interface CandidateFormProps {
  initialValue?: RecordCreate;
  submitLabel: string;
  onSubmit: (candidate: RecordCreate) => Promise<void>;
}

const emptyCandidate: RecordCreate = {
  full_name: '',
  email: '',
  phone: '',
  position: '',
  experience_years: 0,
  linkedin_url: null,
  cv_url: null,
};

export default function CandidateForm({
  initialValue = emptyCandidate,
  submitLabel,
  onSubmit,
}: CandidateFormProps) {
  const [form, setForm] = useState<RecordCreate>(initialValue);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (
      !form.full_name.trim() ||
      !form.email.trim() ||
      !form.phone.trim() ||
      !form.position.trim() ||
      form.experience_years < 0
    ) {
      setError('Complete all required fields before submitting.');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        ...form,
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        position: form.position.trim(),
        linkedin_url: form.linkedin_url?.trim() || null,
        cv_url: form.cv_url?.trim() || null,
      });
      setSuccess('Candidate saved successfully.');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <label>
        Full Name *
        <input
          value={form.full_name}
          onChange={(event) => setForm({ ...form, full_name: event.target.value })}
          required
        />
      </label>
      <label>
        Email *
        <input
          type="email"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          required
        />
      </label>
      <label>
        Phone *
        <input
          value={form.phone}
          onChange={(event) => setForm({ ...form, phone: event.target.value })}
          required
        />
      </label>
      <label>
        Position *
        <input
          value={form.position}
          onChange={(event) => setForm({ ...form, position: event.target.value })}
          required
        />
      </label>
      <label>
        Experience (Years) *
        <input
          type="number"
          min={0}
          max={80}
          value={form.experience_years}
          onChange={(event) =>
            setForm({ ...form, experience_years: Number(event.target.value) })
          }
          required
        />
      </label>
      <label>
        LinkedIn URL
        <input
          type="url"
          placeholder="https://linkedin.com/in/..."
          value={form.linkedin_url ?? ''}
          onChange={(event) => setForm({ ...form, linkedin_url: event.target.value })}
        />
      </label>
      <label>
        CV URL
        <input
          type="url"
          placeholder="https://example.com/cv.pdf"
          value={form.cv_url ?? ''}
          onChange={(event) => setForm({ ...form, cv_url: event.target.value })}
        />
      </label>

      <div className={styles.actions}>
        <button type="submit" className={styles.primaryCta} disabled={submitting}>
          {submitting ? 'Saving…' : submitLabel}
        </button>
      </div>
      {error ? <p className={styles.error} role="alert">{error}</p> : null}
      {success ? <p className={styles.success} role="status">{success}</p> : null}
    </form>
  );
}
