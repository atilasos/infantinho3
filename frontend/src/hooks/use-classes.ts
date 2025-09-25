'use client';

import { useQuery } from '@tanstack/react-query';

import { useAuth } from '@/providers/auth-provider';
import type { ClassSummary } from '@/types/api';

export function useClasses() {
  const { fetchWithAuth, isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await fetchWithAuth('/classes');
      if (!res.ok) {
        throw new Error('Não foi possível carregar as turmas.');
      }
      const data = await res.json();
      return data.results as ClassSummary[];
    },
    enabled: isAuthenticated,
  });
}

