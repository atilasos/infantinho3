'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import { useAuth } from '@/providers/auth-provider';

export default function MicrosoftCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleAzureCallback } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    if (!code || !state) {
      setError('Parâmetros inválidos devolvidos pela Microsoft.');
      return;
    }

    const completeCallback = async () => {
      try {
        await handleAzureCallback({ code, state });
        router.replace('/');
      } catch (err) {
        console.error(err);
        setError('Não foi possível concluir a autenticação.');
      }
    };

    void completeCallback();
  }, [handleAzureCallback, router, searchParams]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-3 bg-slate-100 px-6 text-center">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Infantinho 3.0</p>
      {error ? (
        <div className="max-w-md space-y-3">
          <h1 className="text-xl font-semibold text-rose-600">Erro no login</h1>
          <p className="text-sm text-slate-600">{error}</p>
          <p className="text-sm text-slate-600">
            Volte à página de <a href="/login" className="font-medium text-sky-600 hover:underline">login</a> e tente novamente.
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <h1 className="text-xl font-semibold text-slate-800">Estamos a ligar a sua conta…</h1>
          <p className="text-sm text-slate-600">Este processo demora apenas alguns segundos.</p>
        </div>
      )}
    </main>
  );
}
