'use client';

import { useState } from 'react';
import Link from 'next/link';
import { createCandidate } from '../../../candidates';
import { useRouter } from 'next/navigation';

import styles from './page.module.css';

export default function NewCandidatePage() {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    position: '',
    experience_years: 0,
  });
  const [error, setError] = useState('');
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      await createCandidate(form);
      router.push('/candidates');
    } catch (err: any) {
      setError(err.message);
    }
  }

  const completion = [
    form.full_name,
    form.email,
    form.phone,
    form.position,
    String(form.experience_years || ''),
  ].filter((value) => value.trim().length > 0).length;

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <p className={styles.kicker}>Talent Pipeline</p>
        <h1>Add Candidate Profile</h1>
        <p className={styles.subtitle}>
          Capture applicant details and push them directly into your hiring workflow.
        </p>
        <div className={styles.heroActions}>
          <Link href="/candidates" className={styles.secondaryCta}>
            Back to Directory
          </Link>
          <Link href="/" className={styles.ghostCta}>
            Open Dashboard
          </Link>
        </div>
      </section>

      <section className={styles.stats}>
        <article>
          <span>Required Fields</span>
          <strong>5</strong>
        </article>
        <article>
          <span>Completed</span>
          <strong>{completion}</strong>
        </article>
        <article>
          <span>Remaining</span>
          <strong>{Math.max(0, 5 - completion)}</strong>
        </article>
      </section>

      <section className={styles.formBlock}>
        <div className={styles.blockHeader}>
          <h2>Candidate Information</h2>
          <p>All fields are required before creating a profile.</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label>
            Full Name
            <input
              placeholder="e.g. Maria Rodriguez"
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              required
            />
          </label>

          <label>
            Email
            <input
              type="email"
              placeholder="name@company.com"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              required
            />
          </label>

          <label>
            Phone
            <input
              placeholder="+1 555 010 200"
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              required
            />
          </label>

          <label>
            Position
            <input
              placeholder="Frontend Engineer"
              value={form.position}
              onChange={(e) => setForm((f) => ({ ...f, position: e.target.value }))}
              required
            />
          </label>

          <label>
            Experience (Years)
            <input
              type="number"
              min={0}
              placeholder="0"
              value={form.experience_years}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  experience_years: Number(e.target.value),
                }))
              }
              required
            />
          </label>

          <div className={styles.actions}>
            <button type="submit" className={styles.primaryCta}>
              Create Candidate
            </button>
          </div>

          {error && <p className={styles.error}>{error}</p>}
        </form>
      </section>
    </main>
  );
}
