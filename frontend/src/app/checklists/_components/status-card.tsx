'use client';

import type { ReactElement } from 'react';
import type { ChecklistMark, ChecklistStatus } from '@/types/api';

export type MarkStatus = Exclude<ChecklistMark['mark_status'], undefined>;

const MARK_STATUS_FALLBACK: MarkStatus = 'NOT_STARTED';

const statusColors: Record<MarkStatus, string> = {
  NOT_STARTED: 'bg-slate-100 text-slate-700 border border-slate-200',
  IN_PROGRESS: 'bg-sky-100 text-sky-700 border border-sky-200',
  COMPLETED: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
  VALIDATED: 'bg-emerald-500/10 text-emerald-800 border border-emerald-400',
};

export const MARK_STATUS_BADGE_CLASSES = statusColors;

const statusLabels: Record<MarkStatus, string> = {
  NOT_STARTED: 'Não Iniciado',
  IN_PROGRESS: 'Em Progresso',
  COMPLETED: 'Concluído',
  VALIDATED: 'Validado',
};

export const MARK_STATUS_LABELS = statusLabels;

const markOptions: Array<{ value: MarkStatus; label: string }> = [
  { value: 'NOT_STARTED', label: statusLabels.NOT_STARTED },
  { value: 'IN_PROGRESS', label: statusLabels.IN_PROGRESS },
  { value: 'COMPLETED', label: statusLabels.COMPLETED },
  { value: 'VALIDATED', label: statusLabels.VALIDATED },
];

const statusIcons: Record<MarkStatus, ReactElement> = {
  NOT_STARTED: (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 text-slate-500" aria-hidden>
      <circle cx="8" cy="8" r="3" />
    </svg>
  ),
  IN_PROGRESS: (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 text-sky-500" aria-hidden>
      <path d="M3 8a5 5 0 1 1 2.1 4.06" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" />
    </svg>
  ),
  COMPLETED: (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 text-emerald-600" aria-hidden>
      <path d="m4 8.4 2.6 2.6 5.4-6.4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" />
    </svg>
  ),
  VALIDATED: (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 text-emerald-700" aria-hidden>
      <path d="m3.5 8.5 2.5 3L12.5 4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" />
    </svg>
  ),
};

interface ChecklistStatusCardProps {
  status: ChecklistStatus;
  canEdit?: boolean;
  onUpdateMark?: (mark: ChecklistMark, nextStatus: MarkStatus) => void;
  updatingMarkId?: number | null;
  errorByMark?: Record<number, string>;
  allowedStatuses?: MarkStatus[] | null;
  isReadOnlyForMark?: (mark: ChecklistMark) => boolean;
}

export function ChecklistStatusCard({
  status,
  canEdit = false,
  onUpdateMark,
  updatingMarkId = null,
  errorByMark = {},
  allowedStatuses = null,
  isReadOnlyForMark,
}: ChecklistStatusCardProps) {
  const marks = status.marks ?? [];

  return (
    <article className="flex h-full flex-col rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 break-words">{status.template.name}</h2>
          {status.template.description ? (
            <p className="text-sm leading-relaxed text-slate-600 break-words">{status.template.description}</p>
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
      <ul className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {marks.map((mark) => {
          const displayStatus: MarkStatus = mark.teacher_validated
            ? 'VALIDATED'
            : ((mark.mark_status ?? MARK_STATUS_FALLBACK) as MarkStatus);
          const markStatusKey = displayStatus;
          const isUpdating = updatingMarkId === mark.id;
          const error = errorByMark[mark.id];

          const readOnly = isReadOnlyForMark?.(mark) ?? false;
          const showSelect = canEdit && !readOnly;
          const statusChoices = markOptions.filter((option) => !allowedStatuses || allowedStatuses.includes(option.value));

          const handleChoice = (nextStatus: MarkStatus) => {
            if (!onUpdateMark || isUpdating || nextStatus === displayStatus) {
              return;
            }
            onUpdateMark(mark, nextStatus);
          };

          const cardClass = readOnly
            ? 'border-emerald-200/80 bg-emerald-50/70 shadow-inner'
            : 'border-slate-200/80 bg-white/85 shadow-sm';

          return (
            <li
              key={mark.id}
              className={`flex h-full flex-col justify-between gap-3 rounded-2xl border p-4 text-sm text-slate-600 transition hover:border-sky-200/70 hover:shadow-md ${cardClass}`}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="font-medium leading-relaxed text-slate-800 break-words">{mark.item.text}</p>
                {!showSelect ? (
                  <span
                    className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold shadow-sm ${
                      statusColors[markStatusKey] ?? 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {statusIcons[markStatusKey]}
                    {statusLabels[markStatusKey] ?? markStatusKey}
                  </span>
                ) : null}
              </div>
              {mark.comment ? <p className="text-xs text-slate-500">Comentário: {mark.comment}</p> : null}
              {showSelect ? (
                <div className="space-y-2">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Escolher estado</p>
                  <div className="flex flex-wrap gap-2">
                    {statusChoices.map((option) => {
                      const selected = option.value === displayStatus;
                      return (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleChoice(option.value)}
                          disabled={isUpdating || selected}
                          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500 ${
                            selected
                              ? 'border-sky-500 bg-sky-500 text-white shadow-sm'
                              : 'border-slate-200 bg-white text-slate-600 hover:border-sky-300 hover:text-sky-700'
                          } ${isUpdating ? 'opacity-60' : ''}`}
                          aria-pressed={selected}
                        >
                          {statusIcons[option.value]}
                          {option.label}
                        </button>
                      );
                    })}
                  </div>
                  {error ? (
                    <p className="text-xs text-rose-600" role="alert">
                      {error}
                    </p>
                  ) : null}
                </div>
              ) : (
                readOnly && canEdit ? (
                  <p className="text-[11px] text-emerald-700/80">
                    (Objetivo fechado pelo professor.)
                  </p>
                ) : null
              )}
            </li>
          );
        })}
      </ul>
    </article>
  );
}
