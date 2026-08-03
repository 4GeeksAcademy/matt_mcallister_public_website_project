import Link from 'next/link';

import { getCandidatesPage } from '@/candidates';
import type { CandidateStatus } from '@/types';

import styles from './page.module.css';

export const dynamic = 'force-dynamic';

interface CandidatesPageProps {
  searchParams: Promise<{
    page?: string;
    search?: string;
    status?: CandidateStatus;
  }>;
}

function buildQuery(params: { page?: number; search?: string; status?: string }): string {
  const query = new URLSearchParams();

  if (params.page && params.page > 1) query.set('page', String(params.page));
  if (params.search) query.set('search', params.search);
  if (params.status) query.set('status', params.status);

  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

export default async function CandidatesPage({ searchParams }: CandidatesPageProps) {
  const resolved = await searchParams;
  const search = resolved.search?.trim() ?? '';
  const status = resolved.status ?? '';
  const page = Math.max(1, Number(resolved.page ?? '1') || 1);
  const limit = 12;

  let result;
  try {
    result = await getCandidatesPage({
      page,
      limit,
      search: search || undefined,
      status: (status || undefined) as CandidateStatus | undefined,
    });
  } catch (e) {
    return <main className={styles.shell}>Error loading candidates: {String(e)}</main>;
  }

  const totalPages = Math.max(1, Math.ceil(result.total / result.limit));
  const prevPage = page > 1 ? page - 1 : undefined;
  const nextPage = page < totalPages ? page + 1 : undefined;

  return (
    <main className={styles.shell}>
      <section className={styles.header}>
        <h1>Candidate Directory</h1>
        <Link href="/candidates/new" className={styles.addButton}>
          Add Candidate
        </Link>
      </section>

      <form method="get" className={styles.filters}>
        <input
          type="text"
          name="search"
          defaultValue={search}
          placeholder="Search by name, email, or role"
        />
        <select name="status" defaultValue={status}>
          <option value="">All statuses</option>
          <option value="received">Received</option>
          <option value="in_progress">In progress</option>
          <option value="selected">Selected</option>
          <option value="discarded">Discarded</option>
        </select>
        <button type="submit">Apply</button>
      </form>

      <p className={styles.meta}>
        Showing page {page} of {totalPages} ({result.total} candidates)
      </p>

      <ul className={styles.grid}>
        {result.data.map((candidate) => (
          <li key={candidate.id}>
            <article className={styles.card}>
              <div className={styles.cardTop}>
                <h2>
                  <Link href={`/candidates/${candidate.id}`}>{candidate.full_name}</Link>
                </h2>
                <span className={styles.stage}>{candidate.stage.replace('_', ' ')}</span>
              </div>
              <p className={styles.role}>{candidate.position}</p>
              <p className={styles.contact}>{candidate.email}</p>
              <div className={styles.cardBottom}>
                <span className={styles.status}>{candidate.status.replace('_', ' ')}</span>
                <Link href={`/candidates/${candidate.id}`} className={styles.viewLink}>
                  Open profile
                </Link>
              </div>
            </article>
          </li>
        ))}
      </ul>

      <nav className={styles.pagination}>
        {prevPage ? (
          <Link href={`/candidates${buildQuery({ page: prevPage, search, status })}`}>Previous</Link>
        ) : (
          <span className={styles.disabled}>Previous</span>
        )}

        {nextPage ? (
          <Link href={`/candidates${buildQuery({ page: nextPage, search, status })}`}>Next</Link>
        ) : (
          <span className={styles.disabled}>Next</span>
        )}
      </nav>
    </main>
  );
}
