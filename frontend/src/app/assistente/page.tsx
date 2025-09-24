'use client';

import { FormEvent, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import { AppShell } from '@/components/layout/app-shell';
import { useAuth } from '@/providers/auth-provider';

type FeedbackValue = 'helpful' | 'neutral' | 'not_helpful';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: number;
  meta?: {
    model?: string;
    requestId?: string | null;
    feedback?: FeedbackValue;
  };
};

type AssistantResponse = {
  response: string;
  model?: string;
  meta?: Record<string, unknown>;
  session_id?: string | null;
  request_id?: string | null;
};

const FEEDBACK_OPTIONS: FeedbackValue[] = ['helpful', 'neutral', 'not_helpful'];

function randomId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function AssistantPage() {
  const searchParams = useSearchParams();
  const { fetchWithAuth, isAuthenticated, loading } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: randomId(),
      role: 'assistant',
      content: 'Olá! Sou o tutor IA do Infantinho 3.0. Posso contextualizar checklists, PIT ou projetos consoante o módulo em que está.',
      createdAt: Date.now(),
    },
  ]);
  const [composer, setComposer] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const origin = searchParams.get('context') ?? 'portal';

  const canSend = composer.trim().length > 0 && !sending;

  const lastAssistantMessage = useMemo(() => {
    return [...messages].reverse().find((msg) => msg.role === 'assistant');
  }, [messages]);

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();
    if (!canSend) return;

    const content = composer.trim();
    setComposer('');
    setError(null);

    const userMessage: ChatMessage = {
      id: randomId(),
      role: 'user',
      content,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);

    try {
      const history = [...messages, userMessage]
        .filter((msg) => msg.role !== 'system')
        .map((msg) => ({ role: msg.role, content: msg.content }));

      const response = await fetchWithAuth('/ai/assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          origin_app: origin,
          session_id: sessionId ?? undefined,
          history,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({} as any));
        if (errData && (errData.code === 'guardrail' || errData.error)) {
          setError((errData.error as string) || 'Conteúdo bloqueado pelos guardrails.');
          return;
        }
        throw new Error('O assistente não respondeu.');
      }

      const data = (await response.json()) as AssistantResponse;
      const assistantMessage: ChatMessage = {
        id: randomId(),
        role: 'assistant',
        content: data.response,
        createdAt: Date.now(),
        meta: {
          model: data.model,
          requestId: data.request_id ?? (typeof data.meta?.request_id === 'string' ? (data.meta.request_id as string) : null),
        },
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setSessionId(data.session_id ?? (typeof data.meta?.session_id === 'string' ? (data.meta.session_id as string) : sessionId));
    } catch (err) {
      console.error(err);
      setError('Não foi possível contactar o assistente neste momento.');
    } finally {
      setSending(false);
    }
  };

  const handleFeedback = async (message: ChatMessage, feedback: FeedbackValue) => {
    if (!message.meta?.requestId || message.meta.feedback === feedback) return;
    try {
      const res = await fetchWithAuth('/ai/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ request_id: message.meta.requestId, feedback }),
      });
      if (!res.ok) {
        throw new Error('Falha ao registar feedback.');
      }
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === message.id && msg.meta) {
            return { ...msg, meta: { ...msg.meta, feedback } };
          }
          return msg;
        }),
      );
    } catch (err) {
      console.error(err);
      setError('Não foi possível enviar o feedback.');
    }
  };

  const resetConversation = () => {
    setMessages([
      {
        id: randomId(),
        role: 'assistant',
        content: 'Nova sessão iniciada. Conte-me como posso apoiar a sua próxima apresentação.',
        createdAt: Date.now(),
      },
    ]);
    setSessionId(null);
    setError(null);
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">A carregar assistente…</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
        <p className="text-sm text-slate-600">Inicie sessão para utilizar o tutor inteligente.</p>
      </main>
    );
  }

  return (
    <AppShell
      title="Assistente Inteligente"
      description="Orquestração multi-modelo que contextualiza o diálogo com dados de checklists, PIT e projetos. Ideal para a demonstração à direção."
      actions={
        <div className="flex items-center gap-2">
          {sessionId && (
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
              Sessão ativa
            </span>
          )}
          <button
            type="button"
            onClick={resetConversation}
            className="rounded-full border border-slate-300 px-3 py-1 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
          >
            Nova sessão
          </button>
        </div>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <section className="flex h-[520px] flex-col rounded-3xl border border-slate-200 bg-white/90 shadow-sm">
          <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    message.role === 'user'
                      ? 'bg-sky-600 text-white'
                      : 'bg-slate-100 text-slate-800'
                  }`}
                >
                  <p>{message.content}</p>
                  {message.role === 'assistant' && (
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-slate-500">
                      {message.meta?.model && <span>Modelo: {message.meta.model}</span>}
                    </div>
                  )}
                  {message.role === 'assistant' && message.meta?.requestId && (
                    <div className="mt-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-slate-500">
                      <span>Feedback:</span>
                      {FEEDBACK_OPTIONS.map((option) => (
                        <button
                          key={option}
                          type="button"
                          onClick={() => handleFeedback(message, option)}
                          className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] transition ${
                            message.meta?.feedback === option
                              ? 'bg-emerald-500 text-white'
                              : 'bg-white/70 text-slate-500 hover:bg-slate-100'
                          }`}
                        >
                          {option === 'helpful' && 'Útil'}
                          {option === 'neutral' && 'Neutro'}
                          {option === 'not_helpful' && 'Rever'}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-500">
                  O tutor está a escrever…
                </div>
              </div>
            )}
          </div>
          <form onSubmit={handleSend} className="border-t border-slate-200 bg-white/90 px-6 py-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <textarea
                value={composer}
                onChange={(event) => setComposer(event.target.value)}
                rows={2}
                placeholder="Descreva a dúvida ou peça um resumo para a direção…"
                className="w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200"
              />
              <button
                type="submit"
                disabled={!canSend}
                className="shrink-0 rounded-2xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Enviar
              </button>
            </div>
            {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}
          </form>
        </section>
        <aside className="space-y-4 rounded-3xl border border-slate-200 bg-white/80 p-6 text-sm text-slate-600 shadow-sm">
          <h2 className="text-base font-semibold text-slate-800">Como o tutor trabalha</h2>
          <ul className="space-y-3">
            <li>
              • Orquestrador consulta checklists, PIT e projetos para enriquecer o prompt.
            </li>
            <li>
              • Respostas multi-modelo: planeamento pedagógico + FAQ administrativa.
            </li>
            <li>
              • Feedback docente/aluno é registado para afinar as sugestões.
            </li>
          </ul>
          {lastAssistantMessage?.meta?.model && (
            <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
              Último modelo utilizado: <span className="font-semibold text-slate-700">{lastAssistantMessage.meta.model}</span>
            </p>
          )}
        </aside>
      </div>
    </AppShell>
  );
}

// Avoid prerendering; this page relies on useSearchParams at runtime
export const dynamic = 'force-dynamic';
