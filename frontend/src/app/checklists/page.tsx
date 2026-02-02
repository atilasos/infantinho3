'use client';

import { Suspense, useMemo } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import { extractResults } from '@/lib/utils';
import type { AppUser, ChecklistStatus } from '@/types/api';

function studentName(student?: AppUser | null) {
  if (!student) return 'Aluno desconhecido';
  const fullName = `${student.first_name ?? ''} ${student.last_name ?? ''}`.trim();
  return fullName || student.username || student.email || 'Aluno sem nome';
}

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  try {
    return new Intl.DateTimeFormat('pt-PT', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function ChecklistsContent() {
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();
  const searchParams = useSearchParams();
  const classIdParam = searchParams.get('class_id');

  const { data, isLoading, error } = useQuery({
    queryKey: ['checklists-statuses'],
    queryFn: async () => {
      const res = await fetchWithAuth('/checklists/statuses');
      if (!res.ok) {
        throw new Error('Não foi possível obter as checklists.');
      }
      const body = await res.json();
      return extractResults<ChecklistStatus>(body);
    },
    enabled: isAuthenticated,
  });

  const filteredStatuses = useMemo(() => {
    if (!data) return [] as ChecklistStatus[];
    if (!classIdParam) return data;
    return data.filter((status) => String(status.student_class_id) === classIdParam);
  }, [data, classIdParam]);

  const totalCompleted = useMemo(() => {
    if (!filteredStatuses.length) return 0;
    return (
      filteredStatuses.reduce((acc, status) => acc + status.percent_complete, 0) /
      filteredStatuses.length
    );
  }, [filteredStatuses]);

  const studentSummaries = useMemo(() => {
    if (!filteredStatuses.length) {
      return [] as Array<{
        student: AppUser;
        statuses: ChecklistStatus[];
        average: number;
        averageRounded: number;
        latestUpdatedAt: string | null;
      }>;
    }

    const map = new Map<number, { student: AppUser; statuses: ChecklistStatus[] }>();

    filteredStatuses.forEach((status) => {
      const student = status.student as AppUser | undefined;
      const studentId = student?.id;
      if (!student || !studentId) {
        return;
      }
      const existing = map.get(studentId);
      if (existing) {
        existing.statuses.push(status);
      } else {
        map.set(studentId, { student, statuses: [status] });
      }
    });

    return Array.from(map.values())
      .map(({ student, statuses }) => {
        const total = statuses.reduce((acc, item) => acc + item.percent_complete, 0);
        const average = total / statuses.length;
        const latestUpdatedAt = statuses.reduce<string | null>((latest, item) => {
          if (!item.updated_at) return latest;
          if (!latest) return item.updated_at;
          return new Date(item.updated_at) > new Date(latest) ? item.updated_at : latest;
        }, null);

        const sortedStatuses = [...statuses].sort((a, b) =>
          a.template.name.localeCompare(b.template.name, 'pt-PT'),
        );

        return {
          student,
          statuses: sortedStatuses,
          average,
          averageRounded: Math.round(average),
          latestUpdatedAt,
        };
      })
      .sort((a, b) => studentName(a.student).localeCompare(studentName(b.student), 'pt-PT'));
  }, [filteredStatuses]);

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">A carregar checklists…</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
        <p className="text-sm text-slate-600">Inicie sessão para consultar as checklists.</p>
      </main>
    );
  }

  return (
    <AppShell
      title="Checklists MEM"
      description="Monitorize a autoavaliação dos alunos e a validação docente em cada instrumento cooperativo."
      actions={
        <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-2 text-sm text-slate-600 shadow-sm">
          Média geral concluída: <span className="font-semibold text-slate-800">{totalCompleted.toFixed(0)}%</span>
        </div>
      }
    >
      {classIdParam ? (
        <p className="mb-4 text-sm text-slate-600">
          A mostrar o progresso dos alunos da turma <span className="font-semibold">#{classIdParam}</span>.
        </p>
      ) : null}
      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      ) : studentSummaries.length ? (
        <div className="space-y-4">
          {studentSummaries.map(({ student, statuses, averageRounded, latestUpdatedAt }) => {
            const detailHref = `/checklists/alunos/${student.id}${classIdParam ? `?class_id=${classIdParam}` : ''}`;
            const preview = statuses.slice(0, 3);
            const remaining = statuses.length - preview.length;

            return (
              <article
                key={student.id}
                className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm transition hover:border-sky-200 hover:shadow-md"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <Link
                      href={detailHref}
                      className="inline-flex items-center gap-2 text-base font-semibold text-sky-700 transition hover:text-sky-900"
                    >
                      {studentName(student)}
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        className="h-4 w-4"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                      </svg>
                    </Link>
                    <p className="text-sm text-slate-600">
                      {statuses.length} {statuses.length === 1 ? 'checklist' : 'checklists'} monitorizadas.
                    </p>
                    {latestUpdatedAt ? (
                      <p className="text-xs text-slate-500">Atualizado {formatDateTime(latestUpdatedAt)}</p>
                    ) : null}
                  </div>
                  <div className="text-right">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Média concluída</p>
                    <p className="text-2xl font-semibold text-slate-800">{averageRounded}%</p>
                  </div>
                </div>
                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-sky-500 to-emerald-500 transition-all"
                    style={{ width: `${averageRounded}%` }}
                    aria-hidden
                  />
                </div>
                <div className="mt-4 space-y-2">
                  {preview.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white/70 px-3 py-2 text-xs text-slate-600"
                    >
                      <span className="font-medium text-slate-700">{item.template.name}</span>
                      <span className="font-semibold text-slate-700">{item.percent_complete}%</span>
                    </div>
                  ))}
                  {remaining > 0 ? (
                    <p className="text-right text-xs text-slate-500">
                      +{remaining} {remaining === 1 ? 'checklist' : 'checklists'} adicionais
                    </p>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
          {classIdParam
            ? 'Ainda não há checklists monitorizadas para esta turma.'
            : 'Ainda sem registos de checklists disponíveis. Crie ou atribua checklists para começar a monitorização.'}
        </div>
      )}
    </AppShell>
  );
}

export default function ChecklistsPage() {
  return (
    <Suspense fallback={
      <AppShell title="Listas de Verificação">
        <div className="text-center text-slate-500 py-8">A carregar...</div>
      </AppShell>
    }>
      <ChecklistsContent />
    </Suspense>
  );
}
