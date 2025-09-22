'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

type ActionCardProps = {
  href: string;
  badge: string;
  description: string;
  badgeClassName?: string;
  title?: string;
  footer?: ReactNode;
};

export function ActionCard({ href, badge, description, badgeClassName, title, footer }: ActionCardProps) {
  return (
    <Link
      href={href}
      className="group rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
    >
      <span
        className={cn(
          'inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em]',
          badgeClassName ?? 'bg-slate-100 text-slate-600',
        )}
      >
        {badge}
      </span>
      {title && <h3 className="mt-4 text-base font-semibold text-slate-800">{title}</h3>}
      <p className="mt-4 text-sm text-slate-600">{description}</p>
      <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-sky-600">
        {footer ?? (
          <>
            Aceder
            <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" className="h-4 w-4 transition group-hover:translate-x-1">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14m-7-7 7 7-7 7" />
            </svg>
          </>
        )}
      </span>
    </Link>
  );
}
