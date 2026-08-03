import Link from 'next/link';

import { getCandidatesPage } from '@/candidates';

import styles from './page.module.css';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  let list = { total: 0, data: [] as Awaited<ReturnType<typeof getCandidatesPage>>['data'] };

  try {
    list = await getCandidatesPage({ page: 1, limit: 12 });
  } catch (error) {
    return <main className={styles.shell}>Error loading candidates: {String(error)}</main>;
  }

  const inProgress = list.data.filter((item) => item.status === 'in_progress').length;
  const selected = list.data.filter((item) => item.status === 'selected').length;
  const pendingReview = list.data.filter((item) => item.stage === 'review').length;

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <p className={styles.kicker}>Talent Pipeline</p>
        <h1>Hiring Flow Dashboard</h1>
        <p className={styles.subtitle}>
          Monitor your funnel in one place and move faster on top applicants.
        </p>
        <div className={styles.heroActions}>
          <Link href="/candidates/new" className={styles.primaryCta}>
            Add Candidate
          </Link>
          <Link href="/candidates" className={styles.secondaryCta}>
            Open Full List
          </Link>
        </div>
      </section>

      <section className={styles.stats}>
        <article>
          <span>Total Candidates</span>
          <strong>{list.total}</strong>
        </article>
        <article>
          <span>In Progress</span>
          <strong>{inProgress}</strong>
        </article>
        <article>
          <span>Selected</span>
          <strong>{selected}</strong>
        </article>
        <article>
          <span>Pending Review</span>
          <strong>{pendingReview}</strong>
        </article>
      </section>

      <section className={styles.listBlock}>
        <div className={styles.blockHeader}>
          <h2>Recent Candidates</h2>
          <Link href="/candidates">See all</Link>
        </div>
        <ul className={styles.list}>
          {list.data.map((candidate) => (
            <li key={candidate.id} className={styles.row}>
              <div>
                <Link href={`/candidates/${candidate.id}`} className={styles.name}>
                  {candidate.full_name}
                </Link>
                <p>{candidate.position}</p>
              </div>
              <div className={styles.tags}>
                <span>{candidate.status.replace('_', ' ')}</span>
                <span>{candidate.stage.replace('_', ' ')}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
