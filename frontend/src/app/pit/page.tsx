'use client';

import { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import { extractResults } from '@/lib/utils';
import type { AppUser, ClassSummary, IndividualPlan } from '@/types/api';
import { useClasses } from '@/hooks/use-classes';
import { GeneratePitWizard } from './_components/generate-wizard';

type PlanStatus = IndividualPlan['status'];

const statusMeta: Record<PlanStatus, { label: string; description: string; tone: string; toneLight: string }> = {
  draft: {
    label: 'Rascunho',
    description: 'Aluno prepara objetivos e tarefas com apoio docente.',
    tone: 'bg-slate-200 text-slate-700',
    toneLight: 'bg-slate-100 text-slate-500',
  },
  submitted: {
    label: 'Submetido',
    description: 'A aguardar validação do professor responsável.',
    tone: 'bg-sky-200 text-sky-700',
    toneLight: 'bg-sky-50 text-sky-600',
  },
  approved: {
    label: 'Aprovado',
    description: 'Plano aprovado pelo professor; tarefas em execução.',
    tone: 'bg-emerald-200 text-emerald-700',
    toneLight: 'bg-emerald-50 text-emerald-600',
  },
  concluded: {
    label: 'Concluído',
    description: 'Aluno registou autoavaliação; aguarda feedback docente.',
    tone: 'bg-amber-200 text-amber-700',
    toneLight: 'bg-amber-50 text-amber-600',
  },
  evaluated: {
    label: 'Avaliado',
    description: 'Processo encerrado com avaliação docente.',
    tone: 'bg-emerald-400 text-emerald-900',
    toneLight: 'bg-emerald-50 text-emerald-700',
  },
};

const statusOrder: PlanStatus[] = ['draft', 'submitted', 'approved', 'concluded', 'evaluated'];

function formatUserDisplayName(user: IndividualPlan['student'] | AppUser | undefined | null) {
  if (!user) return '—';
  const first = typeof user.first_name === 'string' ? user.first_name : '';
  const last = typeof user.last_name === 'string' ? user.last_name : '';
  const combined = `${first} ${last}`.trim();
  if (combined) return combined;
  if (user.name) return user.name;
  if (user.email) return user.email;
  if (user.username) return user.username;
  return `Utilizador #${user.id ?? '?'}`;
}

function formatDate(value: string | null | undefined, options: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short' }) {
  if (!value) return '—';
  try {
    return new Intl.DateTimeFormat('pt-PT', options).format(new Date(value));
  } catch (error) {
    console.error('Invalid date', error);
    return value;
  }
}

function planProgress(plan: IndividualPlan) {
  const total = plan.tasks.length;
  if (!total) return { percent: 0, done: 0, total: 0 };
  const doneCount = plan.tasks.filter((task) => task.state === 'done' || task.state === 'validated').length;
  return {
    percent: Math.round((doneCount / total) * 100),
    done: doneCount,
    total,
  };
}

function statusStep(plan: IndividualPlan) {
  return statusOrder.indexOf(plan.status);
}

function summaryHighlights(plan: IndividualPlan) {
  const latestTask = [...plan.tasks]
    .filter((task) => Boolean(task.updated_at))
    .sort((a, b) => new Date(b.updated_at ?? '').getTime() - new Date(a.updated_at ?? '').getTime())[0];
  const latestEvidence = plan.tasks.find((task) => Boolean(task.evidence_link));
  return {
    latestTask,
    latestEvidence,
  };
}

export default function PitDashboardPage({ children }: { children?: React.ReactNode }) {
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();
  const classesQuery = useClasses();

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
  const classes: ClassSummary[] = classesQuery.data ?? [];
  const plansByClass = useMemo(() => {
    if (!activePlans || !activePlans.length) return [] as Array<{ turma: ClassSummary | null; plans: IndividualPlan[] }>;
    const grouped = new Map<number | null, { turma: ClassSummary | null; plans: IndividualPlan[] }>();
    activePlans.forEach((plan) => {
      const classId = plan.student_class?.id ?? null;
      const entry = grouped.get(classId) ?? {
        turma: plan.student_class ?? null,
        plans: [],
      };
      entry.plans.push(plan);
      grouped.set(classId, entry);
    });
    return Array.from(grouped.values()).sort((a, b) => {
      const nameA = a.turma?.name ?? '';
      const nameB = b.turma?.name ?? '';
      return nameA.localeCompare(nameB, 'pt-PT');
    });
  }, [activePlans]);

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

  const content = error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      ) : plansByClass.length ? (
        <div className="space-y-6">
          {plansByClass.map(({ turma, plans }) => (
            <section key={turma?.id ?? 'sem-turma'} className="space-y-3">
              <header className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">
                  {turma?.name ?? 'Turma sem referência'}
                </h2>
                <span className="text-xs text-slate-400">{plans.length} plano(s) ativo(s)</span>
              </header>
              <div className="space-y-3">
                {plans.map((plan) => (
                  <PlanSummaryCard key={plan.id} plan={plan} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
          Ainda não existem PIT ativos. Gere um novo plano ou consulte os planos avaliados dentro do detalhe do aluno.
        </div>
      );

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
      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)] lg:items-start">
        <div className="space-y-6">{content}</div>
        <div className="space-y-6">
          {classes.length ? (
            <GeneratePitWizard classes={classes} />
          ) : classesQuery.isLoading ? (
            <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 text-sm text-slate-600">
              A carregar turmas…
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
              Não foi possível carregar as turmas para gerar novos PIT.
            </div>
          )}
          {children}
        </div>
      </div>
    </AppShell>
  );
}

interface PlanSummaryCardProps {
  plan: IndividualPlan;
}

function PlanSummaryCard({ plan }: PlanSummaryCardProps) {
  const router = useRouter();
  const meta = statusMeta[plan.status];
  const progress = planProgress(plan);
  const currentStep = statusStep(plan);
  const { latestTask, latestEvidence } = summaryHighlights(plan);
  const studentName = formatUserDisplayName(plan.student);

  return (
    <article className="rounded-3xl border border-slate-200 bg-white/90 p-5 shadow-sm transition hover:border-sky-200 hover:shadow-md">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-800">{plan.period_label}</h2>
          <p className="text-xs text-slate-500">
            {formatDate(plan.start_date ?? null)} → {formatDate(plan.end_date ?? null)} ·{' '}
            <span className="font-medium text-slate-700">{studentName}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] ${meta.tone}`}>
            {meta.label}
          </span>
          <button
            type="button"
            onClick={() => router.push(`/pit/${plan.id}/editar`)}
            className="inline-flex items-center rounded-full border border-sky-500 px-3 py-1 text-xs font-semibold text-sky-600 transition hover:border-sky-600"
          >
            Ver detalhes
          </button>
        </div>
      </header>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white/70 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Avanço</p>
          <p className="mt-2 flex items-baseline gap-2 text-sm text-slate-700">
            <span className="text-2xl font-semibold text-slate-900">{progress.percent}%</span>
            <span className="text-xs">{progress.done} de {progress.total} tarefas</span>
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white/70 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Linha temporal</p>
          <ol className="mt-2 flex items-center gap-2 text-[11px] text-slate-500">
            {statusOrder.map((status, index) => (
              <li
                key={status}
                className={`flex-1 rounded-full border px-2 py-1 text-center ${
                  index <= currentStep ? meta.toneLight : 'border-slate-200'
                }`}
              >
                {statusMeta[status].label}
              </li>
            ))}
          </ol>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white/70 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Destaques recentes</p>
          <ul className="mt-2 space-y-1 text-xs text-slate-600">
            {latestTask ? (
              <li>
                Última tarefa: <span className="font-medium text-slate-800">{latestTask.description}</span>
              </li>
            ) : (
              <li>Sem tarefas atualizadas recentemente.</li>
            )}
            {latestEvidence ? (
              <li>
                Evidência: <span className="font-medium text-slate-800">{latestEvidence.description}</span>
              </li>
            ) : (
              <li>Sem evidências anexadas.</li>
            )}
          </ul>
        </div>
      </div>
    </article>
  );
}
