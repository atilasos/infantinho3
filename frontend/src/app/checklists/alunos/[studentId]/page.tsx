'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { notFound, useParams, useSearchParams } from 'next/navigation';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import type { AppUser, ChecklistMark, ChecklistStatus, ChecklistTemplate } from '@/types/api';
import {
  ChecklistStatusCard,
  MARK_STATUS_BADGE_CLASSES,
  MARK_STATUS_LABELS,
  type MarkStatus,
} from '../../_components/status-card';
import {
  useChecklistStatuses,
  useChecklistTemplates,
  useCreateChecklistStatus,
  useUpdateChecklistMark,
  useChecklistAutosave,
  useSubmitChecklist,
  useChecklistStateHelpers,
} from '@/hooks/use-checklists';

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

export default function StudentChecklistsPage() {
  const { isAuthenticated, loading, user } = useAuth();
  const params = useParams<{ studentId: string }>();
  const searchParams = useSearchParams();
  const classIdParam = searchParams.get('class_id');
  const studentId = params?.studentId;

  if (!studentId) notFound();

  const classFilter = classIdParam ? Number(classIdParam) : undefined;
  const { data: statusesData, isLoading, error } = useChecklistStatuses(classFilter);
  const { data: templatesData } = useChecklistTemplates();
  const createStatusMutation = useCreateChecklistStatus();
  const updateMarkMutation = useUpdateChecklistMark();

  const studentStatuses = useMemo(() => {
    if (!statusesData) return [] as ChecklistStatus[];
    return statusesData.filter((status) => String(status.student?.id ?? '') === studentId);
  }, [statusesData, studentId]);

  const student = studentStatuses[0]?.student as AppUser | undefined;
  const role = user?.role;
  const isProfessor = Boolean(user && (role === 'professor' || role === 'admin' || user.is_superuser));
  const isStudentViewingSelf = Boolean(user && role === 'aluno' && user.id === student?.id);
  const canEdit = isProfessor || isStudentViewingSelf;

  const average = useMemo(() => {
    if (!studentStatuses.length) return 0;
    return (
      studentStatuses.reduce((acc, status) => acc + status.percent_complete, 0) /
      studentStatuses.length
    );
  }, [studentStatuses]);

  const latestUpdatedAt = useMemo(() => {
    if (!studentStatuses.length) return null as string | null;
    return studentStatuses.reduce<string | null>((latest, item) => {
      if (!item.updated_at) return latest;
      if (!latest) return item.updated_at;
      return new Date(item.updated_at) > new Date(latest) ? item.updated_at : latest;
    }, null);
  }, [studentStatuses]);

  const statusTotals = useMemo(() => {
    const initial: Record<MarkStatus, number> = {
      NOT_STARTED: 0,
      IN_PROGRESS: 0,
      COMPLETED: 0,
      VALIDATED: 0,
    };
    studentStatuses.forEach((status) => {
      status.marks?.forEach((mark) => {
        const bucket: MarkStatus = mark.teacher_validated
          ? 'VALIDATED'
          : ((mark.mark_status ?? 'NOT_STARTED') as MarkStatus);
        initial[bucket] += 1;
      });
    });
    return initial;
  }, [studentStatuses]);

  const totalMarks = useMemo(
    () => Object.values(statusTotals).reduce((acc, value) => acc + value, 0),
    [statusTotals],
  );

  const backHref = useMemo(() => {
    const base = '/checklists';
    if (!classIdParam) return base;
    return `${base}?class_id=${classIdParam}`;
  }, [classIdParam]);

  const availableTemplates = useMemo(() => {
    if (!templatesData) return [] as ChecklistTemplate[];
    const startedTemplateIds = new Set(studentStatuses.map((status) => status.template?.id));
    return templatesData.filter((template) => {
      const classMatches = template.classes?.some((cls) =>
        classIdParam ? String(cls.id) === classIdParam : studentStatuses.some((status) => status.student_class?.id === cls.id),
      );
      if (!classMatches) return false;
      return !startedTemplateIds.has(template.id);
    });
  }, [templatesData, studentStatuses, classIdParam]);

  const handleCreateStatus = useCallback(
    async (templateId: number) => {
      if (!classIdParam) return;
      await createStatusMutation.mutateAsync({ templateId, classId: Number(classIdParam) });
    },
    [classIdParam, createStatusMutation],
  );

  const handleMarkUpdate = useCallback(
    async (mark: ChecklistMark, nextStatus: MarkStatus) => {
      if (!canEdit) return;
      const isCurrentlyValidated = Boolean(mark.teacher_validated);
      if (!isProfessor && isCurrentlyValidated) return;
      const teacherValidated = isProfessor ? nextStatus === 'VALIDATED' : undefined;
      const normalisedStatus: MarkStatus = isProfessor ? nextStatus : nextStatus === 'VALIDATED' ? 'COMPLETED' : nextStatus;
      await updateMarkMutation.mutateAsync({
        markId: mark.id,
        data: {
          mark_status: normalisedStatus,
          teacher_validated: teacherValidated,
        },
      });
    },
    [canEdit, isProfessor, updateMarkMutation],
  );

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
      title="Checklists do aluno"
      description="Revise o progresso por checklist e acompanhe o fluxo de submissão e validação."
      actions={
        <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-2 text-sm text-slate-600 shadow-sm">
          Média concluída: <span className="font-semibold text-slate-800">{average.toFixed(0)}%</span>
        </div>
      }
    >
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
        <aside className="w-full space-y-4 lg:w-64">
          <Link
            href={backHref}
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-sky-300 hover:text-sky-700"
          >
            ← Voltar à lista
          </Link>
          <div className="rounded-3xl border border-slate-200 bg-white/90 p-4 text-sm text-slate-600">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Aluno</p>
            <p className="mt-1 text-base font-semibold text-slate-800">{studentName(student)}</p>
            {latestUpdatedAt ? (
              <p className="mt-2 text-xs text-slate-500">Atualizado {formatDateTime(latestUpdatedAt)}</p>
            ) : null}
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white/90 p-4 text-sm text-slate-600">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Resumo dos objetivos</p>
            <ul className="mt-3 space-y-2 text-xs">
              {Object.entries(statusTotals).map(([key, value]) => (
                <li key={key} className="flex items-center justify-between gap-2">
                  <span className={`inline-flex items-center gap-2 rounded-full px-2 py-1 font-semibold ${MARK_STATUS_BADGE_CLASSES[key as MarkStatus]}`}>
                    {MARK_STATUS_LABELS[key as MarkStatus]}
                  </span>
                  <span>{value}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-slate-500">Total de itens: {totalMarks}</p>
          </div>
          {canEdit && classIdParam ? (
            <div className="rounded-3xl border border-slate-200 bg-white/90 p-4 text-sm text-slate-600">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Iniciar nova checklist</p>
              {availableTemplates.length ? (
                <ul className="mt-3 space-y-2">
                  {availableTemplates.map((template) => (
                    <li key={template.id}>
                      <button
                        type="button"
                        onClick={() => handleCreateStatus(template.id)}
                        className="w-full rounded-full border border-sky-500 px-3 py-1 text-xs font-semibold text-sky-600 transition hover:border-sky-600 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
                        disabled={createStatusMutation.isPending}
                      >
                        {template.name}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-xs text-slate-500">Não existem modelos disponíveis para esta turma.</p>
              )}
              {createStatusMutation.isError ? (
                <p className="mt-2 text-xs text-rose-600" role="alert">
                  {(createStatusMutation.error as Error).message}
                </p>
              ) : null}
            </div>
          ) : null}
        </aside>
        <div className="flex-1 space-y-4">
          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
              {(error as Error).message}
            </div>
          ) : studentStatuses.length ? (
            studentStatuses.map((status) => (
              <ChecklistStatusSection
                key={status.id}
                status={status}
                canEdit={canEdit}
                isProfessor={isProfessor}
                onUpdateMark={handleMarkUpdate}
              />
            ))
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
              Nenhuma checklist iniciada ainda.
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

interface ChecklistStatusSectionProps {
  status: ChecklistStatus;
  canEdit: boolean;
  isProfessor: boolean;
  onUpdateMark: (mark: ChecklistMark, nextStatus: MarkStatus) => Promise<void> | void;
}

function ChecklistStatusSection({ status, canEdit, isProfessor, onUpdateMark }: ChecklistStatusSectionProps) {
  const [notes, setNotes] = useState(status.student_notes ?? '');
  const [localError, setLocalError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [pendingSubmit, setPendingSubmit] = useState(false);
  const [markErrors, setMarkErrors] = useState<Record<number, string>>({});
  const [updatingMarkId, setUpdatingMarkId] = useState<number | null>(null);
  const { autosave } = useChecklistAutosave(status.id);
  const { submit } = useSubmitChecklist();
  const { state, percent, canSubmit, pendingMandatory } = useChecklistStateHelpers(status);

  useEffect(() => {
    setNotes(status.student_notes ?? '');
  }, [status.student_notes, status.id]);

  const handleNotesChange = useCallback(
    (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = event.target.value;
      setNotes(value);
      setLocalError(null);
      setSaving(true);
      const timeout = window.setTimeout(async () => {
        try {
          await autosave(value);
        } catch (autosaveError) {
          setLocalError(autosaveError instanceof Error ? autosaveError.message : 'Não foi possível guardar notas.');
        } finally {
          setSaving(false);
        }
      }, 600);
      return () => window.clearTimeout(timeout);
    },
    [autosave],
  );

  const handleSubmit = useCallback(async () => {
    try {
      setPendingSubmit(true);
      await submit(status.id);
    } catch (submitError) {
      setLocalError(submitError instanceof Error ? submitError.message : 'Não foi possível submeter a checklist.');
    } finally {
      setPendingSubmit(false);
    }
  }, [submit, status.id]);

  const handleMark = useCallback(
    async (mark: ChecklistMark, nextStatus: MarkStatus) => {
      setUpdatingMarkId(mark.id);
      setMarkErrors((prev) => {
        const next = { ...prev };
        delete next[mark.id];
        return next;
      });
      try {
        await onUpdateMark(mark, nextStatus);
      } catch (markError) {
        setMarkErrors((prev) => ({
          ...prev,
          [mark.id]: markError instanceof Error ? markError.message : 'Não foi possível atualizar o objetivo.',
        }));
      } finally {
        setUpdatingMarkId(null);
      }
    },
    [onUpdateMark],
  );

  const badgeTone = state === 'validated'
    ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
    : state === 'submitted'
      ? 'bg-sky-100 text-sky-700 border border-sky-200'
      : state === 'needs_revision'
        ? 'bg-amber-100 text-amber-700 border border-amber-200'
        : 'bg-slate-100 text-slate-700 border border-slate-200';

  return (
    <section className="space-y-4 rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold text-slate-800">{status.template?.name ?? 'Checklist'}</h2>
          <p className="text-xs text-slate-500">Estado atual: <span className={`rounded-full px-2 py-1 font-semibold ${badgeTone}`}>{stateLabel(state)}</span></p>
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>Concluído: {percent.toFixed(0)}%</p>
          {pendingMandatory > 0 ? (
            <p className="text-rose-600">Itens obrigatórios pendentes: {pendingMandatory}</p>
          ) : null}
        </div>
      </header>
      <textarea
        className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm leading-relaxed text-slate-700 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
        placeholder="Notas pessoais do aluno (autosave em segundos)."
        value={notes}
        onChange={handleNotesChange}
        disabled={!canEdit || state !== 'draft'}
      />
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
        <p>
          {saving
            ? 'A guardar…'
            : localError
              ? <span className="text-rose-600">{localError}</span>
              : 'Notas guardadas automaticamente.'}
        </p>
        {canEdit && state === 'draft' ? (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit || pendingSubmit}
            className="inline-flex items-center gap-2 rounded-full border border-emerald-500 px-4 py-1.5 text-sm font-semibold text-emerald-600 transition hover:border-emerald-600 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
          >
            {pendingSubmit ? 'A submeter…' : 'Submeter checklist'}
          </button>
        ) : null}
      </div>
      <ChecklistStatusCard
        status={status}
        canEdit={canEdit && state === 'draft'}
        onUpdateMark={handleMark}
        updatingMarkId={updatingMarkId}
        errorByMark={markErrors}
        allowedStatuses={isProfessor ? ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'VALIDATED'] : ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED']}
        isReadOnlyForMark={(mark) => Boolean(mark.teacher_validated)}
      />
    </section>
  );
}

function stateLabel(state?: ChecklistStatus['state']) {
  switch (state) {
    case 'submitted':
      return 'Submetida';
    case 'validated':
      return 'Validada';
    case 'needs_revision':
      return 'Com reparos';
    default:
      return 'Rascunho';
  }
}
