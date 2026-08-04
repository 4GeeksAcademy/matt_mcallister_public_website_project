'use client';

import Link from 'next/link';
import { createCandidate } from '@/lib/candidates';
import { useRouter } from 'next/navigation';
import CandidateForm from '@/components/CandidateForm';

import styles from './page.module.css';

export default function NewCandidatePage() {
  const router = useRouter();

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <p className={styles.kicker}>Talent Pipeline</p>
        <h1>Add Candidate Profile</h1>
        <p className={styles.subtitle}>
          Capture applicant details and push them directly into your hiring workflow.
        </p>
        <div className={styles.heroActions}>
          <Link href="/" className={styles.secondaryCta}>
            Back to Directory
          </Link>
        </div>
      </section>

      <section className={styles.formBlock}>
        <div className={styles.blockHeader}>
          <h2>Candidate Information</h2>
          <p>All fields are required before creating a profile.</p>
        </div>

        <CandidateForm
          submitLabel="Create Candidate"
          onSubmit={async (candidate) => {
            const created = await createCandidate(candidate);
            router.push(`/candidates/${created.id}`);
          }}
        />
      </section>
    </main>
  );
}
