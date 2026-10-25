export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface Membership {
  id: string;
  organization_id: string;
  organization_name?: string;
  role: 'admin' | 'manager' | 'agent';
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  memberships: Membership[];
}

export interface Team {
  id: string;
  name: string;
}

export interface Citation {
  id: string;
  chunk_id: string;
  passage_snippet?: string;
  relevance_score?: number;
  created_at: string;
}

export interface ResponseDraft {
  id: string;
  ticket_id: string;
  body: string;
  status: 'draft' | 'approved' | 'rejected';
  created_by_model: string;
  confidence_score?: number;
  rejection_reason?: string;
  reviewed_by_id?: string;
  reviewed_at?: string;
  created_at: string;
  citations: Citation[];
}

export interface Message {
  id: string;
  ticket_id: string;
  sender_type: 'customer' | 'agent' | 'system' | 'internal';
  sender_id?: string;
  sender_name?: string;
  body: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  organization_id: string;
  subject: string;
  description: string;
  source: string;
  external_id?: string;
  idempotency_key?: string;
  status: 'received' | 'processing' | 'needs_triage' | 'awaiting_review' | 'approved' | 'sending' | 'sent' | 'resolved';
  priority: 'urgent' | 'high' | 'normal' | 'low';
  category?: 'billing' | 'technical' | 'security' | 'account' | 'general';
  sentiment?: 'positive' | 'neutral' | 'negative' | 'frustrated';
  intent?: string;
  confidence_score?: number;
  needs_human_review: boolean;
  assigned_team_id?: string;
  assigned_team?: Team;
  assigned_user_id?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  messages: Message[];
  drafts: ResponseDraft[];
}

export interface KnowledgeDocument {
  id: string;
  organization_id: string;
  title: string;
  file_type: string;
  version: number;
  status: 'processing' | 'indexed' | 'failed';
  error_message?: string;
  created_at: string;
}

export interface AnalyticsOverview {
  ticket_volume: number;
  first_response_time_seconds: number;
  resolution_time_seconds: number;
  escalation_rate: number;
  draft_approval_rate: number;
  ai_failure_rate: number;
  average_processing_latency_ms: number;
  by_status: { status: string; count: number }[];
  by_category: { category: string; count: number }[];
  by_priority: { priority: string; count: number }[];
}

export interface AuditEvent {
  id: string;
  organization_id: string;
  actor_id?: string;
  actor_email?: string;
  action: string;
  target_type: string;
  target_id: string;
  details?: Record<string, any>;
  timestamp: string;
}
