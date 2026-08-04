'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, useCallback } from 'react';

import type { CandidateStage, CandidateStatus } from '@/types';

export function useCandidateListFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const page = Math.max(1, Number(searchParams.get('page') ?? '1') || 1);
  const search = searchParams.get('search') ?? '';
  const status = (searchParams.get('status') ?? '') as CandidateStatus | '';
  const stage = (searchParams.get('stage') ?? '') as CandidateStage | '';

  const navigate = useCallback(
    (params: URLSearchParams) => {
      const query = params.toString();
      router.push(query ? `${pathname}?${query}` : pathname);
    },
    [pathname, router]
  );

  const applyFilters = useCallback(
    (event: FormEvent<HTMLFormElement>, beforeNavigate?: () => void) => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const next = new URLSearchParams();
      for (const key of ['search', 'status', 'stage']) {
        const value = String(data.get(key) ?? '').trim();
        if (value) next.set(key, value);
      }
      beforeNavigate?.();
      navigate(next);
    },
    [navigate]
  );

  const goToPage = useCallback(
    (nextPage: number, beforeNavigate?: () => void) => {
      const next = new URLSearchParams(searchParams.toString());
      if (nextPage <= 1) next.delete('page');
      else next.set('page', String(nextPage));
      beforeNavigate?.();
      navigate(next);
    },
    [navigate, searchParams]
  );

  return { page, search, status, stage, applyFilters, goToPage };
}
