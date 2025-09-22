import type { Meta, StoryObj } from '@storybook/react';

import { ActionCard } from './action-card';

const meta: Meta<typeof ActionCard> = {
  title: 'UI/ActionCard',
  component: ActionCard,
  tags: ['autodocs'],
  args: {
    href: '/checklists',
    badge: 'Checklists MEM',
    description: 'Autoavaliação visível e validação docente com feedback imediato.',
    badgeClassName: 'bg-sky-100 text-sky-700',
  },
};

export default meta;

type Story = StoryObj<typeof ActionCard>;

export const Default: Story = {};

export const WithCustomTitle: Story = {
  args: {
    title: 'Ciclo completo de cooperação',
    description: 'Demonstre como o ciclo MEM passa pela autoavaliação, validação e reflexão partilhada.',
  },
};

export const WithCustomFooter: Story = {
  args: {
    footer: (
      <span className="inline-flex items-center gap-2 text-emerald-600">
        Ver instruções
        <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" className="h-4 w-4">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14m-7-7 7 7-7 7" />
        </svg>
      </span>
    ),
  },
};
