import {
  User,
  Organization,
  Ticket,
  Message,
  KnowledgeDocument,
  ResponseDraft,
  AnalyticsOverview,
  AuditEvent
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;
  private currentOrgId: string | null = null;

  constructor() {
    this.token = localStorage.getItem('auth_token');
    this.currentOrgId = localStorage.getItem('current_org_id');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  setCurrentOrgId(orgId: string | null) {
    this.currentOrgId = orgId;
    if (orgId) {
      localStorage.setItem('current_org_id', orgId);
    } else {
      localStorage.removeItem('current_org_id');
    }
  }

  getCurrentOrgId(): string | null {
    return this.currentOrgId;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (this.currentOrgId) {
      headers['X-Organization-ID'] = this.currentOrgId;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `API Error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {}
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Auth & Tenant
  async login(email: string, password: string):Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    if (res.user.memberships?.length > 0 && !this.currentOrgId) {
      this.setCurrentOrgId(res.user.memberships[0].organization_id);
    }
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  async getOrganizations(): Promise<Organization[]> {
    return this.request<Organization[]>('/organizations');
  }

  // Tickets
  async getTickets(params: { status?: string; priority?: string; category?: string; search?: string } = {}): Promise<{ total: number; items: Ticket[] }> {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.priority) query.append('priority', params.priority);
    if (params.category) query.append('category', params.category);
    if (params.search) query.append('search', params.search);

    const qs = query.toString();
    return this.request<{ total: number; items: Ticket[] }>(`/tickets${qs ? `?${qs}` : ''}`);
  }

  async getTicket(id: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${id}`);
  }

  async createTicket(payload: { subject: string; description: string; source?: string; idempotency_key?: string }): Promise<Ticket> {
    return this.request<Ticket>('/tickets', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateTicket(id: string, updates: { status?: string; priority?: string; category?: string; assigned_team_id?: string }): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async addMessage(ticketId: string, payload: { body: string; sender_type: string; sender_name?: string }): Promise<Message> {
    return this.request<Message>(`/tickets/${ticketId}/messages`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async classifyTicket(ticketId: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}/classify`, {
      method: 'POST',
    });
  }

  async escalateTicket(ticketId: string, reason: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}/escalate`, {
      method: 'POST',
      body: JSON.stringify({ reason, target_priority: 'urgent' }),
    });
  }

  // AI Suggestions & Approvals
  async getDrafts(ticketId: string): Promise<ResponseDraft[]> {
    return this.request<ResponseDraft[]>(`/tickets/${ticketId}/drafts`);
  }

  async generateDraft(ticketId: string): Promise<ResponseDraft> {
    return this.request<ResponseDraft>(`/tickets/${ticketId}/drafts`, {
      method: 'POST',
    });
  }

  async editDraft(draftId: string, body: string): Promise<ResponseDraft> {
    return this.request<ResponseDraft>(`/drafts/${draftId}`, {
      method: 'PATCH',
      body: JSON.stringify({ body }),
    });
  }

  async approveDraft(draftId: string): Promise<ResponseDraft> {
    return this.request<ResponseDraft>(`/drafts/${draftId}/approve`, {
      method: 'POST',
    });
  }

  async rejectDraft(draftId: string, reason: string): Promise<ResponseDraft> {
    return this.request<ResponseDraft>(`/drafts/${draftId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async sendApprovedDraft(draftId: string): Promise<{ success: boolean; message: string; delivery_status: string }> {
    return this.request<{ success: boolean; message: string; delivery_status: string }>(`/drafts/${draftId}/send`, {
      method: 'POST',
    });
  }

  // Knowledge Base
  async getDocuments(): Promise<KnowledgeDocument[]> {
    return this.request<KnowledgeDocument[]>('/knowledge/documents');
  }

  async uploadDocument(title: string, content: string): Promise<KnowledgeDocument> {
    return this.request<KnowledgeDocument>('/knowledge/documents', {
      method: 'POST',
      body: JSON.stringify({ title, content, file_type: 'text/markdown' }),
    });
  }

  async searchKnowledge(query: string): Promise<any[]> {
    return this.request<any[]>('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: 4 }),
    });
  }

  // Analytics & Auditing
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>('/analytics/overview');
  }

  async getAuditEvents(): Promise<{ total: number; items: AuditEvent[] }> {
    return this.request<{ total: number; items: AuditEvent[] }>('/audit-events');
  }
}

export const api = new ApiClient();
