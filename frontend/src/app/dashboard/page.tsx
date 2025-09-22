'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { ActionCard } from '@/components/ui/action-card';
import { useAuth } from '@/providers/auth-provider';
import { extractResults } from '@/lib/utils';
import type { ClassSummary } from '@/types/api';

const quickActions = [
  {
    href: '/checklists',
    badge: 'Checklists MEM',
    description: 'Autoavaliação visível e validação docente com feedback imediato.',
    badgeClassName: 'bg-sky-100 text-sky-700',
  },
  {
    href: '/pit',
    badge: 'Planos Individuais de Trabalho',
    description: 'Acompanhe cada PIT do rascunho à avaliação cooperada.',
    badgeClassName: 'bg-emerald-100 text-emerald-700',
  },
  {
    href: '/diario',
    badge: 'Diário de Turma',
    description: 'Relate aprendizagens, decisões e projetos com editor rico.',
    badgeClassName: 'bg-amber-100 text-amber-700',
  },
  {
    href: '/projects',
    badge: 'Projetos cooperativos',
    description: 'Organize tarefas, membros e entregáveis dos projetos MEM.',
    badgeClassName: 'bg-rose-100 text-rose-700',
  },
];

export default function DashboardPage() {
  const { loading, isAuthenticated, user, fetchWithAuth } = useAuth();

  const { data: classes, isLoading } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const response = await fetchWithAuth('/classes');
      if (!response.ok) {
        throw new Error('Falha ao carregar turmas.');
      }
      const body = await response.json();
      return extractResults<ClassSummary>(body);
    },
    enabled: isAuthenticated,
  });

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-3 bg-slate-100">
        <p className="text-slate-600 text-sm uppercase tracking-[0.3em]">Infantinho 3.0</p>
        <p className="text-lg text-slate-500 animate-pulse">A carregar…</p>
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
      title="Painel cooperativo"
      description="Visão integrada das turmas, instrumentos MEM e apoio inteligente disponível via API headless."
      actions={
        <Link
          href="/assistente"
          className="rounded-full bg-sky-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-sky-700"
        >
          Falar com o assistente IA
        </Link>
      }
    >
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {quickActions.map((item) => (
          <ActionCard key={item.href} {...item} />
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800">Turmas em acompanhamento</h2>
          <p className="mt-1 text-sm text-slate-600">
            Acesso rápido às turmas associadas e instrumentos prontos a utilizar.
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {classes?.length ? (
              classes.map((turma) => (
                <article key={turma.id} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5">
                  <h3 className="text-base font-semibold text-slate-800">{turma.name}</h3>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-500 mt-1">Ano {turma.year}</p>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                    <span className="rounded-full bg-white px-3 py-1 shadow-sm">Checklists</span>
                    <span className="rounded-full bg-white px-3 py-1 shadow-sm">PIT</span>
                    <span className="rounded-full bg-white px-3 py-1 shadow-sm">Projetos</span>
                  </div>
                </article>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
                Ainda sem turmas associadas ao perfil {user?.role ?? 'convidado'}.
              </div>
            )}
          </div>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-sky-500 via-sky-600 to-sky-700 p-6 text-white shadow-sm">
          <h2 className="text-lg font-semibold">Workflow headless pronto</h2>
          <p className="mt-2 text-sm text-sky-50/80">
            A arquitetura Django + Next.js garante dados sincronizados, autenticação Azure AD e endpoints dedicados
            para cada instrumento MEM, prontos para demonstração à direção.
          </p>
          <ul className="mt-4 space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-200" />
              Checklists com validação de papéis
            </li>
            <li className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-200" />
              PIT com fluxo completo de aprovação
            </li>
            <li className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-200" />
              Projetos e diário integrados
            </li>
            <li className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-200" />
              Assistente IA contextualizado
            </li>
          </ul>
        </div>
      </section>
    </AppShell>
  );
}
