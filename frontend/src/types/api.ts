import type { components } from './openapi';

export type AppUser = components['schemas']['User'] & {
  must_change_password?: boolean;
};
export type ClassSummary = Pick<components['schemas']['Class'], 'id' | 'name' | 'year'>;
export type ChecklistStatus = components['schemas']['ChecklistStatus'];
export type ChecklistMark = components['schemas']['ChecklistMark'];
export type ChecklistTemplate = components['schemas']['ChecklistTemplate'];
export type IndividualPlan = components['schemas']['IndividualPlan'];
export type PlanTask = components['schemas']['PlanTask'];
export type Project = components['schemas']['Project'];
export type ProjectTask = components['schemas']['ProjectTask'];
export type DiaryPost = components['schemas']['Post'];
export type PublicPost = components['schemas']['PublicPost'];

export interface DiaryEntryResponse {
  id: number;
  column: string;
  column_label: string;
  content: string;
  created_at: string;
  author: AppUser | null;
}

export interface DiaryColumnResponse {
  key: string;
  label: string;
  entries: DiaryEntryResponse[];
}

export interface DiarySessionResponse {
  id: number;
  start_date: string;
  end_date: string | null;
  status: 'ACTIVE' | 'ARCHIVED';
}

export interface DiaryActiveResponse {
  class: ClassSummary;
  session: DiarySessionResponse | null;
  columns: DiaryColumnResponse[];
  can_moderate: boolean;
  can_add_entries: boolean;
}
