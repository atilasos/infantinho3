'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { ActionCard } from '@/components/ui/action-card';
import { API_BASE_URL, PUBLIC_SITE_BASE_URL } from '@/lib/config';
import { extractResults } from '@/lib/utils';
import { useAuth } from '@/providers/auth-provider';
import type { PublicPost } from '@/types/api';

const quickActions = [
  {
    href: '/dashboard',
    badge: 'Painel cooperativo',
    description: 'Entre no cockpit MEM com as turmas, planos e IA contextualizada.',
    badgeClassName: 'bg-slate-200 text-slate-700',
  },
  {
    href: '/checklists',
    badge: 'Checklists MEM',
    description: 'Veja como o portal regista autoavaliação e validação docente.',
    badgeClassName: 'bg-sky-100 text-sky-700',
  },
  {
    href: '/diario',
    badge: 'Diário de Turma',
    description: 'Reforce a memória coletiva da escola com registos multimédia.',
    badgeClassName: 'bg-amber-100 text-amber-700',
  },
  {
    href: '/assistente',
    badge: 'Assistente IA',
    description: 'Demonstre o tutor inteligente e o apoio imediato aos alunos.',
    badgeClassName: 'bg-emerald-100 text-emerald-700',
  },
];

export default function LandingPage() {
  const { isAuthenticated, user, signIn } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ['public-blog'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/blog/public`);
      if (!response.ok) {
        throw new Error('Não foi possível carregar o blog público.');
      }
      const body = await response.json();
      return extractResults<PublicPost>(body);
    },
  });

  const posts = data?.slice(0, 4) ?? [];

  const resolveAuthorName = (autor: PublicPost['autor']) => {
    if (!autor) return undefined;
    if (typeof autor === 'string') return autor;
    if (typeof autor === 'object' && 'name' in autor && typeof autor.name === 'string') {
      return autor.name;
    }
    return undefined;
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-emerald-50">
      <section className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-16 lg:flex-row lg:items-center">
        <div className="flex-1 space-y-5 text-slate-800">
          <span className="inline-flex rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-sky-600">
            Blog da Comunidade MEM
          </span>
          <h1 className="text-3xl font-semibold leading-tight sm:text-4xl">
            Uma experiência cooperativa entre alunos, professores e família.
          </h1>
          <p className="text-base text-slate-600 sm:text-lg">
            Explore as histórias, projetos e reflexões do Colégio Infante Dom Henrique.
            O Infantinho 3.0 reúne instrumentos MEM digitais, integração com Microsoft 365
            e tutores IA para reforçar a autonomia dos alunos.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {isAuthenticated ? (
              <Link
                href="/dashboard"
                className="rounded-full bg-sky-600 px-5 py-3 text-center text-sm font-medium text-white shadow-sm transition hover:bg-sky-700"
              >
                Ir para o painel cooperativo
              </Link>
            ) : (
              <button
                type="button"
                onClick={() => signIn()}
                className="rounded-full bg-sky-600 px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-sky-700"
              >
                Entrar com Microsoft
              </button>
            )}
            <Link
              href={`${PUBLIC_SITE_BASE_URL}/blog/`}
              className="rounded-full border border-slate-300 px-5 py-3 text-center text-sm font-medium text-slate-600 transition hover:bg-white"
            >
              Ver blog completo
            </Link>
          </div>
          {isAuthenticated && (
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
              Sessão ativa como {user?.first_name || user?.username}
            </p>
          )}
        </div>
        <div className="flex-1 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800">Módulos em destaque</h2>
          <p className="mt-2 text-sm text-slate-600">
            Use estes atalhos para preparar a apresentação à direção e demonstrar o trabalho cooperativo.
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {quickActions.map((item) => (
              <ActionCard key={item.href} {...item} />
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Últimas publicações</p>
            <h2 className="text-2xl font-semibold text-slate-800">Diário aberto à comunidade</h2>
          </div>
          <Link
            href={`${PUBLIC_SITE_BASE_URL}/blog/`}
            className="text-sm font-medium text-sky-600 hover:underline"
          >
            Consultar todas as notícias →
          </Link>
        </div>

        {error && (
          <div className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
            {(error as Error).message}
          </div>
        )}

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          {isLoading && !posts.length ? (
            <div className="rounded-3xl border border-slate-200 bg-white/70 p-6 text-sm text-slate-500">
              A carregar histórias da comunidade…
            </div>
          ) : (
            posts.map((post) => {
              const authorName = resolveAuthorName(post.autor);
              return (
                <article key={post.id} className="group rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.25em] text-slate-500">
                    <span>{post.categoria || 'Diário'}</span>
                    <span>{post.publicado_em ? new Date(post.publicado_em).toLocaleDateString('pt-PT') : 'Por publicar'}</span>
                  </div>
                  <h3 className="mt-4 text-xl font-semibold text-slate-800">{post.titulo ?? 'Sem título'}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-slate-600">{post.excerpt || post.conteudo}</p>
                  {authorName && (
                    <p className="mt-3 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                      {authorName}
                    </p>
                  )}
                  <Link
                    href={`${PUBLIC_SITE_BASE_URL}/blog/post/${post.id}/`}
                    className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-sky-600"
                  >
                    Ler artigo completo
                    <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" className="h-4 w-4 transition group-hover:translate-x-1">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14m-7-7 7 7-7 7" />
                    </svg>
                  </Link>
                </article>
              );
            })
          )}

          {!isLoading && posts.length === 0 && !error && (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
              Ainda não existem publicações aprovadas. Utilize o backend para criar posts e partilhar novidades.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
