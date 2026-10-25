import React from 'react';
import { Inbox, CheckCircle2, BookOpen, BarChart3, ShieldAlert } from 'lucide-react';

export type NavTab = 'inbox' | 'approvals' | 'knowledge' | 'analytics' | 'audit';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  pendingReviewsCount: number;
  openTicketsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  pendingReviewsCount,
  openTicketsCount
}) => {
  const navItems = [
    {
      id: 'inbox' as NavTab,
      label: 'Ticket Inbox',
      icon: Inbox,
      badge: openTicketsCount > 0 ? openTicketsCount : undefined,
      badgeColor: 'bg-indigo-500/20 text-indigo-400'
    },
    {
      id: 'approvals' as NavTab,
      label: 'Approval Queue',
      icon: CheckCircle2,
      badge: pendingReviewsCount > 0 ? pendingReviewsCount : undefined,
      badgeColor: 'bg-amber-500/20 text-amber-400'
    },
    {
      id: 'knowledge' as NavTab,
      label: 'Knowledge & RAG',
      icon: BookOpen
    },
    {
      id: 'analytics' as NavTab,
      label: 'Operations Analytics',
      icon: BarChart3
    },
    {
      id: 'audit' as NavTab,
      label: 'Audit Trail',
      icon: ShieldAlert
    }
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col justify-between p-4 shrink-0">
      <div className="space-y-1.5">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Operations Hub
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* System Status Footnote */}
      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-slate-300 font-medium">AI Engine Online</span>
        </div>
        <p className="text-[11px] text-slate-500">
          Deterministic business rules & pgvector RAG active.
        </p>
      </div>
    </aside>
  );
};
