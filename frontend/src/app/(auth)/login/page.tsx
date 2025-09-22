'use client';

import { FormEvent, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

import { useAuth } from '@/providers/auth-provider';

export default function LoginPage() {
  const { signIn, signInLocal } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loadingLocal, setLoadingLocal] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleLocalLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoadingLocal(true);
    setLocalError(null);
    try {
      await signInLocal({ identifier, password });
    } catch (error) {
      if (error instanceof Error) {
        setLocalError(error.message.replace(/^"|"$/g, ''));
      } else {
        setLocalError('Falha no login. Tente novamente.');
      }
    } finally {
      setLoadingLocal(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center px-6 py-8">
      <Head>
        <title>Entrar • Infantinho 3.0</title>
      </Head>
      <div className="max-w-3xl w-full grid grid-cols-1 md:grid-cols-2 gap-8">
        <section className="rounded-2xl bg-white p-8 shadow-sm border border-slate-200">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Infantinho 3.0</p>
          <h1 className="text-2xl font-semibold text-slate-800 mt-2">Login com email e password</h1>
          <p className="text-sm text-slate-600 mt-2">
            Administradores e encarregados de educação podem entrar com as credenciais fornecidas pela escola.
          </p>
          <form className="mt-6 space-y-4" onSubmit={handleLocalLogin}>
            <div>
              <label htmlFor="identifier" className="block text-sm font-medium text-slate-700">
                Email ou utilizador
              </label>
              <input
                id="identifier"
                type="text"
                autoComplete="username"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
              />
            </div>
            {localError ? (
              <p className="text-sm text-red-600" role="alert">
                {localError}
              </p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-lg bg-sky-600 py-2 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={loadingLocal}
            >
              {loadingLocal ? 'A entrar…' : 'Entrar'}
            </button>
          </form>
          <div className="mt-4 text-sm text-slate-600 space-y-2">
            <p>
              <Link href="/register/guardian" className="text-sky-600 hover:underline">
                Primeiro acesso como encarregado? Criar conta
              </Link>
            </p>
            <p>
              Para recuperar a password contacte a equipa administrativa do Infantinho.
            </p>
          </div>
        </section>

        <section className="rounded-2xl bg-white p-8 shadow-sm border border-slate-200 space-y-6">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Infantinho 3.0</p>
            <h2 className="text-2xl font-semibold text-slate-800 mt-2">Autenticação Microsoft</h2>
            <p className="text-sm text-slate-600 mt-2">
              Alunos e professores devem usar a conta escolar Microsoft. Após o login será efetuado o redirecionamento automático.
            </p>
          </div>
          <button
            type="button"
            onClick={() => signIn()}
            className="w-full rounded-full bg-sky-600 py-3 text-white font-medium hover:bg-sky-700 transition"
          >
            Entrar com Microsoft
          </button>
        </section>
      </div>
    </div>
  );
}
