'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import { extractResults } from '@/lib/utils';
import type { IndividualPlan, PlanTask } from '@/types/api';

type PlanStatus = IndividualPlan['status'];
type TaskState = Exclude<PlanTask['state'], undefined>;

const statusMeta: Record<PlanStatus, { label: string; description: string; tone: string }> = {
  draft: {
    label: 'Rascunho',
    description: 'Aluno prepara objetivos e tarefas com apoio docente.',
    tone: 'bg-slate-200 text-slate-700',
  },
  submitted: {
    label: 'Submetido',
    description: 'A aguardar validação do professor responsável.',
    tone: 'bg-sky-200 text-sky-700',
  },
  approved: {
    label: 'Aprovado',
    description: 'Plano aprovado pelo professor; tarefas em execução.',
    tone: 'bg-emerald-200 text-emerald-700',
  },
  concluded: {
    label: 'Concluído',
    description: 'Aluno registou autoavaliação; aguarda feedback docente.',
    tone: 'bg-amber-200 text-amber-700',
  },
  evaluated: {
    label: 'Avaliado',
    description: 'Processo encerrado com avaliação docente.',
    tone: 'bg-emerald-400 text-emerald-900',
  },
};

const statusOrder: PlanStatus[] = ['draft', 'submitted', 'approved', 'concluded', 'evaluated'];

const TASK_STATE_FALLBACK: TaskState = 'pending';
const taskStateLabels: Record<TaskState, string> = {
  pending: 'Pendente',
  in_progress: 'Em curso',
  done: 'Concluída',
  validated: 'Validada',
};

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  try {
    return new Intl.DateTimeFormat('pt-PT', { day: '2-digit', month: 'short' }).format(new Date(value));
  } catch (error) {
    console.error('Invalid date', error);
    return value;
  }
}

export default function PlansPage() {
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ['pit-plans'],
    queryFn: async () => {
      const res = await fetchWithAuth('/pit/plans');
      if (!res.ok) {
        throw new Error('Não foi possível carregar os planos individuais.');
      }
      const body = await res.json();
      return extractResults<IndividualPlan>(body);
    },
    enabled: isAuthenticated,
  });

  const activePlans = useMemo(() => data?.filter((plan) => plan.status !== 'evaluated'), [data]);

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">A carregar planos individuais…</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
        <p className="text-sm text-slate-600">Inicie sessão para consultar os PIT.</p>
      </main>
    );
  }

  return (
    <AppShell
      title="Planos Individuais de Trabalho"
      description="Fluxo completo do PIT do aluno, desde o rascunho à avaliação e comunicação família-escola."
      actions={
        <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-2 text-sm text-slate-600 shadow-sm">
          {activePlans?.length ?? 0} planos ativos
        </div>
      }
    >
      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      ) : data?.length ? (
        <div className="space-y-6">
          {data.map((plan) => {
            const meta = statusMeta[plan.status];
            const currentStep = statusOrder.indexOf(plan.status);
            return (
              <article key={plan.id} className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
                <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-800">{plan.period_label}</h2>
                    <p className="text-sm text-slate-600">
                      {formatDate(plan.start_date ?? null)} → {formatDate(plan.end_date ?? null)}
                    </p>
                  </div>
                  <span className={`inline-flex max-w-[220px] items-center rounded-full px-4 py-1 text-xs font-semibold uppercase tracking-[0.25em] ${meta.tone}`}>
                    {meta.label}
                  </span>
                </header>
                <p className="mt-4 text-sm text-slate-600">{meta.description}</p>
                {plan.general_objectives && (
                  <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm text-slate-700">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Objetivos gerais</p>
                    <p className="mt-2 leading-relaxed">{plan.general_objectives}</p>
                  </div>
                )}
                <div className="mt-6 grid gap-6 lg:grid-cols-[3fr,2fr]">
                  <ul className="space-y-3">
                    {plan.tasks.length ? (
                      plan.tasks.map((task) => {
                        const taskState = (task.state ?? TASK_STATE_FALLBACK) as TaskState;
                        return (
                          <li key={task.id} className="rounded-2xl border border-slate-200 bg-white/70 p-4 text-sm text-slate-600">
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                              <p className="font-medium text-slate-800">{task.description}</p>
                              {task.subject && <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{task.subject}</p>}
                            </div>
                            <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
                              {taskStateLabels[taskState] ?? taskState}
                            </span>
                          </div>
                          {task.teacher_feedback && (
                            <p className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                              Feedback docente: {task.teacher_feedback}
                            </p>
                          )}
                          {task.evidence_link && (
                            <a
                              href={task.evidence_link}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-3 inline-flex items-center gap-2 text-xs font-semibold text-sky-600 hover:underline"
                            >
                              Ver evidência
                              <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" className="h-4 w-4">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h9m0 0 3-3m-3 3 3 3" />
                              </svg>
                            </a>
                          )}
                        </li>
                        );
                      })
                    ) : (
                      <li className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-4 text-sm text-slate-600">
                        Sem tarefas registadas neste plano.
                      </li>
                    )}
                  </ul>
                  <div className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Linha temporal</p>
                    <ol className="space-y-3 text-sm">
                      {statusOrder.map((step, index) => (
                        <li
                          key={step}
                          className={`rounded-2xl border px-4 py-3 ${
                            index <= currentStep
                              ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                              : 'border-slate-200 bg-slate-50 text-slate-500'
                          }`}
                        >
                          <p className="font-semibold uppercase tracking-[0.3em] text-xs">{statusMeta[step].label}</p>
                          <p className="mt-1 text-xs leading-relaxed text-current">{statusMeta[step].description}</p>
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
          Ainda não existem PIT disponíveis. Utilize o script de povoamento ou a API para gerar planos de demonstração.
        </div>
      )}
    </AppShell>
  );
}
