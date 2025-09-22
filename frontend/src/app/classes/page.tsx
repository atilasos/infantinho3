'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import { extractResults } from '@/lib/utils';
import type { ClassSummary } from '@/types/api';

export default function ClassesPage() {
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await fetchWithAuth('/classes');
      if (!res.ok) {
        throw new Error('Falha ao carregar as turmas.');
      }
      const body = await res.json();
      return extractResults<ClassSummary>(body);
    },
    enabled: isAuthenticated,
  });

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-3 bg-slate-100">
        <p className="text-sm text-slate-500">A carregar turmas…</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
        <h1 className="text-xl font-semibold text-slate-800">Sessão expirada</h1>
        <Link href="/login" className="rounded-full bg-sky-600 px-4 py-2 text-white">
          Voltar ao login
        </Link>
      </main>
    );
  }

  return (
    <AppShell
      title="Turmas"
      description="Estrutura atual de turmas ligadas à sua conta, com acesso rápido aos instrumentos MEM."
    >
      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2">
          {data?.map((turma) => (
            <article key={turma.id} className="rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-800">{turma.name}</h2>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-500 mt-1">Ano {turma.year}</p>
                </div>
                <Link
                  href={`/turmas/${turma.id}`}
                  className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
                >
                  Abrir turma
                </Link>
              </div>
              <div className="mt-4 grid gap-3 text-sm text-slate-600">
                <p>• Checklists MEM com validação a dois passos.</p>
                <p>• PIT com histórico de versões.</p>
                <p>• Projetos cooperativos e diário integrado.</p>
              </div>
            </article>
          )) ?? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
              Ainda sem turmas atribuídas. Solicite ao professor coordenador a associação.
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
