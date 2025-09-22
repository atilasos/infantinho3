'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { notFound, useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import type { AppUser } from '@/types/api';

interface ClassDetailResponse {
  id: number;
  name: string;
  year: number;
  students: AppUser[];
  teachers: AppUser[];
}

export default function TurmaDetailPage() {
  const params = useParams<{ classId: string }>();
  const classId = params?.classId ?? '';
  const numericId = Number(classId);

  if (!classId || Number.isNaN(numericId)) {
    notFound();
  }

  const { fetchWithAuth, isAuthenticated, loading } = useAuth();

  const {
    data: turma,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['turma', numericId],
    queryFn: async () => {
      const res = await fetchWithAuth(`/classes/${numericId}`);
      if (res.status === 404) {
        notFound();
      }
      if (!res.ok) {
        throw new Error('Não foi possível carregar a turma.');
      }
      const body: ClassDetailResponse = await res.json();
      return body;
    },
    enabled: isAuthenticated,
  });

  const menuLinks = useMemo(() => {
    if (!turma) {
      return [];
    }
    return [
      { href: `/checklists?class_id=${turma.id}`, label: 'Checklists da turma' },
      { href: `/pit?class_id=${turma.id}`, label: 'Planos Individualizados (PIT)' },
      { href: `/projects?class_id=${turma.id}`, label: 'Projetos cooperativos' },
      { href: `/turmas/${turma.id}/diario`, label: 'Diário de bordo' },
    ];
  }, [turma]);

  if (!isAuthenticated && !loading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
        <h1 className="text-xl font-semibold text-slate-800">Sessão expirada</h1>
        <Link href="/login" className="rounded-full bg-sky-600 px-4 py-2 text-white">
          Voltar ao login
        </Link>
      </main>
    );
  }

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-3 bg-slate-100">
        <p className="text-sm text-slate-500">A carregar dados da turma…</p>
      </main>
    );
  }

  if (error) {
    return (
      <AppShell title="Turma" description="Detalhes da turma.">
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      </AppShell>
    );
  }

  if (!turma) {
    notFound();
  }

  const { teachers = [], students = [] } = turma;

  return (
    <AppShell
      title={`Turma ${turma.name}`}
      description={`Ano ${turma.year} — visão geral dos membros e instrumentos ativos.`}
    >
      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm lg:col-span-2">
          <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Professores</h2>
          <ul className="mt-4 grid gap-3">
            {teachers.length === 0 ? (
              <li className="text-sm text-slate-600">Sem professores associados.</li>
            ) : (
              teachers.map((prof) => (
                <li key={prof.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                  <span className="font-medium text-slate-800">{prof.full_name || prof.email}</span>
                  <span className="ml-2 text-xs uppercase tracking-wide text-slate-500">{prof.role ?? 'professor'}</span>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Instrumentos MEM</h2>
          <ul className="mt-4 grid gap-3 text-sm text-slate-700">
            {menuLinks.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 transition hover:border-sky-200 hover:bg-sky-50"
                >
                  <span>{item.label}</span>
                  <span className="text-xs text-slate-500">Abrir</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mt-8 rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Alunos</h2>
            <p className="text-xs text-slate-500 mt-1">Total: {students.length}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href={`/checklists?class_id=${turma.id}`}
              className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
            >
              Ver checklists
            </Link>
            <Link
              href={`/turmas/${turma.id}/diario`}
              className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
            >
              Ver diário
            </Link>
          </div>
        </div>
        <div className="mt-4 grid gap-3">
          {students.length === 0 ? (
            <p className="text-sm text-slate-600">Ainda não existem alunos associados.</p>
          ) : (
            students.map((aluno) => (
              <article
                key={aluno.id}
                className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700"
              >
                <span className="font-medium text-slate-800">{aluno.full_name || aluno.email}</span>
                <span className="ml-2 text-xs uppercase tracking-wide text-slate-500">{aluno.role ?? 'aluno'}</span>
              </article>
            ))
          )}
        </div>
      </section>
    </AppShell>
  );
}
