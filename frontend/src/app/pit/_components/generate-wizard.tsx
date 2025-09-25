'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuth } from '@/providers/auth-provider';
import type { ClassSummary, IndividualPlan } from '@/types/api';

type ClassStudent = {
  id: number;
  first_name?: string;
  last_name?: string;
  email?: string;
  username?: string;
  name?: string;
};

function personDisplayName(person: ClassStudent | null | undefined) {
  if (!person) return '—';
  const first = typeof person.first_name === 'string' ? person.first_name : '';
  const last = typeof person.last_name === 'string' ? person.last_name : '';
  const combined = `${first} ${last}`.trim();
  if (combined) return combined;
  if (person.name) return person.name;
  if (person.email) return person.email;
  if (person.username) return person.username;
  return `Aluno #${person.id}`;
}

interface GeneratePitWizardProps {
  classes: ClassSummary[];
}

type FormState = {
  classId: string;
  studentId: string | null;
  targetDate: string;
};

export function GeneratePitWizard({ classes }: GeneratePitWizardProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { fetchWithAuth, user } = useAuth();
  const [step, setStep] = useState<'select-class' | 'confirm'>('select-class');
  const [formState, setFormState] = useState<FormState>({
    classId: classes[0]?.id ? String(classes[0].id) : '',
    studentId: null,
    targetDate: new Date().toISOString().slice(0, 10),
  });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const classId = Number(formState.classId);

  const studentsQuery = useQuery({
    queryKey: ['class-students', classId],
    queryFn: async () => {
      if (!classId) return [];
      const res = await fetchWithAuth(`/classes/${classId}`);
      if (!res.ok) throw new Error('Não foi possível carregar alunos da turma selecionada.');
      const data = await res.json();
      return (data.students as ClassStudent[]) || [];
    },
    enabled: Boolean(classId && user?.role !== 'aluno'),
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        student_class_id: Number(formState.classId),
        target_date: formState.targetDate,
      };
      if (user?.role !== 'aluno' && formState.studentId) {
        payload.student_id = Number(formState.studentId);
      }
      const res = await fetchWithAuth('/pit/plans/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Não foi possível gerar o PIT.');
      }
      return (await res.json()) as IndividualPlan;
    },
    onSuccess: (plan) => {
      queryClient.invalidateQueries({ queryKey: ['pit-plans'] });
      setErrorMessage(null);
      router.push(`/pit/${plan.id}/editar`);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Falha ao gerar o PIT.');
    },
  });

  const selectedClass = classes.find((item) => item.id === Number(formState.classId));
  const isProfessorOrAdmin = user?.role === 'professor' || user?.role === 'admin' || Boolean(user?.is_superuser);

  useEffect(() => {
    if (!isProfessorOrAdmin || formState.studentId) return;
    const fetchedStudents = studentsQuery.data;
    if (fetchedStudents && fetchedStudents.length > 0) {
      setFormState((prev) => ({ ...prev, studentId: String(fetchedStudents[0].id) }));
    }
  }, [isProfessorOrAdmin, formState.studentId, studentsQuery.data]);

  const students = studentsQuery.data ?? [];

  const handleNext = () => {
    if (!formState.classId) {
      setErrorMessage('Selecione uma turma.');
      return;
    }
    if (isProfessorOrAdmin && !formState.studentId) {
      setErrorMessage('Escolha o aluno para quem deseja gerar o PIT.');
      return;
    }
    setStep('confirm');
    setErrorMessage(null);
  };

  const handleBack = () => {
    setStep('select-class');
  };

  return (
    <div className="space-y-6">
      {step === 'select-class' ? (
        <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800">Selecionar turma e semana</h2>
          <p className="mt-1 text-sm text-slate-600">Escolha a turma e o intervalo da semana que pretende planear.</p>
          <div className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-700" htmlFor="pit-class">
              Turma
            </label>
            <select
              id="pit-class"
              value={formState.classId}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  classId: event.target.value,
                  studentId: null,
                }))
              }
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            >
              {classes.map((turma) => (
                <option key={turma.id} value={turma.id}>
                  {turma.name}
                </option>
              ))}
            </select>

            {isProfessorOrAdmin ? (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700" htmlFor="pit-student">
                  Aluno
                </label>
                <select
                  id="pit-student"
                  value={formState.studentId ?? ''}
                  onChange={(event) => setFormState((prev) => ({ ...prev, studentId: event.target.value || null }))}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                  disabled={studentsQuery.isLoading}
                >
                  <option value="">Selecionar aluno…</option>
                  {students.map((studentOption) => (
                    <option key={studentOption.id} value={studentOption.id}>
                      {personDisplayName(studentOption)}
                    </option>
                  ))}
                </select>
                {studentsQuery.isError ? (
                  <p className="text-xs text-rose-600">Não foi possível carregar os alunos desta turma.</p>
                ) : null}
              </div>
            ) : null}

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700" htmlFor="pit-target-date">
                Data de referência da semana
              </label>
              <input
                id="pit-target-date"
                type="date"
                value={formState.targetDate}
                onChange={(event) => setFormState((prev) => ({ ...prev, targetDate: event.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
              />
            </div>
          </div>
          {errorMessage ? (
            <p className="mt-4 text-sm text-rose-600" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={handleNext}
              className="inline-flex items-center rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700"
            >
              Continuar
            </button>
          </div>
        </section>
      ) : null}

      {step === 'confirm' ? (
        <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800">Confirmar geração do PIT</h2>
          <p className="mt-1 text-sm text-slate-600">Revise os dados antes de gerar o plano.</p>
          <dl className="mt-6 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-[0.3em] text-slate-500">Turma</dt>
              <dd className="mt-1 font-medium">{selectedClass?.name ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-[0.3em] text-slate-500">Data de referência</dt>
              <dd className="mt-1 font-medium">{formState.targetDate}</dd>
            </div>
            {isProfessorOrAdmin ? (
              <div>
                <dt className="text-xs uppercase tracking-[0.3em] text-slate-500">Aluno</dt>
                <dd className="mt-1 font-medium">
                  {personDisplayName(students.find((item) => String(item.id) === formState.studentId))}
                </dd>
              </div>
            ) : null}
          </dl>
          {errorMessage ? (
            <p className="mt-4 text-sm text-rose-600" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <div className="mt-6 flex justify-between">
            <button
              type="button"
              onClick={handleBack}
              className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-400"
              disabled={generateMutation.isPending}
            >
              Voltar
            </button>
            <button
              type="button"
              onClick={() => generateMutation.mutate()}
              className="inline-flex items-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-emerald-300"
              disabled={generateMutation.isPending}
            >
              {generateMutation.isPending ? 'A gerar…' : 'Gerar PIT'}
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
