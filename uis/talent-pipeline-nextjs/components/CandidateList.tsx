'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';

import { getCandidatesPage } from '@/lib/candidates';
import { useCandidateListFilters } from '@/hooks/useCandidateListFilters';
import type {
  CandidateStage,
  CandidateStatus,
  RecordsPageOut,
} from '@/types';

import styles from './CandidateList.module.css';

const statuses: CandidateStatus[] = [
  'received',
  'in_progress',
  'selected',
  'discarded',
];
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

export default function CandidateList() {
  const { page, search, status, stage, applyFilters, goToPage } =
    useCandidateListFilters();
  const [result, setResult] = useState<RecordsPageOut | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    void getCandidatesPage({
      page,
      limit: 12,
      search: search || undefined,
      status: status || undefined,
      stage: stage || undefined,
    })
      .then((data) => {
        if (active) setResult(data);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : String(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [page, search, stage, status]);

  function onApplyFilters(event: FormEvent<HTMLFormElement>) {
    applyFilters(event, () => {
      setLoading(true);
      setError('');
    });
  }

  function onGoToPage(nextPage: number) {
    goToPage(nextPage, () => {
      setLoading(true);
      setError('');
    });
  }

  const totalPages = Math.max(1, Math.ceil((result?.total ?? 0) / 12));

  return (
    <main className={styles.shell}>
      <section className={styles.header}>
        <h1>Candidate Directory</h1>
        <Link href="/candidates/new" className={styles.addButton}>
          Add Candidate
        </Link>
      </section>

      <form onSubmit={onApplyFilters} className={styles.filters}>
        <input
          type="search"
          name="search"
          defaultValue={search}
          placeholder="Search by name or email"
          aria-label="Search candidates"
        />
        <select name="status" defaultValue={status} aria-label="Filter by status">
          <option value="">All statuses</option>
          {statuses.map((value) => (
            <option key={value} value={value}>{label(value)}</option>
          ))}
        </select>
        <select name="stage" defaultValue={stage} aria-label="Filter by stage">
          <option value="">All stages</option>
          {stages.map((value) => (
            <option key={value} value={value}>{label(value)}</option>
          ))}
        </select>
        <button type="submit">Apply filters</button>
      </form>

      {loading ? <p className={styles.state}>Loading candidates…</p> : null}
      {error ? <p className={styles.error} role="alert">Error loading candidates: {error}</p> : null}

      {!loading && !error && result ? (
        <>
          <p className={styles.meta}>
            Showing page {page} of {totalPages} ({result.total} candidates)
          </p>

          {result.data.length === 0 ? (
            <p className={styles.state}>No candidates match these filters.</p>
          ) : (
            <ul className={styles.grid}>
              {result.data.map((candidate) => (
                <li key={candidate.id}>
                  <article className={styles.card}>
                    <div className={styles.cardTop}>
                      <h2>
                        <Link href={`/candidates/${candidate.id}`}>{candidate.full_name}</Link>
                      </h2>
                      <span className={styles.stage}>{label(candidate.stage)}</span>
                    </div>
                    <p className={styles.role}>{candidate.position}</p>
                    <p className={styles.contact}>{candidate.email}</p>
                    <div className={styles.cardBottom}>
                      <span className={styles.status}>{label(candidate.status)}</span>
                      <Link href={`/candidates/${candidate.id}`} className={styles.viewLink}>
                        Open profile
                      </Link>
                    </div>
                  </article>
                </li>
              ))}
            </ul>
          )}

          <nav className={styles.pagination} aria-label="Candidate pages">
            <button type="button" disabled={page <= 1} onClick={() => onGoToPage(page - 1)}>
              Previous
            </button>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => onGoToPage(page + 1)}
            >
              Next
            </button>
          </nav>
        </>
      ) : null}
    </main>
  );
}
