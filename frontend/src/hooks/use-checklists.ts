'use client';

import { useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuth } from '@/providers/auth-provider';
import type { ChecklistStatus, ChecklistMark, ChecklistTemplate } from '@/types/api';
import { extractResults } from '@/lib/utils';

type LVState = ChecklistStatus['state'];

interface CreateChecklistPayload {
  templateId: number;
  classId: number;
  notes?: string;
}

interface UpdateChecklistPayload {
  statusId: number;
  data: Partial<Pick<ChecklistStatus, 'state' | 'student_notes'>>;
}

interface UpdateMarkPayload {
  markId: number;
  data: Partial<Pick<ChecklistMark, 'mark_status' | 'teacher_validated' | 'comment'>>;
}

export function useChecklistTemplates() {
  const { fetchWithAuth, isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ['checklist-templates'],
    queryFn: async () => {
      const res = await fetchWithAuth('/checklists/templates');
      if (!res.ok) {
        throw new Error('Não foi possível obter os modelos de checklist.');
      }
      const body = await res.json();
      return extractResults<ChecklistTemplate>(body);
    },
    enabled: isAuthenticated,
  });
}

export function useChecklistStatuses(classId?: number | null) {
  const { fetchWithAuth, isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ['checklist-statuses', classId ?? null],
    queryFn: async () => {
      const query = classId ? `?student_class=${classId}` : '';
      const res = await fetchWithAuth(`/checklists/statuses${query}`);
      if (!res.ok) {
        throw new Error('Não foi possível obter as listas de verificação.');
      }
      const body = await res.json();
      return extractResults<ChecklistStatus>(body);
    },
    enabled: isAuthenticated,
  });
}

export function useCreateChecklistStatus() {
  const { fetchWithAuth } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ['checklist-statuses', 'create'],
    mutationFn: async ({ templateId, classId, notes }: CreateChecklistPayload) => {
      const res = await fetchWithAuth('/checklists/statuses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: templateId,
          student_class_id: classId,
          student_notes: notes ?? '',
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || 'Não foi possível iniciar a checklist.');
      }
      return body as ChecklistStatus;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['checklist-statuses'] });
      return data;
    },
  });
}

export function useUpdateChecklistStatus() {
  const { fetchWithAuth } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ['checklist-statuses', 'update'],
    mutationFn: async ({ statusId, data }: UpdateChecklistPayload) => {
      const res = await fetchWithAuth(`/checklists/statuses/${statusId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || 'Não foi possível atualizar a checklist.');
      }
      return body as ChecklistStatus;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['checklist-statuses'] });
      return data;
    },
  });
}

export function useUpdateChecklistMark() {
  const { fetchWithAuth } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ['checklist-marks', 'update'],
    mutationFn: async ({ markId, data }: UpdateMarkPayload) => {
      const res = await fetchWithAuth(`/checklists/marks/${markId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || 'Não foi possível atualizar o objetivo.');
      }
      return body as ChecklistMark;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['checklist-statuses'] });
      return data;
    },
  });
}

export function useChecklistStateHelpers(status?: ChecklistStatus | null) {
  const state: LVState = status?.state ?? 'draft';
  const percent = status?.percent_complete ?? 0;
  const marks = status?.marks ?? [];

  const pendingMandatory = marks.filter((mark) => {
    const isRequired = true; // placeholder: add flag when modelo tiver atributo
    const isDone = mark.mark_status === 'COMPLETED' || mark.mark_status === 'VALIDATED';
    return isRequired && !isDone;
  }).length;

  const canSubmit = state === 'draft' && pendingMandatory === 0;

  return {
    state,
    percent,
    pendingMandatory,
    canSubmit,
  };
}

export function useChecklistAutosave(statusId?: number) {
  const updateStatus = useUpdateChecklistStatus();

  const autosave = useCallback(
    async (notes: string) => {
      if (!statusId) return;
      await updateStatus.mutateAsync({ statusId, data: { student_notes: notes } });
    },
    [statusId, updateStatus],
  );

  return {
    autosave,
    saving: updateStatus.isPending,
    error: updateStatus.isError ? (updateStatus.error as Error)?.message : null,
  };
}

export function useSubmitChecklist() {
  const updateStatus = useUpdateChecklistStatus();

  const submit = useCallback(
    async (statusId: number) => {
      await updateStatus.mutateAsync({ statusId, data: { state: 'submitted' } });
    },
    [updateStatus],
  );

  return {
    submit,
    submitting: updateStatus.isPending,
    error: updateStatus.isError ? (updateStatus.error as Error)?.message : null,
  };
}
