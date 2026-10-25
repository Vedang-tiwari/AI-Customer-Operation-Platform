import React, { useState } from 'react';
import { Ticket } from '../../types';
import { ApprovalCard } from '../approvals/ApprovalCard';
import {
  Send,
  Lock,
  MessageSquare,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  User,
  ArrowRight,
  Bot
} from 'lucide-react';

interface TicketDetailProps {
  ticket: Ticket;
  onSendMessage: (body: string, isInternal: boolean) => Promise<void>;
  onApproveDraft: (draftId: string) => Promise<void>;
  onRejectDraft: (draftId: string, reason: string) => Promise<void>;
  onSendDraft: (draftId: string) => Promise<void>;
  onEditDraft: (draftId: string, body: string) => Promise<void>;
  onRegenerateDraft: () => Promise<void>;
  onEscalateTicket: (reason: string) => Promise<void>;
}

export const TicketDetail: React.FC<TicketDetailProps> = ({
  ticket,
  onSendMessage,
  onApproveDraft,
  onRejectDraft,
  onSendDraft,
  onEditDraft,
  onRegenerateDraft,
  onEscalateTicket
}) => {
  const [replyText, setReplyText] = useState('');
  const [isInternalNote, setIsInternalNote] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [escalateReason, setEscalateReason] = useState('');

  const latestDraft = ticket.drafts && ticket.drafts.length > 0 ? ticket.drafts[0] : null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    setIsSending(true);
    try {
      await onSendMessage(replyText, isInternalNote);
      setReplyText('');
    } finally {
      setIsSending(false);
    }
  };

  const handleEscalate = async () => {
    if (!escalateReason.trim()) return;
    await onEscalateTicket(escalateReason);
    setShowEscalateModal(false);
    setEscalateReason('');
  };

  const lifecycleStages = [
    'received',
    'processing',
    'awaiting_review',
    'approved',
    'sent',
    'resolved'
  ];
  const currentStageIndex = lifecycleStages.indexOf(ticket.status);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950">
      {/* Ticket Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
        <div className="text-left space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-500">#{ticket.id.slice(0, 8)}</span>
            <h2 className="text-sm font-bold text-slate-100">{ticket.subject}</h2>
            {ticket.assigned_team && (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-indigo-300 border border-indigo-500/20">
                Team: {ticket.assigned_team.name}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span>Source: <strong className="text-slate-300 uppercase">{ticket.source}</strong></span>
            {ticket.intent && (
              <span>Intent: <code className="text-indigo-400 font-mono">{ticket.intent}</code></span>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {ticket.status !== 'resolved' && (
            <button
              onClick={() => setShowEscalateModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Escalate</span>
            </button>
          )}
        </div>
      </div>

      {/* Lifecycle Progress Bar */}
      <div className="px-6 py-2.5 bg-slate-900/30 border-b border-slate-800/80 flex items-center justify-between text-[11px]">
        {lifecycleStages.map((stage, idx) => {
          const isPassed = currentStageIndex >= idx;
          const isCurrent = ticket.status === stage;
          return (
            <React.Fragment key={stage}>
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${
                  isCurrent
                    ? 'bg-indigo-400 ring-4 ring-indigo-500/20 animate-pulse'
                    : isPassed
                    ? 'bg-emerald-400'
                    : 'bg-slate-700'
                }`} />
                <span className={`capitalize font-medium ${
                  isCurrent ? 'text-indigo-300 font-bold' : isPassed ? 'text-slate-300' : 'text-slate-600'
                }`}>
                  {stage.replace('_', ' ')}
                </span>
              </div>
              {idx < lifecycleStages.length - 1 && (
                <div className={`flex-1 h-[1px] mx-3 ${
                  isPassed ? 'bg-emerald-500/40' : 'bg-slate-800'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* AI Suggestion Section if available */}
        {latestDraft && (
          <ApprovalCard
            draft={latestDraft}
            ticket={ticket}
            onApprove={onApproveDraft}
            onReject={onRejectDraft}
            onSend={onSendDraft}
            onEdit={onEditDraft}
            onRegenerate={onRegenerateDraft}
          />
        )}

        {/* Conversation Thread */}
        <div className="space-y-4">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider text-left border-b border-slate-800/60 pb-2">
            Conversation Thread & Timeline
          </div>

          {ticket.messages && ticket.messages.map((msg) => {
            const isCustomer = msg.sender_type === 'customer';
            const isInternal = msg.sender_type === 'internal';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 text-left ${
                  isCustomer ? 'justify-start' : 'justify-end'
                }`}
              >
                {isCustomer && (
                  <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300 shrink-0">
                    <User className="w-4 h-4 text-slate-400" />
                  </div>
                )}

                <div className={`max-w-xl rounded-2xl p-4 space-y-1.5 shadow-md ${
                  isInternal
                    ? 'bg-amber-950/30 border border-amber-500/30 text-amber-200'
                    : isCustomer
                    ? 'bg-slate-900 border border-slate-800 text-slate-200'
                    : 'bg-indigo-950/40 border border-indigo-500/30 text-slate-100'
                }`}>
                  <div className="flex items-center justify-between text-[11px] gap-4">
                    <span className="font-semibold text-slate-300">
                      {msg.sender_name || (isCustomer ? 'Customer' : 'Support Agent')}
                      {isInternal && (
                        <span className="ml-2 px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-mono text-[10px]">
                          Internal Note
                        </span>
                      )}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="text-xs whitespace-pre-wrap leading-relaxed font-sans">
                    {msg.body}
                  </div>
                </div>

                {!isCustomer && (
                  <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-xs font-bold text-indigo-300 shrink-0">
                    <Bot className="w-4 h-4 text-indigo-400" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Message Composer Footer */}
      <form onSubmit={handleSend} className="p-3.5 border-t border-slate-800 bg-slate-900/90 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsInternalNote(false)}
              className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg font-medium transition ${
                !isInternalNote
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Customer Reply</span>
            </button>
            <button
              type="button"
              onClick={() => setIsInternalNote(true)}
              className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg font-medium transition ${
                isInternalNote
                  ? 'bg-amber-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Internal Team Note</span>
            </button>
          </div>
          <span className="text-[11px] text-slate-500">
            {isInternalNote ? 'Hidden from customer' : 'Sent directly to customer'}
          </span>
        </div>

        <div className="flex gap-2">
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder={isInternalNote ? "Write an internal note for team members..." : "Draft an agent message to customer..."}
            rows={2}
            className="flex-1 p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 resize-none font-sans"
          />
          <button
            type="submit"
            disabled={!replyText.trim() || isSending}
            className={`px-4 py-2 rounded-xl flex items-center justify-center text-xs font-semibold transition ${
              isInternalNote
                ? 'bg-amber-600 hover:bg-amber-500 text-white'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Escalate Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl text-left">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Escalate Ticket to Urgent Priority</span>
            </h3>
            <p className="text-xs text-slate-400">
              Escalating flags this ticket for immediate priority review by tier-2 engineering and security operations.
            </p>
            <textarea
              value={escalateReason}
              onChange={(e) => setEscalateReason(e.target.value)}
              placeholder="Reason for escalation (e.g. Critical security exposure, executive escalation)..."
              rows={3}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowEscalateModal(false)}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleEscalate}
                disabled={!escalateReason.trim()}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold"
              >
                Confirm Escalation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
