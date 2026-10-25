import React from 'react';
import { Organization, User } from '../types';
import { Building2, ShieldCheck, UserCheck, Plus, Sparkles, RefreshCw } from 'lucide-react';

interface NavbarProps {
  organizations: Organization[];
  currentOrg: Organization | null;
  onSelectOrg: (org: Organization) => void;
  currentUser: User | null;
  onOpenNewTicket: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  organizations,
  currentOrg,
  onSelectOrg,
  currentUser,
  onOpenNewTicket,
  onRefresh,
  isRefreshing
}) => {
  const currentRole = currentUser?.memberships?.find(
    m => m.organization_id === currentOrg?.id
  )?.role || 'agent';

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white font-bold">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent leading-none">
              Customer Ops AI
            </h1>
            <span className="text-[11px] text-indigo-400 font-medium">Operations & Grounded RAG</span>
          </div>
        </div>

        {/* Tenant Organization Switcher */}
        <div className="h-5 w-[1px] bg-slate-800 mx-2 hidden sm:block" />
        <div className="relative flex items-center gap-2 bg-slate-950/70 border border-slate-800 rounded-lg px-3 py-1.5 shadow-inner">
          <Building2 className="w-4 h-4 text-slate-400" />
          <select
            value={currentOrg?.id || ''}
            onChange={(e) => {
              const selected = organizations.find(o => o.id === e.target.value);
              if (selected) onSelectOrg(selected);
            }}
            className="bg-transparent text-sm font-medium text-slate-200 focus:outline-none cursor-pointer pr-2"
          >
            {organizations.map(org => (
              <option key={org.id} value={org.id} className="bg-slate-900 text-slate-200">
                {org.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          title="Refresh Data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
        </button>

        {/* New Ticket Button */}
        <button
          onClick={onOpenNewTicket}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition transform active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>New Ticket</span>
        </button>

        {/* Current User & Role Pill */}
        {currentUser && (
          <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800">
            <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-slate-300">
              {currentUser.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden md:block text-left leading-tight">
              <div className="text-xs font-medium text-slate-200">{currentUser.full_name}</div>
              <div className="flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">{currentRole}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
