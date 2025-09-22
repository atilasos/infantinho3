'use client';

import { FormEvent, useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/navigation';

import { useAuth } from '@/providers/auth-provider';

export default function ForcePasswordPage() {
  const router = useRouter();
  const { user, loading, isAuthenticated, completePasswordChange } = useAuth();
  const [formState, setFormState] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (user && !user.must_change_password) {
      router.replace('/');
    }
  }, [isAuthenticated, loading, router, user]);

  const handleChange = (field: keyof typeof formState) => (event: FormEvent<HTMLInputElement>) => {
    setFormState((prev) => ({ ...prev, [field]: event.currentTarget.value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await completePasswordChange({
        oldPassword: formState.oldPassword,
        newPassword: formState.newPassword,
        confirmPassword: formState.confirmPassword,
      });
    } catch (err) {
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message);
          const firstError = Object.values(parsed as Record<string, string[]>)[0]?.[0];
          setError(firstError ?? 'Não foi possível atualizar a password.');
        } catch {
          setError(err.message);
        }
      } else {
        setError('Não foi possível atualizar a password.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center px-6 py-8">
      <Head>
        <title>Atualizar password • Infantinho 3.0</title>
      </Head>
      <div className="max-w-lg w-full rounded-2xl bg-white p-8 shadow-sm border border-slate-200">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Infantinho 3.0</p>
        <h1 className="text-2xl font-semibold text-slate-800 mt-2">Atualize a sua password</h1>
        <p className="text-sm text-slate-600 mt-2">
          Por segurança, é necessário definir uma nova password antes de continuar a utilizar o portal.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="oldPassword" className="block text-sm font-medium text-slate-700">
              Password atual
            </label>
            <input
              id="oldPassword"
              type="password"
              autoComplete="current-password"
              required
              value={formState.oldPassword}
              onChange={handleChange('oldPassword')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-slate-700">
              Nova password
            </label>
            <input
              id="newPassword"
              type="password"
              autoComplete="new-password"
              required
              value={formState.newPassword}
              onChange={handleChange('newPassword')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700">
              Confirmar nova password
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={formState.confirmPassword}
              onChange={handleChange('confirmPassword')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          {error ? (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          ) : null}
          <button
            type="submit"
            className="w-full rounded-lg bg-sky-600 py-2 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={submitting}
          >
            {submitting ? 'A atualizar…' : 'Guardar nova password'}
          </button>
        </form>
      </div>
    </div>
  );
}
