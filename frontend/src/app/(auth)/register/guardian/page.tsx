'use client';

import { FormEvent, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

import { useAuth } from '@/providers/auth-provider';

export default function GuardianRegisterPage() {
  const { registerGuardian } = useAuth();
  const [formState, setFormState] = useState({
    firstName: '',
    lastName: '',
    email: '',
    studentNumber: '',
    relationship: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof typeof formState) => (event: FormEvent<HTMLInputElement>) => {
    setFormState((prev) => ({ ...prev, [field]: event.currentTarget.value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerGuardian({
        firstName: formState.firstName,
        lastName: formState.lastName,
        email: formState.email,
        password: formState.password,
        confirmPassword: formState.confirmPassword,
        studentNumber: formState.studentNumber,
        relationship: formState.relationship,
      });
    } catch (err) {
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message);
          const firstError = Object.values(parsed as Record<string, { message: string }[]>)[0]?.[0]?.message;
          setError(firstError ?? 'Não foi possível criar a conta.');
        } catch {
          setError(err.message);
        }
      } else {
        setError('Não foi possível criar a conta.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center px-6 py-8">
      <Head>
        <title>Criar conta de encarregado • Infantinho 3.0</title>
      </Head>
      <div className="max-w-2xl w-full rounded-2xl bg-white p-8 shadow-sm border border-slate-200">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Infantinho 3.0</p>
        <h1 className="text-2xl font-semibold text-slate-800 mt-2">Registo de encarregado de educação</h1>
        <p className="text-sm text-slate-600 mt-2">
          Utilize o número de aluno partilhado pela escola para associar a sua conta ao educando.
        </p>
        <form className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleSubmit}>
          <div className="md:col-span-1">
            <label htmlFor="firstName" className="block text-sm font-medium text-slate-700">
              Primeiro nome
            </label>
            <input
              id="firstName"
              type="text"
              value={formState.firstName}
              onChange={handleChange('firstName')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div className="md:col-span-1">
            <label htmlFor="lastName" className="block text-sm font-medium text-slate-700">
              Apelido
            </label>
            <input
              id="lastName"
              type="text"
              value={formState.lastName}
              onChange={handleChange('lastName')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="email" className="block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={formState.email}
              onChange={handleChange('email')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div className="md:col-span-1">
            <label htmlFor="studentNumber" className="block text-sm font-medium text-slate-700">
              Número do aluno
            </label>
            <input
              id="studentNumber"
              type="text"
              required
              value={formState.studentNumber}
              onChange={handleChange('studentNumber')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div className="md:col-span-1">
            <label htmlFor="relationship" className="block text-sm font-medium text-slate-700">
              Relação (opcional)
            </label>
            <input
              id="relationship"
              type="text"
              value={formState.relationship}
              onChange={handleChange('relationship')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div className="md:col-span-1">
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={formState.password}
              onChange={handleChange('password')}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div className="md:col-span-1">
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700">
              Confirmar password
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
            <div className="md:col-span-2">
              <p className="text-sm text-red-600" role="alert">
                {error}
              </p>
            </div>
          ) : null}
          <div className="md:col-span-2">
            <button
              type="submit"
              className="w-full rounded-lg bg-sky-600 py-2 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={loading}
            >
              {loading ? 'A criar conta…' : 'Criar conta'}
            </button>
          </div>
        </form>
        <div className="mt-4 text-sm text-slate-600">
          <Link href="/login" className="text-sky-600 hover:underline">
            Voltar ao login
          </Link>
        </div>
      </div>
    </div>
  );
}
