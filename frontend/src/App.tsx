import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { Organization, User, Ticket, KnowledgeDocument, AnalyticsOverview, AuditEvent } from './types';
import { Navbar } from './components/Navbar';
import { Sidebar, NavTab } from './components/Sidebar';
import { TicketList } from './features/tickets/TicketList';
import { TicketDetail } from './features/tickets/TicketDetail';
import { KnowledgeManager } from './features/knowledge/KnowledgeManager';
import { AnalyticsDashboard } from './features/analytics/AnalyticsDashboard';
import { AuditView } from './features/audit/AuditView';
import { NewTicketModal } from './features/tickets/NewTicketModal';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [currentTab, setCurrentTab] = useState<NavTab>('inbox');

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isNewTicketOpen, setIsNewTicketOpen] = useState(false);

  // Initial Auth & Data Load
  useEffect(() => {
    const initApp = async () => {
      try {
        setIsLoading(true);
        // Default login with demo admin account
        const authRes = await api.login('admin@acme.com', 'password123');
        setCurrentUser(authRes.user);

        const orgs = await api.getOrganizations();
        setOrganizations(orgs);
        if (orgs.length > 0) {
          const defaultOrg = orgs[0];
          setCurrentOrg(defaultOrg);
          api.setCurrentOrgId(defaultOrg.id);
          await loadOrgData(defaultOrg.id);
        }
      } catch (err) {
        console.error('Initialization error:', err);
      } finally {
        setIsLoading(false);
      }
    };
    initApp();
  }, []);

  const loadOrgData = async (orgId: string) => {
    try {
      setIsRefreshing(true);
      const [tixRes, docsRes, anRes, audRes] = await Promise.all([
        api.getTickets(),
        api.getDocuments(),
        api.getAnalyticsOverview(),
        api.getAuditEvents(),
      ]);
      setTickets(tixRes.items);
      setDocuments(docsRes);
      setAnalytics(anRes);
      setAuditEvents(audRes.items);

      if (tixRes.items.length > 0) {
        // Keep currently selected ticket or pick first
        setSelectedTicket(prev => {
          if (!prev) return tixRes.items[0];
          const matched = tixRes.items.find(t => t.id === prev.id);
          return matched || tixRes.items[0];
        });
      } else {
        setSelectedTicket(null);
      }
    } catch (err) {
      console.error('Failed to load organization data:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSelectOrg = async (org: Organization) => {
    setCurrentOrg(org);
    api.setCurrentOrgId(org.id);
    await loadOrgData(org.id);
  };

  const handleRefresh = async () => {
    if (currentOrg) {
      await loadOrgData(currentOrg.id);
    }
  };

  // Ticket Operations
  const handleSendMessage = async (body: string, isInternal: boolean) => {
    if (!selectedTicket) return;
    await api.addMessage(selectedTicket.id, {
      body,
      sender_type: isInternal ? 'internal' : 'agent',
    });
    // Refresh ticket details
    const updated = await api.getTicket(selectedTicket.id);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
  };

  const handleApproveDraft = async (draftId: string) => {
    if (!selectedTicket) return;
    await api.approveDraft(draftId);
    const updated = await api.getTicket(selectedTicket.id);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
    handleRefresh();
  };

  const handleRejectDraft = async (draftId: string, reason: string) => {
    if (!selectedTicket) return;
    await api.rejectDraft(draftId, reason);
    const updated = await api.getTicket(selectedTicket.id);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
    handleRefresh();
  };

  const handleSendDraft = async (draftId: string) => {
    if (!selectedTicket) return;
    await api.sendApprovedDraft(draftId);
    const updated = await api.getTicket(selectedTicket.id);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
    handleRefresh();
  };

  const handleEditDraft = async (draftId: string, body: string) => {
    if (!selectedTicket) return;
    await api.editDraft(draftId, body);
    const updated = await api.getTicket(selectedTicket.id);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
  };

  const handleRegenerateDraft = async () => {
    if (!selectedTicket) return;
    await api.generateDraft(selectedTicket.id);
    const updated = await api.getTicket(selectedTicket.id);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
  };

  const handleEscalateTicket = async (reason: string) => {
    if (!selectedTicket) return;
    const updated = await api.escalateTicket(selectedTicket.id, reason);
    setSelectedTicket(updated);
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
    handleRefresh();
  };

  const handleTicketCreated = (newTicket: Ticket) => {
    setTickets(prev => [newTicket, ...prev]);
    setSelectedTicket(newTicket);
    setCurrentTab('inbox');
    handleRefresh();
  };

  const pendingReviewsCount = tickets.filter(t => t.status === 'awaiting_review').length;
  const openTicketsCount = tickets.filter(t => t.status !== 'resolved').length;

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Navbar
        organizations={organizations}
        currentOrg={currentOrg}
        onSelectOrg={handleSelectOrg}
        currentUser={currentUser}
        onOpenNewTicket={() => setIsNewTicketOpen(true)}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          pendingReviewsCount={pendingReviewsCount}
          openTicketsCount={openTicketsCount}
        />

        {/* Dynamic Views */}
        <main className="flex-1 flex overflow-hidden">
          {currentTab === 'inbox' && (
            <>
              <TicketList
                tickets={tickets}
                selectedTicket={selectedTicket}
                onSelectTicket={setSelectedTicket}
                isLoading={isLoading}
              />
              {selectedTicket ? (
                <TicketDetail
                  ticket={selectedTicket}
                  onSendMessage={handleSendMessage}
                  onApproveDraft={handleApproveDraft}
                  onRejectDraft={handleRejectDraft}
                  onSendDraft={handleSendDraft}
                  onEditDraft={handleEditDraft}
                  onRegenerateDraft={handleRegenerateDraft}
                  onEscalateTicket={handleEscalateTicket}
                />
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-slate-500">
                  Select a ticket to inspect conversation and AI draft suggestions.
                </div>
              )}
            </>
          )}

          {currentTab === 'approvals' && (
            <>
              <TicketList
                tickets={tickets.filter(t => t.status === 'awaiting_review' || t.status === 'needs_triage')}
                selectedTicket={selectedTicket}
                onSelectTicket={setSelectedTicket}
                isLoading={isLoading}
              />
              {selectedTicket ? (
                <TicketDetail
                  ticket={selectedTicket}
                  onSendMessage={handleSendMessage}
                  onApproveDraft={handleApproveDraft}
                  onRejectDraft={handleRejectDraft}
                  onSendDraft={handleSendDraft}
                  onEditDraft={handleEditDraft}
                  onRegenerateDraft={handleRegenerateDraft}
                  onEscalateTicket={handleEscalateTicket}
                />
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-slate-500">
                  No tickets awaiting review. All AI drafts are up to date!
                </div>
              )}
            </>
          )}

          {currentTab === 'knowledge' && (
            <KnowledgeManager
              documents={documents}
              onRefresh={handleRefresh}
            />
          )}

          {currentTab === 'analytics' && (
            <AnalyticsDashboard
              analytics={analytics}
              isLoading={isLoading}
            />
          )}

          {currentTab === 'audit' && (
            <AuditView
              events={auditEvents}
              isLoading={isLoading}
            />
          )}
        </main>
      </div>

      <NewTicketModal
        isOpen={isNewTicketOpen}
        onClose={() => setIsNewTicketOpen(false)}
        onTicketCreated={handleTicketCreated}
      />
    </div>
  );
};
