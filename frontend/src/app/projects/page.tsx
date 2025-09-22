'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import { extractResults } from '@/lib/utils';
import type { Project } from '@/types/api';

const projectStateLabels: Record<Project['state'], string> = {
  active: 'Em curso',
  completed: 'Concluído',
  canceled: 'Cancelado',
};

export default function ProjectsPage() {
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await fetchWithAuth('/projects');
      if (!res.ok) {
        throw new Error('Falha ao carregar projetos.');
      }
      const body = await res.json();
      return extractResults<Project>(body);
    },
    enabled: isAuthenticated,
  });

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">A carregar projetos…</p>
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
      title="Projetos cooperativos"
      description="Organização visual dos projetos ativos, alinhados com o ciclo cooperativo MEM e prontos para demonstração."
      actions={
        <Link
          href="/assistente?context=projects"
          className="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
        >
          Pedir apoio ao tutor IA
        </Link>
      }
    >
      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      ) : (
        <div className="grid gap-5">
          {data?.map((project) => (
            <article key={project.id} className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-800">{project.title}</h2>
                <span className="mt-1 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
                  {projectStateLabels[project.state] ?? project.state}
                </span>
                </div>
                <div className="flex items-center gap-2">
                  <Link
                    href={`/projects/${project.id}`}
                    className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
                  >
                    Ver detalhes
                  </Link>
                </div>
              </div>
              <p className="mt-4 text-sm text-slate-600">{project.description || 'Sem descrição.'}</p>
            </article>
          )) ?? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
              Ainda não existem projetos associados. Utilize a API para criar novos projetos e demonstrar a colaboração.
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
