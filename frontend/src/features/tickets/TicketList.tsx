import React, { useState } from 'react';
import { Ticket } from '../../types';
import { Search, Filter, AlertTriangle, Clock, CheckCircle2, User, Flame } from 'lucide-react';

interface TicketListProps {
  tickets: Ticket[];
  selectedTicket: Ticket | null;
  onSelectTicket: (ticket: Ticket) => void;
  isLoading: boolean;
}

export const TicketList: React.FC<TicketListProps> = ({
  tickets,
  selectedTicket,
  onSelectTicket,
  isLoading
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredTickets = tickets.filter(t => {
    if (filterStatus === 'awaiting_review' && t.status !== 'awaiting_review') return false;
    if (filterStatus === 'needs_triage' && t.status !== 'needs_triage') return false;
    if (filterStatus === 'urgent' && t.priority !== 'urgent') return false;
    if (filterStatus === 'resolved' && t.status !== 'resolved') return false;

    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        t.subject.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        (t.category && t.category.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return (
          <span className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
            <Flame className="w-3 h-3" /> Urgent
          </span>
        );
      case 'high':
        return (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
            High
          </span>
        );
      case 'normal':
        return (
          <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-700/60 text-slate-300">
            Normal
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
            Low
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'awaiting_review':
        return (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            Awaiting Review
          </span>
        );
      case 'needs_triage':
        return (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-400 border border-orange-500/30">
            Needs Triage
          </span>
        );
      case 'approved':
        return (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            Approved
          </span>
        );
      case 'sent':
      case 'resolved':
        return (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
            {status}
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">
            {status}
          </span>
        );
    }
  };

  const getSentimentEmoji = (sentiment?: string) => {
    switch (sentiment) {
      case 'frustrated':
        return '🤬 Frustrated';
      case 'negative':
        return '😟 Negative';
      case 'positive':
        return '😊 Positive';
      default:
        return '😐 Neutral';
    }
  };

  return (
    <div className="w-80 md:w-96 border-r border-slate-800 bg-slate-950/40 flex flex-col shrink-0 h-full">
      {/* Search and Filters */}
      <div className="p-3.5 border-b border-slate-800 space-y-2.5">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search tickets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        {/* Quick Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px]">
          {['all', 'awaiting_review', 'needs_triage', 'urgent', 'resolved'].map((f) => (
            <button
              key={f}
              onClick={() => setFilterStatus(f)}
              className={`px-2.5 py-1 rounded-lg capitalize whitespace-nowrap font-medium transition ${
                filterStatus === f
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Ticket List Items */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-2 space-y-1">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading tickets...</div>
        ) : filteredTickets.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">No tickets found.</div>
        ) : (
          filteredTickets.map((t) => {
            const isSelected = selectedTicket?.id === t.id;
            return (
              <div
                key={t.id}
                onClick={() => onSelectTicket(t)}
                className={`p-3 rounded-xl cursor-pointer transition text-left border ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500/50 shadow-md shadow-indigo-950/30'
                    : 'bg-slate-900/40 border-transparent hover:bg-slate-900/80 hover:border-slate-800'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="text-xs font-semibold text-slate-200 line-clamp-1">
                    {t.subject}
                  </h3>
                  {getPriorityBadge(t.priority)}
                </div>

                <p className="text-[11px] text-slate-400 line-clamp-2 mb-2 leading-relaxed">
                  {t.description}
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-500">
                  <div className="flex items-center gap-1.5">
                    {getStatusBadge(t.status)}
                    {t.category && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 capitalize">
                        {t.category}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {getSentimentEmoji(t.sentiment)}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
