'use client';

import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { notFound, useParams } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import type { PlanDetail, PlanSection, PlanTask } from '@/types/api';

type TaskState = Exclude<PlanTask['state'], undefined>;

const PLAN_STATUS_LABELS: Record<string, string> = {
  draft: 'Rascunho',
  submitted: 'Submetido',
  approved: 'Aprovado',
  concluded: 'Concluído',
  evaluated: 'Avaliado',
};

const TASK_STATE_FALLBACK: TaskState = 'pending';
const taskStateLabels: Record<TaskState, string> = {
  pending: 'Pendente',
  in_progress: 'Em curso',
  done: 'Concluída',
  validated: 'Validada',
};

const suggestionOriginLabels: Record<string, string> = {
  template: 'Modelo',
  council: 'Conselho',
  pending: 'Pendência',
  manual: 'Manual',
};

interface EditableTask extends PlanTask {
  order: number;
}

export default function PlanEditorPage() {
  const params = useParams<{ planId: string }>();
  const planId = Number(params?.planId ?? '');
  if (!planId) {
    notFound();
  }

  const { fetchWithAuth, user } = useAuth();
  const queryClient = useQueryClient();
  const [localTasks, setLocalTasks] = useState<EditableTask[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<number | null>(null);
  const [draggedTaskId, setDraggedTaskId] = useState<number | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [generalObjectives, setGeneralObjectives] = useState('');
  const [lastSavedObjectives, setLastSavedObjectives] = useState('');
  const [autosaveStatus, setAutosaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const autosaveTimeoutRef = useRef<number | null>(null);
  const resetStatusTimeoutRef = useRef<number | null>(null);
  const [teacherEvaluation, setTeacherEvaluation] = useState('');
  const [teacherEvalStatus, setTeacherEvalStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const teacherStatusTimeoutRef = useRef<number | null>(null);

  const planQuery = useQuery({
    queryKey: ['pit-plan', planId],
    queryFn: async () => {
      const res = await fetchWithAuth(`/pit/plans/${planId}`);
      if (!res.ok) {
        if (res.status === 404) {
          notFound();
        }
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Não foi possível carregar o PIT.');
      }
      const data = (await res.json()) as PlanDetail;
      return data;
    },
  });

  const plan = planQuery.data;
  const role = user?.role;
  const currentUserId = user?.id != null ? Number(user.id) : null;
  const planStudentId = plan?.student?.id != null ? Number(plan.student.id) : null;
  const isProfessor = Boolean(user && (role === 'professor' || role === 'admin' || user.is_superuser));
  const isPlanOwner = Boolean(currentUserId != null && planStudentId != null && planStudentId === currentUserId);
  const canEditPlan = Boolean(isPlanOwner && plan && (plan.status === 'draft' || plan.status === 'submitted'));
  const sections = useMemo(() => plan?.sections ?? [], [plan?.sections]);
  const suggestions = plan?.suggestions ?? [];

  useEffect(() => {
    if (plan?.tasks) {
      const sorted = [...plan.tasks]
        .map((task) => ({ ...task, order: task.order ?? 0 }))
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0)) as EditableTask[];
      setLocalTasks(sorted);
    }
  }, [plan?.tasks]);

  useEffect(() => {
    if (!plan) return;
    const initialObjectives = plan.general_objectives ?? '';
    setGeneralObjectives(initialObjectives);
    setLastSavedObjectives(initialObjectives);
    setAutosaveStatus('idle');
    if (teacherStatusTimeoutRef.current) {
      window.clearTimeout(teacherStatusTimeoutRef.current);
    }
    const initialTeacher = plan.teacher_evaluation ?? '';
    setTeacherEvaluation(initialTeacher);
    setTeacherEvalStatus('idle');
  }, [plan]);

  useEffect(() => {
    if (!canEditPlan) {
      if (autosaveTimeoutRef.current) {
        window.clearTimeout(autosaveTimeoutRef.current);
      }
      if (resetStatusTimeoutRef.current) {
        window.clearTimeout(resetStatusTimeoutRef.current);
      }
      setAutosaveStatus('idle');
    }
  }, [canEditPlan]);

  useEffect(() => {
    return () => {
      if (autosaveTimeoutRef.current) {
        window.clearTimeout(autosaveTimeoutRef.current);
      }
      if (resetStatusTimeoutRef.current) {
        window.clearTimeout(resetStatusTimeoutRef.current);
      }
      if (teacherStatusTimeoutRef.current) {
        window.clearTimeout(teacherStatusTimeoutRef.current);
      }
    };
  }, []);

  const createTaskMutation = useMutation({
    mutationFn: async (payload: { description: string; subject: string | null; state: TaskState; order: number }) => {
      const res = await fetchWithAuth('/pit/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: planId,
          description: payload.description,
          subject: payload.subject ?? '',
          state: payload.state,
          order: payload.order,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Não foi possível criar a tarefa.');
      }
      return (await res.json()) as PlanTask;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pit-plan', planId] });
      setErrorMessage(null);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Erro ao criar tarefa.');
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<PlanTask> }) => {
      const res = await fetchWithAuth(`/pit/tasks/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Não foi possível atualizar a tarefa.');
      }
      return (await res.json()) as PlanTask;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pit-plan', planId] });
      setErrorMessage(null);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Erro ao atualizar tarefa.');
    },
  });

  const deleteTaskMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetchWithAuth(`/pit/tasks/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok && res.status !== 204) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Não foi possível remover a tarefa.');
      }
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pit-plan', planId] });
      setErrorMessage(null);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Erro ao remover tarefa.');
    },
  });

  const updatePlanMutation = useMutation({
    mutationFn: async (payload: Partial<PlanDetail>) => {
      const res = await fetchWithAuth(`/pit/plans/${planId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || 'Não foi possível guardar o PIT.');
      }
      return (await res.json()) as PlanDetail;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['pit-plan', planId], data);
      setLastSavedObjectives(data.general_objectives ?? '');
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Erro ao guardar o PIT.');
    },
  });

  const teacherEvaluationMutation = useMutation({
    mutationFn: async (payload: { teacher_evaluation: string }) => {
      const res = await fetchWithAuth(`/pit/plans/${planId}/teacher-evaluation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || 'Não foi possível guardar a devolução.');
      }
      return (await res.json()) as PlanDetail;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['pit-plan', planId], data);
      setTeacherEvaluation(data.teacher_evaluation ?? '');
      setErrorMessage(null);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Erro ao guardar a devolução.');
    },
  });

  const planStatus = plan?.status ?? 'draft';
  const canSubmitTeacherEvaluation = Boolean(
    isProfessor && plan && !['draft', 'submitted'].includes(planStatus),
  );
  const teacherEvaluationBlockedMessage =
    isProfessor && !canSubmitTeacherEvaluation
      ? 'Aguarde o aluno concluir ou autoavaliar o PIT antes de registar a devolução.'
      : null;
  const hasSelfEvaluation = Boolean((plan?.self_evaluation ?? '').trim());
  const hasTeacherEvaluation = Boolean((plan?.teacher_evaluation ?? '').trim());
  const teacherActionDisabled =
    !canSubmitTeacherEvaluation || teacherEvaluationMutation.isPending;
  const teacherBadgeDisabled = !isProfessor || !canSubmitTeacherEvaluation;

  const orderedTasks = useMemo(() => {
    return [...localTasks].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
  }, [localTasks]);

  const tasksBySection = useMemo(() => {
    if (!sections.length) {
      return { none: orderedTasks };
    }
    const map: Record<string, EditableTask[]> = {};
    sections.forEach((section) => {
      map[String(section.id)] = orderedTasks.filter((task) => {
        const code = section.area_code ?? '';
        if (!code) {
          return (task.subject ?? '') === '';
        }
        return (task.subject ?? '') === code;
      });
    });
    const withoutSection = orderedTasks.filter((task) => {
      if (!sections.length) return true;
      return !sections.some((section) => (section.area_code ?? '') === (task.subject ?? ''));
    });
    map['__unassigned__'] = withoutSection;
    return map;
  }, [orderedTasks, sections]);

  const handleTaskSubmit = async (
    event: FormEvent<HTMLFormElement>,
    section: PlanSection | null,
  ) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const description = String(form.get('description') ?? '').trim();
    if (!description) {
      setErrorMessage('Preencha a descrição da tarefa.');
      return;
    }
    const state = String(form.get('state') ?? TASK_STATE_FALLBACK) as TaskState;
    const subject = section?.area_code ?? String(form.get('subject') ?? '').trim() || null;
    await createTaskMutation.mutateAsync({
      description,
      state,
      subject,
      order: orderedTasks.length + 1,
    });
    event.currentTarget.reset();
  };

  const persistOrder = async (tasks: EditableTask[]) => {
    try {
      await Promise.all(
        tasks.map((task, index) =>
          fetchWithAuth(`/pit/tasks/${task.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: index + 1, subject: task.subject ?? '' }),
          }).then((res) => {
            if (!res.ok) {
              throw new Error('Falha ao atualizar a ordem.');
            }
          }),
        ),
      );
      queryClient.invalidateQueries({ queryKey: ['pit-plan', planId] });
      setErrorMessage(null);
    } catch {
      setErrorMessage('Não foi possível reordenar as tarefas.');
      queryClient.invalidateQueries({ queryKey: ['pit-plan', planId] });
    }
  };

  const reorderTasksLocally = (
    tasks: EditableTask[],
    draggedId: number,
    targetSectionId: number | '__unassigned__',
    insertBeforeId: number | null,
  ): EditableTask[] | null => {
    const list = tasks.map((task) => ({ ...task }));
    const draggedIndex = list.findIndex((task) => task.id === draggedId);
    if (draggedIndex === -1) {
      return null;
    }
    const draggedTask = { ...list[draggedIndex] };
    list.splice(draggedIndex, 1);

    let insertIndex = list.length;
    if (insertBeforeId) {
      const idx = list.findIndex((task) => task.id === insertBeforeId);
      insertIndex = idx >= 0 ? idx : list.length;
    }

    if (targetSectionId === '__unassigned__') {
      draggedTask.subject = '';
    } else {
      const section = sections.find((item) => item.id === targetSectionId);
      draggedTask.subject = section?.area_code ?? '';
    }

    list.splice(insertIndex, 0, draggedTask);
    return list.map((task, index) => ({ ...task, order: index + 1 }));
  };

  const handleReorder = async (
    draggedId: number,
    targetSectionId: number | '__unassigned__',
    insertBeforeId: number | null,
  ) => {
    const nextTasks = reorderTasksLocally(localTasks, draggedId, targetSectionId, insertBeforeId);
    if (!nextTasks) {
      return;
    }
    setLocalTasks(nextTasks);
    await persistOrder(nextTasks);
  };

  const handleDragStart = (taskId: number) => {
    setDraggedTaskId(taskId);
  };

  const handleDropOnSection = async (
    section: PlanSection | null,
    insertBeforeId: number | null,
  ) => {
    if (!draggedTaskId) return;
    const sectionKey = section ? section.id : '__unassigned__';
    await handleReorder(draggedTaskId, sectionKey, insertBeforeId);
    setDraggedTaskId(null);
  };

  const handleExportPdf = async () => {
    try {
      setIsExporting(true);
      const res = await fetchWithAuth(`/pit/plans/${planId}/export-pdf`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || 'Não foi possível exportar o PIT.');
      }
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const disposition = res.headers.get('Content-Disposition') ?? '';
      const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
      const filename = filenameMatch?.[1] ?? `pit-${planId}.pdf`;
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      setErrorMessage(null);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Erro ao exportar o PIT.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleObjectivesChange = (value: string) => {
    setGeneralObjectives(value);
    if (!plan || !canEditPlan) {
      return;
    }

    if (autosaveTimeoutRef.current) {
      window.clearTimeout(autosaveTimeoutRef.current);
    }
    if (resetStatusTimeoutRef.current) {
      window.clearTimeout(resetStatusTimeoutRef.current);
    }

    if (value === lastSavedObjectives) {
      setAutosaveStatus('idle');
      return;
    }

    setAutosaveStatus('saving');

    autosaveTimeoutRef.current = window.setTimeout(async () => {
      try {
        const updated = await updatePlanMutation.mutateAsync({ general_objectives: value });
        setLastSavedObjectives(updated.general_objectives ?? value);
        setAutosaveStatus('saved');
        resetStatusTimeoutRef.current = window.setTimeout(() => {
          setAutosaveStatus('idle');
        }, 2000);
        setErrorMessage(null);
      } catch (error) {
        setAutosaveStatus('error');
        if (error instanceof Error) {
          setErrorMessage(error.message);
        }
      }
    }, 800);
  };

  const handleTeacherEvaluationSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!plan || !canSubmitTeacherEvaluation) {
      return;
    }
    if (teacherStatusTimeoutRef.current) {
      window.clearTimeout(teacherStatusTimeoutRef.current);
    }
    setTeacherEvalStatus('saving');
    try {
      const updated = await teacherEvaluationMutation.mutateAsync({
        teacher_evaluation: teacherEvaluation,
      });
      setTeacherEvalStatus('saved');
      setTeacherEvaluation(updated.teacher_evaluation ?? teacherEvaluation);
      teacherStatusTimeoutRef.current = window.setTimeout(() => {
        setTeacherEvalStatus('idle');
      }, 2000);
    } catch {
      setTeacherEvalStatus('error');
      teacherStatusTimeoutRef.current = window.setTimeout(() => {
        setTeacherEvalStatus('idle');
      }, 3000);
    }
  };

  if (planQuery.isLoading) {
    return (
      <AppShell title="Editar PIT" description="A carregar o plano…">
        <p className="text-sm text-slate-500">A carregar plano…</p>
      </AppShell>
    );
  }

  if (planQuery.isError || !plan) {
    notFound();
  }

  const studentName = formatStudentName(plan.student);

  return (
    <AppShell
      title={`Editar PIT — ${plan?.period_label ?? ''}`}
      description="Organize as tarefas por área, atualize estados e registe evidências do trabalho."
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleExportPdf}
            disabled={isExporting}
            className="inline-flex items-center rounded-full border border-sky-500 px-4 py-2 text-sm font-semibold text-sky-600 transition hover:border-sky-600 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
          >
            {isExporting ? 'A exportar…' : 'Exportar PDF'}
          </button>
          <Link
            href="/pit"
            className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-400"
          >
            Voltar à lista
          </Link>
        </div>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,3fr)_minmax(260px,1fr)] xl:items-start">
        <div className="space-y-6">
          <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Turma</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">{plan?.student_class?.name ?? '—'}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Aluno</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">{studentName}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Período</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">{plan?.period_label}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Estado</p>
                <p className="mt-1 text-sm font-semibold text-slate-700">
                  {PLAN_STATUS_LABELS[String(plan?.status ?? '')] ?? plan?.status ?? '—'}
                </p>
              </div>
            </div>
            {plan?.template ? (
              <p className="mt-4 text-xs text-slate-500">
                Modelo aplicado: {plan.template.name} (versão {plan.template.version})
              </p>
            ) : null}
            <div className="mt-6 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500" htmlFor="general-objectives">
                  Objetivos gerais
                </label>
                <AutosaveStatusBadge status={autosaveStatus} disabled={!canEditPlan} />
              </div>
              <textarea
                id="general-objectives"
                className="min-h-[120px] w-full rounded-lg border border-slate-300 px-3 py-2 text-sm leading-relaxed focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:bg-slate-100"
                value={generalObjectives}
                onChange={(event) => handleObjectivesChange(event.target.value)}
                placeholder="Resumo dos objetivos para a semana."
                disabled={!canEditPlan}
              />
              {!canEditPlan ? (
                <p className="text-xs text-slate-500">O plano encontra-se bloqueado para edição neste estado.</p>
              ) : null}
            </div>
          </section>

          {sections.map((section) => (
          <PlanSectionCard
            key={section.id}
            section={section}
            tasks={tasksBySection[String(section.id)] ?? []}
            onAddTask={handleTaskSubmit}
            onUpdateTask={updateTaskMutation.mutateAsync}
            onDeleteTask={deleteTaskMutation.mutateAsync}
            onDragStart={handleDragStart}
            onDropTask={handleDropOnSection}
            onDragEnd={() => setDraggedTaskId(null)}
            setActiveSection={setActiveSectionId}
            activeSectionId={activeSectionId}
            canEdit={canEditPlan}
          />
        ))}

        <PlanSectionCard
          section={null}
          tasks={tasksBySection['__unassigned__'] ?? []}
          onAddTask={handleTaskSubmit}
          onUpdateTask={updateTaskMutation.mutateAsync}
          onDeleteTask={deleteTaskMutation.mutateAsync}
          onDragStart={handleDragStart}
          onDropTask={handleDropOnSection}
          onDragEnd={() => setDraggedTaskId(null)}
          setActiveSection={setActiveSectionId}
          activeSectionId={activeSectionId}
          canEdit={canEditPlan}
        />
        </div>

        <aside className="space-y-6">
          {suggestions.length ? (
            <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
              <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Sugestões importadas</h3>
              <ul className="mt-4 space-y-3 text-sm text-slate-600">
                {suggestions.map((suggestion) => (
                  <li key={suggestion.id} className="rounded-2xl border border-slate-200 bg-slate-50/80 px-3 py-2">
                    <p className="font-medium text-slate-800">{suggestion.text}</p>
                    <p className="text-xs text-slate-500">
                      Origem: {suggestionOriginLabels[suggestion.origin] ?? suggestion.origin}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {(hasSelfEvaluation || isProfessor || hasTeacherEvaluation) ? (
            <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Autoavaliação & devolução</h3>
                <AutosaveStatusBadge status={teacherEvalStatus} disabled={teacherBadgeDisabled} />
              </div>
              <div className="mt-4 space-y-3 text-sm text-slate-700">
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Autoavaliação do aluno</p>
                  {hasSelfEvaluation ? (
                    <p className="mt-2 leading-relaxed text-slate-700">{plan?.self_evaluation}</p>
                  ) : (
                    <p className="mt-2 text-sm text-slate-500">Sem registo de autoavaliação ainda.</p>
                  )}
                </div>

                {isProfessor ? (
                  <form className="space-y-3" onSubmit={handleTeacherEvaluationSubmit}>
                    <div>
                      <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500" htmlFor="teacher-evaluation">
                        Devolução do professor
                      </label>
                      <textarea
                        id="teacher-evaluation"
                        value={teacherEvaluation}
                        onChange={(event) => setTeacherEvaluation(event.target.value)}
                        className="mt-2 min-h-[120px] w-full rounded-lg border border-slate-300 px-3 py-2 text-sm leading-relaxed focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:bg-slate-100"
                        placeholder="Ex.: Síntese do acompanhamento, recomendações para a semana seguinte, próximos passos."
                        disabled={teacherActionDisabled}
                      />
                    </div>
                    {teacherEvaluationBlockedMessage ? (
                      <p className="text-xs text-slate-500">{teacherEvaluationBlockedMessage}</p>
                    ) : null}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={teacherActionDisabled}
                        className="inline-flex items-center rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                      >
                        {teacherEvalStatus === 'saving'
                          ? 'A guardar…'
                          : hasTeacherEvaluation
                            ? 'Atualizar devolução'
                            : 'Guardar devolução'}
                      </button>
                    </div>
                  </form>
                ) : hasTeacherEvaluation ? (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Feedback do professor</p>
                    <p className="mt-2 leading-relaxed text-emerald-800">{plan?.teacher_evaluation}</p>
                  </div>
                ) : null}
              </div>
            </section>
          ) : null}

          {errorMessage ? (
            <div className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700" role="alert">
              {errorMessage}
            </div>
          ) : null}
        </aside>
      </div>
    </AppShell>
  );
}

interface PlanSectionCardProps {
  section: PlanSection | null;
  tasks: EditableTask[];
  onAddTask: (event: FormEvent<HTMLFormElement>, section: PlanSection | null) => Promise<void> | void;
  onUpdateTask: (input: { id: number; data: Partial<PlanTask> }) => Promise<PlanTask>;
  onDeleteTask: (id: number) => Promise<number>;
  onDragStart: (taskId: number) => void;
  onDropTask: (section: PlanSection | null, insertBeforeId: number | null) => Promise<void>;
  onDragEnd: () => void;
  setActiveSection: (id: number | null) => void;
  activeSectionId: number | null;
  canEdit: boolean;
}

function PlanSectionCard({
  section,
  tasks,
  onAddTask,
  onUpdateTask,
  onDeleteTask,
  onDragStart,
  onDropTask,
  onDragEnd,
  setActiveSection,
  activeSectionId,
  canEdit,
}: PlanSectionCardProps) {
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    if (!canEdit) {
      event.preventDefault();
      return;
    }
    await onAddTask(event, section);
  };

  const handleDrop = async (taskId: number | null) => {
    if (!canEdit) return;
    await onDropTask(section, taskId);
  };

  const title = section ? section.title : 'Tarefas sem secção';
  const areaLabel = section?.area_code ? `Área: ${section.area_code}` : 'Sem área definida';

  const isActiveSection = canEdit && activeSectionId === section?.id;

  return (
    <section
      className={`rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm ${
        isActiveSection ? 'ring-2 ring-sky-200' : ''
      }`}
      onDragOver={
        canEdit
          ? (event) => {
              event.preventDefault();
              setActiveSection(section?.id ?? null);
            }
          : undefined
      }
      onDrop={
        canEdit
          ? async (event) => {
              event.preventDefault();
              const draggedId = Number(event.dataTransfer.getData('text/plain'));
              if (draggedId && tasks.every((task) => task.id !== draggedId)) {
                await handleDrop(null);
              }
              setActiveSection(null);
              onDragEnd();
            }
          : undefined
      }
      onDragLeave={
        canEdit
          ? () => {
              setActiveSection(null);
              onDragEnd();
            }
          : undefined
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{areaLabel}</p>
        </div>
      </div>
      <ul className="mt-4 space-y-3">
        {tasks.length ? (
          tasks.map((task) => (
            <li
              key={task.id}
              draggable={canEdit}
              onDragStart={
                canEdit
                  ? (event) => {
                      event.dataTransfer.setData('text/plain', String(task.id));
                      onDragStart(task.id);
                    }
                  : undefined
              }
              onDrop={
                canEdit
                  ? async (event) => {
                      event.preventDefault();
                      const draggedId = Number(event.dataTransfer.getData('text/plain'));
                      if (draggedId && draggedId !== task.id) {
                        await handleDrop(task.id);
                      }
                      setActiveSection(null);
                    }
                  : undefined
              }
              onDragOver={canEdit ? (event) => event.preventDefault() : undefined}
              onDragEnd={canEdit ? onDragEnd : undefined}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-800">{task.description}</p>
                  {task.subject ? (
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{task.subject}</p>
                  ) : null}
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
                    {taskStateLabels[(task.state ?? TASK_STATE_FALLBACK) as TaskState]}
                  </span>
                  {canEdit ? (
                    <>
                      <button
                        type="button"
                        onClick={() => setExpandedTaskId((prev) => (prev === task.id ? null : task.id))}
                        className="inline-flex items-center rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-400"
                      >
                        {expandedTaskId === task.id ? 'Fechar' : 'Editar'}
                      </button>
                      <button
                        type="button"
                        onClick={() => onDeleteTask(task.id)}
                        className="inline-flex items-center rounded-full border border-rose-200 px-3 py-1 text-xs font-semibold text-rose-600 transition hover:border-rose-300"
                      >
                        Remover
                      </button>
                    </>
                  ) : null}
                </div>
              </div>
              {task.teacher_feedback ? (
                <p className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                  Feedback docente: {task.teacher_feedback}
                </p>
              ) : null}
              {canEdit && expandedTaskId === task.id ? (
                <TaskEditForm
                  task={task}
                  section={section}
                  onSave={async (payload) => {
                    await onUpdateTask({ id: task.id, data: payload });
                    setExpandedTaskId(null);
                  }}
                />
              ) : null}
            </li>
          ))
        ) : (
          <li className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-4 text-sm text-slate-600">
            Nenhuma tarefa registada nesta secção.
          </li>
        )}
      </ul>
      <form className="mt-6 space-y-3" onSubmit={handleSubmit}>
        {canEdit ? (
          <>
            <div>
              <label htmlFor={`description-${section ? section.id : 'none'}`} className="text-sm font-medium text-slate-700">
                Nova tarefa
              </label>
              <input
                id={`description-${section ? section.id : 'none'}`}
                name="description"
                type="text"
                placeholder="Descrição da tarefa"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                required
              />
            </div>
            {!section?.area_code ? (
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor={`subject-${section ? section.id : 'none'}`}>
                  Área/Disciplina (opcional)
                </label>
                <input
                  id={`subject-${section ? section.id : 'none'}`}
                  name="subject"
                  type="text"
                  placeholder="Ex.: Matemática"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                />
              </div>
            ) : null}
            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor={`state-${section ? section.id : 'none'}`}>
                Estado
              </label>
              <select
                id={`state-${section ? section.id : 'none'}`}
                name="state"
                defaultValue={TASK_STATE_FALLBACK}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
              >
                {Object.entries(taskStateLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                Adicionar tarefa
              </button>
            </div>
          </>
        ) : null}
      </form>
    </section>
  );
}

interface TaskEditFormProps {
  task: EditableTask;
  section: PlanSection | null;
  onSave: (payload: Partial<PlanTask>) => Promise<PlanTask>;
}

function TaskEditForm({ task, section, onSave }: TaskEditFormProps) {
  const [formState, setFormState] = useState({
    description: task.description ?? '',
    subject: task.subject ?? section?.area_code ?? '',
    state: (task.state ?? TASK_STATE_FALLBACK) as TaskState,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await onSave({
        description: formState.description,
        subject: formState.subject,
        state: formState.state,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="mt-4 space-y-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
          Descrição
        </label>
        <input
          type="text"
          value={formState.description}
          onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
          required
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
          Área/Disciplina
        </label>
        <input
          type="text"
          value={formState.subject}
          onChange={(event) => setFormState((prev) => ({ ...prev, subject: event.target.value }))}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
          Estado
        </label>
        <select
          value={formState.state}
          onChange={(event) => setFormState((prev) => ({ ...prev, state: event.target.value as TaskState }))}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
        >
          {Object.entries(taskStateLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex justify-end">
        <button
          type="submit"
          className="inline-flex items-center rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-sky-300"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'A guardar…' : 'Guardar alterações'}
        </button>
      </div>
    </form>
  );
}

function formatStudentName(student: PlanDetail['student'] | undefined) {
  if (!student) return '—';
  const firstNameField = Object.prototype.hasOwnProperty.call(student, 'first_name')
    ? (student as Record<string, unknown>).first_name
    : undefined;
  const lastNameField = Object.prototype.hasOwnProperty.call(student, 'last_name')
    ? (student as Record<string, unknown>).last_name
    : undefined;
  const fullName = `${typeof firstNameField === 'string' ? firstNameField : ''} ${
    typeof lastNameField === 'string' ? lastNameField : ''
  }`.trim();
  if (fullName) return fullName;
  return student.email ?? student.username ?? '—';
}

interface AutosaveStatusBadgeProps {
  status: 'idle' | 'saving' | 'saved' | 'error';
  disabled?: boolean;
}

function AutosaveStatusBadge({ status, disabled }: AutosaveStatusBadgeProps) {
  if (disabled) {
    return <span className="inline-flex items-center rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">Só leitura</span>;
  }

  const variants: Record<AutosaveStatusBadgeProps['status'], { label: string; className: string }> = {
    idle: {
      label: 'Tudo guardado',
      className: 'border-slate-200 text-slate-500',
    },
    saving: {
      label: 'A guardar…',
      className: 'border-sky-300 text-sky-600',
    },
    saved: {
      label: 'Alterações guardadas',
      className: 'border-emerald-300 text-emerald-600',
    },
    error: {
      label: 'Erro ao guardar',
      className: 'border-rose-300 text-rose-600',
    },
  };

  const { label, className } = variants[status];

  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] ${className} ${status === 'saving' ? 'animate-pulse' : ''}`}>
      {label}
    </span>
  );
}
