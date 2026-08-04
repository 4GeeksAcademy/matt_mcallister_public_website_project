import { useState, useEffect } from 'react';
import type { RecordOut } from '../types';
import { fetchCandidates } from '../lib/api';

export function useCandidates(params?: Record<string, string | number>) {
  const [candidates, setCandidates] = useState<RecordOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchCandidates(params)
      .then(setCandidates)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [JSON.stringify(params)]);

  return { candidates, loading, error };
}
