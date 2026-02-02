// Configuration for Infantinho 3.0 Frontend

// API Base URL - Django backend
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Public site base URL
export const PUBLIC_SITE_BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

// Feature flags
export const FEATURES = {
  AI_ASSISTANT: true,
  CHECKLISTS: true,
  PIT: true,
  BLOG: true,
  COUNCIL: true,
};

// Default pagination
export const DEFAULT_PAGE_SIZE = 20;

// AI Assistant configuration
export const AI_CONFIG = {
  maxTokens: 1000,
  temperature: 0.7,
  defaultPersona: 'student',
};
