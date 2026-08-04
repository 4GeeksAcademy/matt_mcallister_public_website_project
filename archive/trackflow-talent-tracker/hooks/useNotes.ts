import { useState, useEffect } from 'react';
import type { Note } from '../types';
import { fetchNotes } from '../lib/api';

export function useNotes(candidateId: string) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchNotes(candidateId)
      .then(setNotes)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [candidateId]);

  return { notes, loading, error };
}
