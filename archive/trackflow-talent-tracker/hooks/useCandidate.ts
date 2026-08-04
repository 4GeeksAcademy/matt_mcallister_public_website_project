import { useState, useEffect } from 'react';
import type { RecordOut } from '../types';
import { fetchCandidate } from '../lib/api';

export function useCandidate(id: string) {
  const [candidate, setCandidate] = useState<RecordOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchCandidate(id)
      .then(setCandidate)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  return { candidate, loading, error };
}
