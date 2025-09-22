'use client';

import type { ChecklistMark, ChecklistStatus } from '@/types/api';

export type MarkStatus = Exclude<ChecklistMark['mark_status'], undefined>;

const MARK_STATUS_FALLBACK: MarkStatus = 'NOT_STARTED';

const statusColors: Record<MarkStatus, string> = {
  NOT_STARTED: 'bg-slate-200 text-slate-700',
  IN_PROGRESS: 'bg-sky-200 text-sky-700',
  COMPLETED: 'bg-emerald-200 text-emerald-700',
  VALIDATED: 'bg-emerald-400 text-emerald-900',
};

const statusLabels: Record<MarkStatus, string> = {
  NOT_STARTED: 'Não iniciado',
  IN_PROGRESS: 'Em progresso',
  COMPLETED: 'Marcado pelo aluno',
  VALIDATED: 'Validado pelo professor',
};

interface ChecklistStatusCardProps {
  status: ChecklistStatus;
}

export function ChecklistStatusCard({ status }: ChecklistStatusCardProps) {
  const marks = status.marks ?? [];

  return (
    <article className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">{status.template.name}</h2>
          {status.template.description ? (
            <p className="text-sm text-slate-600">{status.template.description}</p>
          ) : null}
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Progresso</p>
          <p className="text-xl font-semibold text-slate-800">{status.percent_complete}%</p>
        </div>
      </header>
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-500 to-emerald-500 transition-all"
          style={{ width: `${status.percent_complete}%` }}
        />
      </div>
      <ul className="mt-6 space-y-3">
        {marks.map((mark) => {
          const markStatusKey = (mark.mark_status ?? MARK_STATUS_FALLBACK) as MarkStatus;
          return (
            <li
              key={mark.id}
              className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white/70 p-3 text-sm text-slate-600"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="font-medium text-slate-800">{mark.item.text}</p>
                <span
                  className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
                    statusColors[markStatusKey] ?? 'bg-slate-200 text-slate-700'
                  }`}
                >
                  {statusLabels[markStatusKey] ?? markStatusKey}
                  {mark.teacher_validated && <span className="hidden sm:inline">• Validado</span>}
                </span>
              </div>
              {mark.comment ? <p className="text-xs text-slate-500">Comentário: {mark.comment}</p> : null}
            </li>
          );
        })}
      </ul>
    </article>
  );
}
