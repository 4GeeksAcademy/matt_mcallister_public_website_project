import { Suspense } from 'react';

import CandidateList from '@/components/CandidateList';
import styles from '@/components/CandidateList.module.css';

export default function HomePage() {
  return (
    <Suspense fallback={<main className={styles.shell}>Loading candidates…</main>}>
      <CandidateList />
    </Suspense>
  );
}
