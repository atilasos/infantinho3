'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { notFound, useParams } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';
import type {
  AppUser,
  ClassSummary,
  DiaryActiveResponse,
  DiaryColumnResponse,
  DiaryEntryResponse,
  DiarySessionResponse,
} from '@/types/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  try {
    return new Intl.DateTimeFormat('pt-PT', {
      dateStyle: 'medium',
      timeStyle: undefined,
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function formatDateTime(value?: string | null) {
  if (!value) return '';
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

function authorName(author?: AppUser | null) {
  if (!author) return 'Sem autor';
  const name = `${author.first_name ?? ''} ${author.last_name ?? ''}`.trim();
  return name || author.email || author.username || 'Sem autor';
}

export default function ClassDiaryPage() {
  const params = useParams<{ classId: string }>();
  const classId = params?.classId;

  if (!classId) {
    notFound();
  }

  const queryClient = useQueryClient();
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['class-diary', classId],
    queryFn: async () => {
      const res = await fetchWithAuth(`/classes/${classId}/diary/active`);
      if (res.status === 404) {
        notFound();
      }
      if (!res.ok) {
        throw new Error('Não foi possível carregar o diário da turma.');
      }
      const body: DiaryActiveResponse = await res.json();
      return body;
    },
    enabled: isAuthenticated,
  });

  const sessionsQuery = useQuery({
    queryKey: ['class-diary-sessions', classId],
    queryFn: async () => {
      const res = await fetchWithAuth(`/classes/${classId}/diary/sessions`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail || 'Não foi possível listar os períodos.';
        throw new Error(detail);
      }
      const body: DiarySessionResponse[] = await res.json();
      return body;
    },
    enabled: isAuthenticated && Boolean(data?.can_moderate),
  });

  const sessionDetailQuery = useQuery({
    queryKey: ['class-diary-session', classId, selectedSessionId],
    queryFn: async () => {
      if (!selectedSessionId) {
        return null;
      }
      const res = await fetchWithAuth(`/classes/${classId}/diary/sessions/${selectedSessionId}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail || 'Não foi possível carregar o diário selecionado.';
        throw new Error(detail);
      }
      const body: DiaryActiveResponse = await res.json();
      return body;
    },
    enabled:
      isAuthenticated &&
      Boolean(selectedSessionId && selectedSessionId !== (data?.session?.id ?? null)),
  });

  const activeSessionId = data?.session?.id ?? null;

  useEffect(() => {
    if (activeSessionId && selectedSessionId === null) {
      setSelectedSessionId(activeSessionId);
    }
  }, [activeSessionId, selectedSessionId]);

  useEffect(() => {
    if (!selectedSessionId && sessionsQuery.data && sessionsQuery.data.length > 0) {
      setSelectedSessionId(sessionsQuery.data[0].id);
    }
  }, [selectedSessionId, sessionsQuery.data]);

  const addEntryMutation = useMutation({
    mutationFn: async ({ column, content }: { column: string; content: string }) => {
      const res = await fetchWithAuth(`/classes/${classId}/diary/entries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ column, content }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail || 'Não foi possível adicionar a entrada.';
        throw new Error(detail);
      }
      return res.json() as Promise<DiaryEntryResponse>;
    },
    onSuccess: (_entry, variables) => {
      setDrafts((prev) => ({ ...prev, [variables.column]: '' }));
      queryClient.invalidateQueries({ queryKey: ['class-diary', classId] });
      queryClient.invalidateQueries({ queryKey: ['class-diary-session', classId, selectedSessionId] });
      setErrorMessage(null);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(mutationError instanceof Error ? mutationError.message : 'Erro ao adicionar entrada.');
    },
  });

  const startSessionMutation = useMutation({
    mutationFn: async () => {
      const res = await fetchWithAuth(`/classes/${classId}/diary/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail || 'Não foi possível iniciar um novo período.';
        throw new Error(detail);
      }
      return res.json() as Promise<DiaryActiveResponse>;
    },
    onSuccess: (payload) => {
      queryClient.invalidateQueries({ queryKey: ['class-diary', classId] });
      queryClient.invalidateQueries({ queryKey: ['class-diary-sessions', classId] });
      setSelectedSessionId(payload.session?.id ?? null);
      setErrorMessage(null);
    },
    onError: (mutationError: unknown) => {
      setErrorMessage(
        mutationError instanceof Error ? mutationError.message : 'Não foi possível iniciar um novo período.',
      );
    },
  });

  const handleSubmit = async (event: FormEvent<HTMLFormElement>, column: string) => {
    event.preventDefault();
    if (!sessionData || sessionData.session?.status !== 'ACTIVE') {
      setErrorMessage('Só é possível registar durante o período ativo.');
      return;
    }
    const formData = new FormData(event.currentTarget);
    const content = String(formData.get('content') ?? '').trim();
    if (!content) {
      setErrorMessage('Escreva algo antes de submeter.');
      return;
    }
    setErrorMessage(null);
    addEntryMutation.mutate({ column, content });
  };

  const handleDraftChange = (column: string, value: string) => {
    setDrafts((prev) => ({ ...prev, [column]: value }));
  };

  if (!isAuthenticated && !loading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
        <p className="text-sm text-slate-600">Inicie sessão para visualizar o diário desta turma.</p>
        <Link href="/login" className="rounded-full bg-sky-600 px-4 py-2 text-white">
          Ir para login
        </Link>
      </main>
    );
  }

  if (loading || isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-100">
        <p className="text-sm text-slate-500">A carregar diário…</p>
      </main>
    );
  }

  if (error) {
    return (
      <AppShell title="Diário de Turma" description="Registos do percurso coletivo da turma.">
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {(error as Error).message}
        </div>
      </AppShell>
    );
  }

  if (!data) {
    notFound();
  }

  const turma: ClassSummary = data.class;

  const sessionData =
    selectedSessionId && selectedSessionId !== activeSessionId
      ? sessionDetailQuery.data ?? null
      : data;

  if (selectedSessionId && selectedSessionId !== activeSessionId && sessionDetailQuery.isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-100">
        <p className="text-sm text-slate-500">A carregar diário…</p>
      </main>
    );
  }

  if (sessionDetailQuery.isError) {
    const detailError = sessionDetailQuery.error as Error;
    return (
      <AppShell title="Diário de Turma" description="Registos do percurso coletivo da turma.">
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {detailError.message}
        </div>
      </AppShell>
    );
  }

  if (!sessionData) {
    return (
      <AppShell title="Diário de Turma" description="Registos do percurso coletivo da turma.">
        <p className="text-sm text-slate-600">Ainda não existe diário para esta turma.</p>
      </AppShell>
    );
  }

  const session = sessionData.session;
  const columns: DiaryColumnResponse[] = sessionData.columns;
  const canModerate = data.can_moderate;
  const isViewingActive = session && session.id === activeSessionId;
  const canAdd = isViewingActive && data.can_add_entries;
  const sessions: DiarySessionResponse[] =
    sessionsQuery.data ?? (session ? [session as DiarySessionResponse] : []);

  return (
    <AppShell
      title={`Diário — ${turma.name}`}
      description="Gostei, Não Gostei, Fizemos, Queremos: o registo cooperativo do dia."
    >
      <Link
        href={`/turmas/${classId}`}
        className="inline-flex items-center gap-2 self-start rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-sky-300 hover:text-sky-700"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="h-4 w-4"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
        </svg>
        Voltar à turma
      </Link>
      <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Período ativo</h2>
            {session ? (
              <p className="mt-2 text-sm text-slate-700">
                Iniciado a <strong>{formatDate(session.start_date)}</strong>
                {session.end_date ? ` — encerrado a ${formatDate(session.end_date)}` : ' — em curso'}
              </p>
            ) : (
              <p className="mt-2 text-sm text-slate-700">Ainda não existe um período ativo para este diário.</p>
            )}
          </div>
          {sessions.length > 0 ? (
            <div className="flex flex-col gap-2 text-sm text-slate-600">
              <label htmlFor="session-select" className="text-xs uppercase tracking-[0.3em] text-slate-500">
                Selecionar período
              </label>
              <select
                id="session-select"
                className="rounded-full border border-slate-300 px-3 py-1 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                value={selectedSessionId ?? ''}
                onChange={(event) => {
                  const value = Number(event.target.value);
                  setSelectedSessionId(Number.isNaN(value) ? null : value);
                  setErrorMessage(null);
                }}
              >
                {sessions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {`${formatDate(item.start_date)} — ${item.status === 'ACTIVE' ? 'Ativo' : 'Arquivado'}`}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
          {canModerate ? (
            <button
              type="button"
              onClick={() => startSessionMutation.mutate()}
              disabled={startSessionMutation.isLoading}
              className="inline-flex items-center rounded-full bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:bg-amber-300"
            >
              {startSessionMutation.isLoading ? 'A iniciar…' : session ? 'Arquivar e iniciar novo período' : 'Iniciar primeiro período'}
            </button>
          ) : null}
        </div>
        {errorMessage ? (
          <p className="mt-4 text-sm text-rose-600" role="alert">
            {errorMessage}
          </p>
        ) : null}
        {!session && canModerate ? (
          <p className="mt-4 text-sm text-slate-600">
            Quando iniciar um novo período, os alunos poderão registar o que gostaram, não gostaram, o que fizeram e o que
            querem planear.
          </p>
        ) : null}
      </section>

      {session ? (
        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {columns.map((column) => (
            <ColumnCard
              key={column.key}
              column={column}
              canAdd={canAdd}
              drafts={drafts}
              onDraftChange={handleDraftChange}
              onSubmit={handleSubmit}
              isSubmitting={addEntryMutation.isPending}
            />
          ))}
        </section>
      ) : null}
      {session && session.status !== 'ACTIVE' ? (
        <p className="mt-6 text-sm text-slate-500">
          Está a visualizar um período arquivado. Apenas professores podem iniciar um novo período ativo.
        </p>
      ) : null}
    </AppShell>
  );
}

interface ColumnCardProps {
  column: DiaryColumnResponse;
  canAdd: boolean;
  drafts: Record<string, string>;
  isSubmitting: boolean;
  onDraftChange: (column: string, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>, column: string) => void;
}

function ColumnCard({ column, canAdd, drafts, isSubmitting, onDraftChange, onSubmit }: ColumnCardProps) {
  const entries = column.entries;
  const draftValue = drafts[column.key] ?? '';

  return (
    <article className="flex h-full flex-col rounded-3xl border border-slate-200 bg-white/90 shadow-sm">
      <header className="border-b border-slate-200 px-4 py-3 text-center text-sm font-semibold uppercase tracking-[0.3em] text-slate-600">
        {column.label}
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {entries.length === 0 ? (
          <p className="text-center text-sm text-slate-500">Ainda sem registos.</p>
        ) : (
          entries.map((entry) => (
            <div key={entry.id} className="rounded-2xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <p className="leading-relaxed">{entry.content}</p>
              <footer className="mt-2 flex items-center justify-between text-xs text-slate-500">
                <span>{authorName(entry.author)}</span>
                <time dateTime={entry.created_at}>{formatDateTime(entry.created_at)}</time>
              </footer>
            </div>
          ))
        )}
      </div>
      {canAdd ? (
        <form className="border-t border-slate-200 px-4 py-3" onSubmit={(event) => onSubmit(event, column.key)}>
          <label htmlFor={`draft-${column.key}`} className="sr-only">
            Registar em {column.label}
          </label>
          <div className="flex items-center gap-2">
            <input
              id={`draft-${column.key}`}
              name="content"
              type="text"
              value={draftValue}
              onChange={(event) => onDraftChange(column.key, event.target.value)}
              placeholder={`Adicionar em "${column.label}"`}
              className="flex-1 rounded-full border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
              required
            />
            <button
              type="submit"
              aria-label={`Adicionar entrada em ${column.label}`}
              className="inline-flex items-center justify-center rounded-full bg-sky-600 p-2 text-lg font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-sky-300"
              disabled={isSubmitting}
            >
              +
            </button>
          </div>
        </form>
      ) : null}
    </article>
  );
}
