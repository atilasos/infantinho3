import type { components } from './openapi';

export type AppUser = components['schemas']['User'] & {
  must_change_password?: boolean;
  is_superuser?: boolean;
  is_staff?: boolean;
};
export type ClassSummary = Pick<components['schemas']['Class'], 'id' | 'name' | 'year'>;
export type ChecklistStatus = components['schemas']['ChecklistStatus'] & {
  state?: 'draft' | 'submitted' | 'validated' | 'needs_revision';
  student_notes?: string;
};
export type ChecklistMark = components['schemas']['ChecklistMark'];
export type ChecklistTemplate = components['schemas']['ChecklistTemplate'];
export type IndividualPlan = components['schemas']['IndividualPlan'];
export type PlanTask = components['schemas']['PlanTask'];
export type Project = components['schemas']['Project'];
export type ProjectTask = components['schemas']['ProjectTask'];
export type DiaryPost = components['schemas']['Post'];
export type PublicPost = components['schemas']['PublicPost'];

export interface PlanSection {
  id: number;
  title: string;
  area_code: string | null;
  order: number;
  template_section_id: number | null;
}

export interface PlanSuggestion {
  id: number;
  text: string;
  origin: 'template' | 'council' | 'pending' | 'manual';
  is_pending: boolean;
  order: number;
  template_suggestion_id: number | null;
  from_task_id: number | null;
  created_at: string;
}

export type PlanLogEntry = {
  id: number;
  action: 'generated_from_template' | 'updated' | 'status_change' | 'comment';
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type PlanDetail = IndividualPlan & {
  template?: {
    id: number;
    name: string;
    version: number;
  } | null;
  template_version?: number;
  origin_plan_id?: number | null;
  suggestions_imported?: boolean;
  pendings_imported?: boolean;
  suggestions?: PlanSuggestion[];
  sections?: PlanSection[];
  log_entries?: PlanLogEntry[];
  student_class?: ClassSummary;
};

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
