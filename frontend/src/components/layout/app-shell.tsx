'use client';

import { ReactNode, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';
import { useAuth } from '@/providers/auth-provider';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Painel' },
  { href: '/classes', label: 'Turmas' },
  { href: '/checklists', label: 'Checklists' },
  { href: '/pit', label: 'Planos PIT' },
  { href: '/diario', label: 'Diário de Turma' },
  { href: '/projects', label: 'Projetos' },
  { href: '/assistente', label: 'Assistente IA' },
];

type AppShellProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function AppShell({ title, description, actions, children }: AppShellProps) {
  const pathname = usePathname();
  const { user, logout, signIn } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const initials = useMemo(() => {
    if (!user) return 'Guest';
    const names = [user.first_name, user.last_name].filter(Boolean);
    if (!names.length) {
      return user.username.slice(0, 2).toUpperCase();
    }
    return names
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => part[0]?.toUpperCase() ?? '')
      .join('')
      .slice(0, 2);
  }, [user]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur supports-backdrop-filter:bg-white/60">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/" className="flex items-center gap-2 font-semibold text-slate-800">
            <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-sky-600">
              Infantinho 3.0
            </span>
            <span className="hidden text-sm text-slate-500 sm:inline">Portal Cooperativo MEM</span>
          </Link>
          <nav className="hidden items-center gap-1 rounded-full bg-white/60 px-1 py-1 text-sm text-slate-600 shadow-sm ring-1 ring-slate-200 md:flex">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'rounded-full px-3 py-2 transition',
                    isActive ? 'bg-sky-500 text-white shadow-sm' : 'hover:bg-white/80',
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex flex-col items-end text-xs text-slate-500">
              <span className="text-sm font-medium text-slate-700">
                {user?.first_name || user?.username || 'Conta convidada'}
              </span>
              <span className="flex items-center gap-2">
                {user?.role ? user.role : 'convidado'}
                {user?.is_guest && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700">
                    Acesso limitado
                  </span>
                )}
              </span>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-700">
              {initials}
            </div>
            <button
              type="button"
              onClick={() => (user ? logout() : signIn())}
              className="hidden rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 sm:inline"
            >
              {user ? 'Terminar sessão' : 'Entrar'}
            </button>
            <button
              type="button"
              onClick={() => setMobileOpen((prev) => !prev)}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 text-slate-600 transition hover:bg-slate-100 md:hidden"
              aria-label="Alternar navegação"
            >
              <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" className="h-5 w-5">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
          </div>
        </div>
        {mobileOpen && (
          <div className="border-t border-slate-200 bg-white/90 px-4 py-3 md:hidden">
            <nav className="flex flex-col gap-2 text-sm text-slate-600">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'rounded-xl px-3 py-2',
                      isActive ? 'bg-sky-500 text-white' : 'bg-white/40 hover:bg-white',
                    )}
                    onClick={() => setMobileOpen(false)}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <button
                type="button"
                onClick={() => {
                  setMobileOpen(false);
                  if (user) {
                    void logout();
                  } else {
                    void signIn();
                  }
                }}
                className="rounded-xl bg-slate-800 px-3 py-2 text-left font-medium text-white"
              >
                {user ? 'Terminar sessão' : 'Entrar com Microsoft'}
              </button>
            </nav>
          </div>
        )}
      </header>
      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Infantinho Headless</p>
            <h1 className="text-3xl font-semibold text-slate-900 sm:text-4xl">{title}</h1>
            {description && <p className="max-w-2xl text-sm text-slate-600 sm:text-base">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
        <section className="space-y-6 pb-10">{children}</section>
      </main>
    </div>
  );
}
