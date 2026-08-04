'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';

import { getCandidate, replaceCandidate } from '@/lib/candidates';
import CandidateForm from '@/components/CandidateForm';
import type { RecordCreate, RecordOut } from '@/types';

import styles from '../../new/page.module.css';

interface EditCandidatePageProps {
  params: Promise<{ id: string }>;
}

export default function EditCandidatePage({ params }: EditCandidatePageProps) {
  const { id } = use(params);
  const [candidate, setCandidate] = useState<RecordOut | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    void getCandidate(id)
      .then(setCandidate)
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : String(reason))
      );
  }, [id]);

  if (error) {
    return <main className={styles.shell}>Error loading candidate: {error}</main>;
  }

  if (!candidate) {
    return <main className={styles.shell}>Loading candidate…</main>;
  }

  const initialValue: RecordCreate = {
    full_name: candidate.full_name,
    email: candidate.email,
    phone: candidate.phone,
    position: candidate.position,
    experience_years: candidate.experience_years,
    linkedin_url: candidate.linkedin_url,
    cv_url: candidate.cv_url,
  };

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <p className={styles.kicker}>Talent Pipeline</p>
        <h1>Edit {candidate.full_name}</h1>
        <p className={styles.subtitle}>Update the candidate profile using a full PUT request.</p>
        <div className={styles.heroActions}>
          <Link href={`/candidates/${id}`} className={styles.secondaryCta}>
            Back to Profile
          </Link>
        </div>
      </section>

      <section className={styles.formBlock}>
        <div className={styles.blockHeader}>
          <h2>Candidate Information</h2>
          <p>Required fields must remain complete.</p>
        </div>
        <CandidateForm
          initialValue={initialValue}
          submitLabel="Save Changes"
          onSubmit={async (updated) => {
            const saved = await replaceCandidate(id, updated);
            setCandidate(saved);
          }}
        />
      </section>
    </main>
  );
}
